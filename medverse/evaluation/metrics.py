from __future__ import annotations

def safe_rate(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator

def routing_accuracy(route_results):
    return safe_rate(
        sum(bool(x["correct"]) for x in route_results),
        len(route_results),
    )

def mandate_compliance_rate(action_results):
    return safe_rate(
        sum(bool(x["compliant"]) for x in action_results),
        len(action_results),
    )

def coordination_success_rate(coordination_results):
    return safe_rate(
        sum(bool(x["correct"]) for x in coordination_results),
        len(coordination_results),
    )

def conflict_detection_rate(conflict_results):
    return safe_rate(
        sum(bool(x["correct"]) for x in conflict_results),
        len(conflict_results),
    )

def escalation_accuracy_rate(escalation_results):
    return safe_rate(
        sum(bool(x["correct"]) for x in escalation_results),
        len(escalation_results),
    )

def policy_grounding_accuracy(policy_results):
    return safe_rate(
        sum(bool(x["correct"]) for x in policy_results),
        len(policy_results),
    )

def information_leakage_rate(leakage_results):
    return safe_rate(
        sum(bool(x["leak"]) for x in leakage_results),
        len(leakage_results),
    )
