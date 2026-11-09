from __future__ import annotations
from pathlib import Path
from typing import Any

REQUIRED_EVENT_KEYS = {"event_id","t","event_type","visible_to","payload"}

def result(check: str, passed: bool, observed: Any, expected: Any, severity="FAIL") -> dict:
    return {
        "check": check,
        "status": "PASS" if passed else severity,
        "observed": observed,
        "expected": expected,
    }

def validate_scenario(s: dict) -> list[dict]:
    out = []
    events = s.get("events", [])
    out.append(result("scenario_has_events", len(events) > 0, len(events), "> 0"))
    ids = [e.get("event_id") for e in events]
    out.append(result("event_ids_unique", len(ids)==len(set(ids)), ids, "all unique"))
    times = [e.get("t") for e in events]
    out.append(result("event_times_strictly_increasing",
                      all(isinstance(t,(int,float)) for t in times) and all(a < b for a,b in zip(times,times[1:])),
                      times, "strictly increasing"))
    missing = []
    for i,e in enumerate(events):
        miss = sorted(REQUIRED_EVENT_KEYS - set(e))
        if miss: missing.append({"index":i,"missing":miss})
    out.append(result("event_schema_complete", not missing, missing, "no missing required keys"))
    invisible = [e.get("event_id") for e in events if not e.get("visible_to")]
    out.append(result("every_event_has_visibility_target", not invisible, invisible, "none"))

    for e in events:
        p = e.get("payload", {})
        if e.get("event_type") == "CLINICAL_ALARM":
            spo2 = p.get("SpO2")
            hr = p.get("heart_rate")
            out.append(result(f"{e['event_id']}_SpO2_range", isinstance(spo2,(int,float)) and 0 <= spo2 <= 100, spo2, "[0,100]"))
            out.append(result(f"{e['event_id']}_heart_rate_positive", isinstance(hr,(int,float)) and hr > 0, hr, ">0"))
        elif e.get("event_type") == "NETWORK_DEGRADATION":
            pl = p.get("packet_loss")
            rtt = p.get("rtt_ms")
            jit = p.get("jitter_ms")
            out.append(result(f"{e['event_id']}_packet_loss_range", isinstance(pl,(int,float)) and 0 <= pl <= 1, pl, "[0,1]"))
            out.append(result(f"{e['event_id']}_rtt_nonnegative", isinstance(rtt,(int,float)) and rtt >= 0, rtt, ">=0"))
            out.append(result(f"{e['event_id']}_jitter_nonnegative", isinstance(jit,(int,float)) and jit >= 0, jit, ">=0"))
        elif e.get("event_type") == "DEVICE_AUTH_ANOMALY":
            cert = p.get("certificate_status")
            out.append(result(f"{e['event_id']}_certificate_status_known",
                              cert in {"valid","mismatch","expired","revoked","unknown"},
                              cert, "known enum"))
    return out

def validate_policy_manifest(m: dict) -> list[dict]:
    out = []
    docs = m.get("documents", [])
    out.append(result("policy_documents_present", len(docs) >= 2, len(docs), ">=2"))
    ids = [d.get("document_id") for d in docs]
    out.append(result("policy_document_ids_unique", len(ids)==len(set(ids)), ids, "all unique"))
    required = {"document_id","title","authority","jurisdiction","official_url","agent_access","topics","status"}
    bad=[]
    for d in docs:
        miss=sorted(required-set(d))
        if miss: bad.append({"document_id":d.get("document_id"),"missing":miss})
    out.append(result("policy_manifest_schema_complete", not bad, bad, "none"))
    non_https=[d.get("document_id") for d in docs if not str(d.get("official_url","")).startswith("https://")]
    out.append(result("policy_urls_https", not non_https, non_https, "none"))
    access=set(a for d in docs for a in d.get("agent_access",[]))
    out.append(result("initial_agents_have_policy_source",
                      {"hospital_agent","cyber_network_agent"}.issubset(access),
                      sorted(access), "hospital_agent and cyber_network_agent"))
    return out

def _to_int(v):
    try:
        return int(float(str(v).replace(",","").strip()))
    except Exception:
        return None

def _to_float(v):
    if v is None or str(v).strip()=="":
        return None
    try:
        return float(str(v).replace(",","").strip())
    except Exception:
        return None

def validate_ncc_csv(headers: list[str], rows: list[dict], required_cols: list[str]) -> list[dict]:
    out=[]
    missing=[c for c in required_cols if c not in headers]
    out.append(result("ncc_required_columns", not missing, missing, "none missing"))
    out.append(result("ncc_row_count", len(rows)==37050, len(rows), 37050, severity="FAIL"))
    if missing:
        return out

    years=[_to_int(r["발생연도"]) for r in rows]
    years_ok=[y for y in years if y is not None]
    yr_range=(min(years_ok), max(years_ok)) if years_ok else None
    out.append(result("ncc_year_coverage", yr_range==(1999,2023), yr_range, (1999,2023)))

    counts=[_to_int(r["발생자수"]) for r in rows]
    bad_counts=sum(c is None or c<0 for c in counts)
    out.append(result("ncc_incidence_counts_nonnegative_numeric", bad_counts==0, bad_counts, 0))

    rates=[_to_float(r["조발생률"]) for r in rows]
    bad_rates=0
    missing_rate_with_positive_count=0
    for c,rate in zip(counts,rates):
        if rate is not None and rate < 0:
            bad_rates += 1
        if rate is None and c is not None and c > 0:
            missing_rate_with_positive_count += 1
    out.append(result("ncc_rates_nonnegative_when_present", bad_rates==0, bad_rates, 0))
    out.append(result("ncc_missing_rate_only_when_count_zero",
                      missing_rate_with_positive_count==0,
                      missing_rate_with_positive_count, 0))

    empty_key=0
    for r in rows:
        for c in ["발생연도","성별","국제질병분류","암종","연령군"]:
            if str(r.get(c,"")).strip()=="":
                empty_key += 1
    out.append(result("ncc_key_categories_nonempty", empty_key==0, empty_key, 0))

    tuples=[tuple(r.get(c,"") for c in headers) for r in rows]
    dup=len(tuples)-len(set(tuples))
    out.append(result("ncc_exact_duplicate_rows", dup==0, dup, 0))
    return out
