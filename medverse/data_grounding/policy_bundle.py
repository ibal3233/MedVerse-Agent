from __future__ import annotations

from typing import Dict, List

def index_policy_records_by_agent(seed: Dict) -> Dict[str, List[Dict]]:
    """
    Partition policy seed records using canonical `agent_access`.
    """
    out: Dict[str, List[Dict]] = {}
    for record in seed.get("records", []):
        for agent_id in record.get("agent_access", []):
            out.setdefault(agent_id, []).append(record)
    return out
