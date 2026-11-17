"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def _finite_number(value: object) -> bool:
    return isinstance(value, int) or (isinstance(value, float) and isfinite(value))


def _report_integrity(
    report: dict, name: str, metric_ids: set[str], graded: set[str], require_cost: bool,
) -> tuple[dict[tuple[str, int], frozenset[str]], list[str]]:
    problems = []
    manifest, rows, metrics = report["manifest"], report["rows"], report["metrics"]
    seeds = set(manifest["seeds"])
    if not seeds or len(seeds) != len(manifest["seeds"]):
        problems.append(f"{name} manifest has empty or repeated seeds")
    if len(rows) != manifest["items"] * len(manifest["seeds"]):
        problems.append(f"{name} row count differs from manifest items × seeds")
    if report.get("evaluator_failures"):
        problems.append(f"{name} contains evaluator_failures")

    for metric_id in sorted(metric_ids - metrics.keys()):
        problems.append(f"{name} is missing metric {metric_id}")
    for metric_id, value in metrics.items():
        no_success_cost = (
            metric_id == "cost_per_success" and value is None
            and all(row.get("pass_rate") is False for row in rows)
        )
        if not no_success_cost and not _finite_number(value):
            problems.append(f"{name} metric {metric_id} is missing or non-finite")

    slices_by_trial = {}
    slices_by_item = {}
    invalid_scores = set()
    for row in rows:
        item, seed = row["item_id"], row["seed"]
        trial = (item, seed)
        if trial in slices_by_trial:
            problems.append(f"{name} duplicate trial {item}@{seed}")
        tags = frozenset(row.get("slices") or ())
        if slices_by_item.setdefault(item, tags) != tags:
            problems.append(f"{name} has inconsistent slice tags for {item}")
        slices_by_trial[trial] = tags
        invalid_scores.update(metric_id for metric_id in graded if row.get(metric_id) not in (False, True))

    expected_trials = {(item, seed) for item in slices_by_item for seed in seeds}
    if len(slices_by_item) != manifest["items"] or slices_by_trial.keys() != expected_trials:
        problems.append(f"{name} trials do not cover each manifest item × seed exactly once")
    for metric_id in sorted(invalid_scores):
        problems.append(f"{name} has missing or invalid trial scores for {metric_id}")
    if require_cost and any(not _finite_number(row.get("cost")) or row["cost"] < 0 for row in rows):
        problems.append(f"{name} has missing or invalid trial costs")
    return slices_by_trial, problems


def _ratchet_problems(spec: dict, base_spec: dict) -> list[str]:
    problems = []
    candidate = {m["id"]: (m, m.get("threshold", {})) for m in spec["metrics"]}
    previous = {m["id"]: (m, m.get("threshold", {})) for m in base_spec["metrics"]}
    for index, rules in ((candidate, spec), (previous, base_spec)):
        for rule in rules.get("slices", []):
            index[f'slice:{rule["name"]}/{rule["metric"]}'] = (rule, rule)

    for rule_id, (old_rule, old_limits) in previous.items():
        if rule_id not in candidate:
            problems.append(f"ratchet removed {rule_id}")
            continue
        rule, limits = candidate[rule_id]
        if old_rule.get("blocking") and not rule.get("blocking"):
            problems.append(f"ratchet made {rule_id} non-blocking")
        if old_limits.get("no_significant_drop") and not limits.get("no_significant_drop"):
            problems.append(f"ratchet removed no_significant_drop from {rule_id}")
        for key in ("min", "max", "max_increase"):
            if key not in old_limits:
                continue
            old_value, value = old_limits[key], limits.get(key)
            if not _finite_number(value):
                problems.append(f"ratchet removed or invalidated {rule_id} {key}")
            elif (key == "min" and value < old_value) or (key != "min" and value > old_value):
                problems.append(f"ratchet loosened {rule_id} {key} from {old_value} to {value}")
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    metric_ids = {m["id"] for m in spec["metrics"]}
    baseline_columns = {key for row in base["rows"] for key in row}
    graded = metric_ids & (GRADERS.keys() | baseline_columns)
    graded.update(rule["metric"] for rule in spec.get("slices", []))
    require_cost = "cost" in baseline_columns or "cost_per_success" in metric_ids
    pr_trials, problems = _report_integrity(pr, "PR", metric_ids, graded, require_cost)
    base_trials, base_problems = _report_integrity(base, "baseline", metric_ids, graded, require_cost)
    problems.extend(base_problems)
    if pr_trials.keys() != base_trials.keys():
        problems.append("PR and baseline have different (item, seed) sets")
    elif pr_trials != base_trials:
        problems.append("PR and baseline have different slice tags")

    if base_spec is not None and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        problems.extend(_ratchet_problems(spec, base_spec))

    # Verify gate inputs against the trial data emitted by the eval harness.
    if not problems and require_cost:
        for name, report in (("PR", pr), ("baseline", base)):
            recalculated = aggregate(report["rows"], sorted(graded), k_values=spec.get("pass_k", []))
            for metric_id in sorted(metric_ids & recalculated.keys()):
                if report["metrics"][metric_id] != recalculated[metric_id]:
                    problems.append(f"{name} metric {metric_id} does not match its trial scores")
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bootstrap = spec.get("bootstrap", {})
    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        gate_id = f"slice:{name}/{metric}"
        candidate = per_item(pr, metric, slice_name=name)
        floor = rule.get("min")
        value = sum(candidate.values()) / len(candidate) if candidate else None
        failed = value is None or (floor is not None and value < floor)
        note = f"n={len(candidate)}"

        if rule.get("no_significant_drop") and candidate:
            baseline = per_item(base, metric, slice_name=name)
            if candidate.keys() != baseline.keys():
                failed = True
                note += "; unmatched baseline items"
            else:
                keys = sorted(candidate)
                delta, low, high = stats.paired_bootstrap(
                    [candidate[key] for key in keys],
                    [baseline[key] for key in keys],
                    n_resamples=bootstrap.get("n_resamples", 1000),
                    rng=bootstrap.get("rng", 2027),
                    confidence=bootstrap.get("confidence", 0.95),
                )
                failed |= high < 0
                note += f" Δ {delta:+.3f} CI [{low:+.3f}, {high:+.3f}]"

        blocking = rule.get("blocking", False)
        if failed and blocking:
            blocked.append(gate_id)
        verdict = ("BLOCK" if blocking else "warn") if failed else "ok"
        value_text = f"{value:.4f}" if value is not None else "MISSING"
        floor_text = f" min={floor}" if floor is not None else ""
        lines.append(f"  {gate_id} {value_text}{floor_text} · {note} · {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                               confidence=bs.get("confidence", 0.95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
