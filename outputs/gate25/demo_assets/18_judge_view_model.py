from __future__ import annotations

from typing import Dict, Any, List

AGENT_LABELS = {
    "hospital_agent": "Healthcare Provider / Hospital",
    "cyber_network_agent": "Cyber / Network",
    "privacy_agent": "Privacy",
    "research_irb_agent": "Research / IRB",
    "regulator_agent": "Health / AI Regulator",
}

AGENT_ROLES = {
    "hospital_agent": "Clinical care, patient safety, and trusted measurement",
    "cyber_network_agent": "Telemetry trust, identity, integrity, and infrastructure",
    "privacy_agent": "Purpose limitation, disclosure, consent scope, and minimization",
    "research_irb_agent": "Research authorization, IRB oversight, and participant rights",
    "regulator_agent": "High-impact AI safety, validation, and human oversight",
}

STATE_LABELS = {
    "AGREEMENT": "Institutional Agreement",
    "COMPLEMENTARY": "Complementary Risk",
    "CONDITIONAL_HARMONIZATION": "Conditional Harmonization",
    "INSTITUTIONAL_CONFLICT": "Institutional Conflict",
    "POLICY_CONFLICT": "Policy Conflict",
    "INSUFFICIENT_EVIDENCE": "Insufficient Evidence",
    "HUMAN_AUTHORITY_REQUIRED": "Human Authority Required",
}

BOUNDARY_LABELS = {
    "COMPLIANT": "Policy-compliant",
    "OUT_OF_POLICY": "Outside policy",
    "WRONG_JURISDICTION": "Wrong jurisdiction",
    "OUTSIDE_MANDATE": "Outside institutional mandate",
    "INSUFFICIENT_EVIDENCE": "Insufficient evidence",
    "HUMAN_AUTHORITY_REQUIRED": "Human authority required",
}

OUTCOME_LABELS = {
    "COMPLEMENTARY_RISK": "Clinical risk + telemetry trust risk handled jointly",
    "CARE_CONTINUES_RESEARCH_RESTRICTED": "Care continues; research use restricted",
    "EVIDENCE_INSUFFICIENT_HIGH_IMPACT_AI_BLOCKED": "High-impact automated action withheld pending trusted evidence and human oversight",
    "DISCLOSURE_BLOCKED": "Unauthorized disclosure blocked",
}

DT_LABELS = {
    "VALID": "Valid",
    "DEGRADED": "Degraded",
    "UNVERIFIED": "Unverified",
}


def humanize_code(value: str) -> str:
    if value is None:
        return ""
    return str(value).replace("_", " ").title()


def _policy_card(hit: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "chunk_id": hit.get("chunk_id", ""),
        "authority": hit.get("authority", ""),
        "source_type": humanize_code(hit.get("source_type", "")),
        "official_url": hit.get("official_url", ""),
        "locator": hit.get("locator", ""),
        "score": hit.get("score"),
    }


def build_judge_view(trace: Dict[str, Any], scenario_name: str = "") -> Dict[str, Any]:
    """
    Pure presentation adapter.

    It transforms a frozen Gate-19 judge trace into UI-ready labels.
    It must not infer, change, filter away, or replace scientific decisions.
    """
    agents = []
    for agent_id, info in trace["agents"].items():
        agents.append({
            "agent_id": agent_id,
            "name": AGENT_LABELS.get(agent_id, humanize_code(agent_id)),
            "role": AGENT_ROLES.get(agent_id, ""),
            "assessment_code": info.get("assessment_code", ""),
            "assessment_label": humanize_code(info.get("assessment_code", "")),
            "risk": info.get("risk", ""),
            "recommended_actions": list(info.get("recommended_actions", [])),
            "selected_boundary_action": info.get("selected_boundary_action", ""),
            "selected_boundary_action_label": humanize_code(
                info.get("selected_boundary_action", "")
            ),
            "policy_boundary_status": info.get("policy_boundary_status", ""),
            "policy_boundary_label": BOUNDARY_LABELS.get(
                info.get("policy_boundary_status", ""),
                humanize_code(info.get("policy_boundary_status", "")),
            ),
            "enforcement": info.get("enforcement", ""),
            "policy_ids": list(info.get("policy_ids", [])),
            "retrieved_policy": [
                _policy_card(h) for h in info.get("retrieved_policy", [])
            ],
            "dt_evidence_used": list(info.get("dt_evidence_used", [])),
            "open_data_evidence_used": list(
                info.get("open_data_evidence_used", [])
            ),
            "patient_level_inference_from_population_data":
                info.get("patient_level_inference_from_population_data", False),
            "unauthorized_evidence_used":
                info.get("unauthorized_evidence_used", False),
        })

    return {
        "scenario_id": trace["scenario_id"],
        "scenario_name": scenario_name,
        "jurisdiction": trace["deployment_jurisdiction"],
        "digital_twin": {
            "validity": trace["dt_validity"],
            "validity_label": DT_LABELS.get(
                trace["dt_validity"], trace["dt_validity"]
            ),
        },
        "agents": agents,
        "coordination": {
            "state": trace["coordination_state"],
            "state_label": STATE_LABELS.get(
                trace["coordination_state"],
                humanize_code(trace["coordination_state"]),
            ),
            "accepted_actions": trace.get("accepted_actions", []),
            "blocked_actions": trace.get("blocked_actions", []),
            "conditional_steps": trace.get("conditional_steps", []),
            "evidence_requests": trace.get("evidence_requests", []),
            "messages": trace.get("minimum_necessary_messages", []),
            "escalation_required": trace.get("escalation_required", False),
            "escalation_targets": trace.get("escalation_targets", []),
            "rationale_code": trace.get("rationale_code", ""),
            "rationale_label": humanize_code(trace.get("rationale_code", "")),
        },
        "outcome": {
            "code": trace["final_outcome"],
            "label": OUTCOME_LABELS.get(
                trace["final_outcome"],
                humanize_code(trace["final_outcome"]),
            ),
        },
    }
