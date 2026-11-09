from medverse.reasoning.bounded_adapter import (
    BoundedReasoningAdapter,
    validate_bounded_output,
)

def base_decision():
    return {
        "coordination_state": "COMPLEMENTARY_RISK",
        "rationale_code": "HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST",
        "joint_actions": [
            "CONTACT_PATIENT",
            "VERIFY_MEASUREMENT",
        ],
        "human_review_required": True,
    }

def policy_hits():
    return [{
        "chunk_id": "P1",
        "document_id": "D1",
        "title": "Policy",
        "article": "A1",
        "official_url": "https://example.org",
        "effective_date": "2026-01-01",
        "authority": "Authority",
        "translation_status": "source-grounded English paraphrase",
    }]

def test_bounded_reference_output():
    adapter = BoundedReasoningAdapter()
    e = adapter.explain(base_decision(), policy_hits())
    assert validate_bounded_output(
        e, base_decision(), policy_hits()
    ) == []

def test_invented_action_rejected():
    adapter = BoundedReasoningAdapter()
    e = adapter.explain(base_decision(), policy_hits())
    e.allowed_joint_actions.append("UNAUTHORIZED_ACTION")
    assert "action_set_changed" in validate_bounded_output(
        e, base_decision(), policy_hits()
    )
