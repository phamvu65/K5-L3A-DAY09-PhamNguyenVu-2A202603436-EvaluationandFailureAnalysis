import pytest


@pytest.mark.student
@pytest.mark.parametrize(
    ("shape", "expected_pass"),
    [("seeded_regression", False), ("fixed", True)],
)
def test_db_fact_and_ledger_for_c002(shape, expected_pass):
    from pydantic_evals.evaluators import EvaluatorContext

    from lab9.graders import DbFactKept
    from lab9.trace_case import investigate

    case = investigate(shape, "C-002", 11)
    trial, label = case["trial"], case["label"]
    context = EvaluatorContext(
        name="C-002@11",
        inputs={"claim_id": "C-002", "seed": 11},
        metadata=None,
        expected_output=label,
        output=trial,
        duration=0.0,
        _span_tree=None,
        attributes={},
        metrics={},
    )

    assert DbFactKept().evaluate(context).value is expected_pass
    assert (trial["snapshot"]["refund_vnd"] == label["refund_vnd"]) is expected_pass
