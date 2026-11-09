from __future__ import annotations
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from medverse.learning.gate21_dataset_builder import write_dataset,AGENT_LABELS

OUT=ROOT/"outputs"/"gate21"; OUT.mkdir(parents=True,exist_ok=True)
DATA=ROOT/"data"/"learning"/"gate21"
BASE=DATA/"baseline_matrix.json"

def check(n,ok,o,e): return {"check":n,"status":"PASS" if ok else "FAIL","observed":o,"expected":e}

def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 21")
    print(" Institutional Learning Dataset")
    print(" & Baseline Freeze")
    print("========================================\n")

    reg=json.loads((ROOT/"FREEZE_REGISTRY.json").read_text(encoding="utf-8"))
    if reg.get("promoted_gates",{}).get("GATE_20",{}).get("status")!="PASS":
        r={"gate":"GATE_21_INSTITUTIONAL_LEARNING_DATASET","status":"HOLD","reason":"Gate 20 is not promoted PASS."}
        (OUT/"gate21_status.json").write_text(json.dumps(r,indent=2),encoding="utf-8")
        print(json.dumps(r,indent=2)); return

    rows,manifest=write_dataset(DATA)
    c=[]
    c.append(check("no_patient_data",all(r["patient_data"] is False for r in rows),sorted({r["patient_data"] for r in rows}),[False]))
    agents=sorted({r["agent_id"] for r in rows}); exp_agents=sorted(AGENT_LABELS)
    c.append(check("all_five_agents_present",agents==exp_agents,agents,exp_agents))
    c.append(check("agent_labels_explicit",all(AGENT_LABELS[a].endswith("Agent") for a in AGENT_LABELS),list(AGENT_LABELS.values()),"all end with Agent"))
    c.append(check("per_agent_dataset_files_exist",all((DATA/f"{a}.csv").exists() for a in exp_agents),[str(DATA/f"{a}.csv") for a in exp_agents],"all five files"))

    req=["target_assessment","target_action","target_boundary_status","target_enforcement"]
    missing=[(r["record_id"],f) for r in rows for f in req if r.get(f) in (None,"")]
    c.append(check("target_fields_complete",not missing,missing[:20],[]))

    states=sorted({r["target_boundary_status"] for r in rows})
    req_states={"COMPLIANT","INSUFFICIENT_EVIDENCE","WRONG_JURISDICTION","OUTSIDE_MANDATE"}
    c.append(check("boundary_state_diversity",req_states.issubset(states),states,sorted(req_states)))
    enf=sorted({r["target_enforcement"] for r in rows})
    c.append(check("enforcement_diversity",{"PERMIT","BLOCK","ESCALATE"}.issubset(enf),enf,["BLOCK","ESCALATE","PERMIT"]))

    fam_split={}; leakage=[]
    for r in rows:
        f,s=r["scenario_family"],r["split"]
        if f in fam_split and fam_split[f]!=s: leakage.append((f,fam_split[f],s))
        fam_split[f]=s
    c.append(check("no_scenario_family_split_leakage",not leakage,leakage,[]))

    split_counts={s:sum(r["split"]==s for r in rows) for s in ["train","dev","test"]}
    c.append(check("train_dev_test_nonempty",all(v>0 for v in split_counts.values()),split_counts,"all > 0"))

    ids=[r["record_id"] for r in rows]
    c.append(check("record_ids_unique",len(ids)==len(set(ids)),{"rows":len(ids),"unique":len(set(ids))},"equal"))

    sig={}; dup=[]
    for r in rows:
        k=(r["agent_id"],r["features_json"])
        if k in sig and sig[k]!=r["split"]: dup.append((k,sig[k],r["split"]))
        sig[k]=r["split"]
    c.append(check("no_exact_feature_duplicate_across_splits",not dup,dup[:20],[]))

    base=json.loads(BASE.read_text(encoding="utf-8"))
    got=sorted(base["baselines"]); exp=sorted(["B1_SINGLE_OMNISCIENT","B2_ROLE_PROMPTED_MAS","B3_CONSENSUS_MAS","B4_POLICY_FILTERED_MAS","B5_MEDVERSE_AGENT"])
    c.append(check("baseline_matrix_complete",got==exp,got,exp))
    c.append(check("synthetic_benchmark_provenance_explicit",all(r["synthetic_policy_benchmark"] is True for r in rows),True,True))

    rows2,manifest2=write_dataset(DATA)
    c.append(check("deterministic_dataset_regeneration",rows==rows2 and manifest==manifest2,rows==rows2 and manifest==manifest2,True))

    (OUT/"gate21_checks.json").write_text(json.dumps(c,indent=2,ensure_ascii=False),encoding="utf-8")
    passed=sum(x["status"]=="PASS" for x in c); total=len(c)
    result={
        "gate":"GATE_21_INSTITUTIONAL_LEARNING_DATASET",
        "status":"PASS" if passed==total else "FAIL",
        "passed_checks":passed,"total_checks":total,
        "dataset_id":"MEDVERSE-G21-INSTITUTIONAL-LEARNING-v1",
        "total_records":len(rows),
        "agent_counts":manifest["agent_counts"],
        "split_counts":split_counts,
        "boundary_states":states,
        "enforcement_states":enf,
        "patient_data":False,
        "training_performed":False,
        "baseline_freeze_id":base["freeze_id"],
    }
    (OUT/"gate21_status.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    print(f"\nDataset saved to:\n{DATA}")
    print(f"\nOutputs saved to:\n{OUT}")
    if result["status"]=="FAIL":
        raise SystemExit("Gate 21 FAILED. Diagnose dataset construction, split leakage, target coverage, or baseline-freeze integrity before training.")
    print("\nFULL GATE 21 PASS — Institutional learning data and B1-B5 baseline definitions are frozen. Gate 22 may begin actual agent training.")
if __name__=="__main__": main()
