"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    outcomes = {
        (POS, POS): "tp",
        ("PASS", POS): "fp",
        (POS, "PASS"): "fn",
        ("PASS", "PASS"): "tn",
    }
    counts = dict.fromkeys(outcomes.values(), 0)
    for pair in zip(human, judge, strict=True):
        outcome = outcomes.get(pair)
        if outcome is None:
            raise ValueError("Human and judge labels must be PASS or FAIL")
        counts[outcome] += 1
    return counts


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    counts = confusion(human, judge)
    true_positives = counts["tp"]
    predicted_failures = true_positives + counts["fp"]
    actual_failures = true_positives + counts["fn"]
    precision = true_positives / predicted_failures if predicted_failures else 0.0
    recall = true_positives / actual_failures if actual_failures else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """Return (observed - expected) / (1 - expected) agreement."""
    counts = confusion(human, judge)
    tp, fp, fn, tn = (counts[key] for key in ("tp", "fp", "fn", "tn"))
    total = tp + fp + fn + tn
    # Scale agreement by total squared to keep the undefined case exact.
    expected = (tp + fn) * (tp + fp) + (tn + fp) * (tn + fn)
    denominator = total * total - expected
    if denominator == 0:
        raise ValueError("Cohen's kappa is undefined for these labels")
    observed = (tp + tn) * total
    return (observed - expected) / denominator


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    denominator = sensitivity + specificity - 1.0
    if denominator == 0:
        raise ValueError("Rogan-Gladen correction is undefined when sensitivity + specificity = 1")
    corrected_rate = (observed_rate + specificity - 1.0) / denominator
    return min(1.0, max(0.0, corrected_rate))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap

    if len(a) != len(b) or len(a) == 0:
        raise ValueError("Paired bootstrap needs equally sized, non-empty samples")

    candidate = np.asarray(a, dtype=float)
    baseline = np.asarray(b, dtype=float)

    def mean_difference(candidate, baseline, axis):
        return np.mean(candidate - baseline, axis=axis)

    delta = float(mean_difference(candidate, baseline, axis=0))
    if np.array_equal(candidate, baseline):
        return 0.0, 0.0, 0.0
    if len(a) == 1:
        return delta, delta, delta

    interval = bootstrap(
        (candidate, baseline),
        mean_difference,
        paired=True,
        method="percentile",
        n_resamples=n_resamples,
        confidence_level=confidence,
        rng=np.random.default_rng(rng),
    ).confidence_interval
    return delta, float(interval.low), float(interval.high)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    raise NotImplementedError
