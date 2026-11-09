from __future__ import annotations
from pathlib import Path
import csv, json, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

from medverse.learning.institutional_classifier import clean_features, train_bundle, save_bundle
from medverse.learning.gate23_research_irb_benchmark import build_ood, build_augmentation, sig

DATA = ROOT / "data" / "learning" / "gate21a" / "research_irb_agent.csv"
OUT = ROOT / "outputs" / "gate23"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

def load_rows():
    with DATA.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def shield(action, f):
    consent = f.get("research_consent")
    irb = f.get("irb_status")
    pseudo = f.get("pseudonymized", True)

    if action == "ALLOW_AUTHORIZED_RESEARCH_PROCESSING":
        if consent == "active" and irb == "approved" and pseudo is True:
            return "COMPLIANT", "PERMIT"
        if consent is None or irb in {None, "unknown"}:
            return "INSUFFICIENT_EVIDENCE", "ESCALATE"
        return "OUT_OF_POLICY", "BLOCK"

    if action == "BLOCK_RESEARCH_PROCESSING":
        return "COMPLIANT", "PERMIT"

    if action == "REQUEST_IRB_REVIEW":
        return "COMPLIANT", "PERMIT"

    if action == "PRESERVE_RESEARCH_AUDIT_LOG":
        if consent == "active" and irb == "approved":
            return "COMPLIANT", "PERMIT"
        return "OUT_OF_POLICY", "BLOCK"

    return "OUTSIDE_MANDATE", "BLOCK"

def row_from_aug(a):
    return {
        "features_json": json.dumps(a["features"], sort_keys=True),
        "target_assessment": a["assessment"],
        "target_action": a["action"],
        "target_boundary_status": a["boundary"],
        "target_enforcement": a["enforcement"],
        "target_evidence_request": "" if a["evidence"] == "NONE" else a["evidence"],
    }

def eval_rows(bundle, rows):
    X=[clean_features(r["features_json"]) for r in rows]
    fields={
        "assessment":("assessment_model","target_assessment"),
        "action":("action_model","target_action"),
        "boundary":("boundary_model","target_boundary_status"),
        "enforcement":("enforcement_model","target_enforcement"),
        "evidence":("evidence_model","target_evidence_request"),
    }
    out={}
    for n,(attr,field) in fields.items():
        yt=[r[field] if r[field] else "NONE" for r in rows]
        yp=list(getattr(bundle,attr).predict(X))
        out[n]={"accuracy":accuracy_score(yt,yp),
                "macro_f1":f1_score(yt,yp,average="macro",zero_division=0),
                "true":yt,"pred":yp}
    return out

def eval_ood(bundle, cases):
    X=[clean_features(json.dumps(c["features"])) for c in cases]
    models={
        "assessment":bundle.assessment_model,
        "action":bundle.action_model,
        "boundary":bundle.boundary_model,
        "enforcement":bundle.enforcement_model,
        "evidence":bundle.evidence_model,
    }
    true={
        "assessment":[c["assessment"] for c in cases],
        "action":[c["action"] for c in cases],
        "boundary":[c["boundary"] for c in cases],
        "enforcement":[c["enforcement"] for c in cases],
        "evidence":[c["evidence"] for c in cases],
    }
    out={}
    for k,m in models.items():
        yp=list(m.predict(X)); yt=true[k]
        out[k]={"accuracy":accuracy_score(yt,yp),
                "macro_f1":f1_score(yt,yp,average="macro",zero_division=0),
                "true":yt,"pred":yp}
    return out

def tune(train,dev):
    best=None; rows=[]
    for C in [0.1,1.0,10.0]:
        b=train_bundle(train,C)
        m=eval_rows(b,dev)
        rec={"C":C,"dev_action_accuracy":m["action"]["accuracy"],
             "dev_action_macro_f1":m["action"]["macro_f1"],
             "dev_assessment_accuracy":m["assessment"]["accuracy"]}
        rows.append(rec)
        key=(m["action"]["macro_f1"],m["action"]["accuracy"],m["assessment"]["accuracy"],-C)
        if best is None or key>best[0]:
            best=(key,C)
    return best[1],rows

def plot_before_after(idacc,before,after):
    fig,ax=plt.subplots(figsize=(7.6,4.8))
    ax.bar(["ID test","OOD before","OOD after"],
           [idacc,before,after])
    ax.set_ylim(0,1.05); ax.set_ylabel("Action accuracy")
    ax.set_title("Research / IRB Agent: ID and OOD Action Accuracy")
    fig.tight_layout()
    fig.savefig(FIG/"fig23_action_accuracy.png",dpi=300,bbox_inches="tight")
    fig.savefig(FIG/"fig23_action_accuracy.pdf",bbox_inches="tight")
    plt.close(fig)

def plot_metrics(before,after):
    keys=["assessment","action","boundary","enforcement","evidence"]
    labels=["Assessment","Action","Boundary","Enforcement","Evidence"]
    x=np.arange(len(keys)); w=.36
    fig,ax=plt.subplots(figsize=(9,5.2))
    ax.bar(x-w/2,[before[k]["accuracy"] for k in keys],w,label="OOD before")
    ax.bar(x+w/2,[after[k]["accuracy"] for k in keys],w,label="OOD after")
    ax.set_ylim(0,1.05); ax.set_ylabel("Accuracy")
    ax.set_title("Research / IRB Agent OOD Performance")
    ax.set_xticks(x); ax.set_xticklabels(labels,rotation=20,ha="right"); ax.legend()
    fig.tight_layout()
    fig.savefig(FIG/"fig23_ood_metrics.png",dpi=300,bbox_inches="tight")
    fig.savefig(FIG/"fig23_ood_metrics.pdf",bbox_inches="tight")
    plt.close(fig)

def plot_safety(errors_before,errors_after,unsafe_exec):
    fig,ax=plt.subplots(figsize=(8,4.8))
    ax.bar(["OOD errors before","OOD errors after","Unsafe executions after shield"],
           [errors_before,errors_after,unsafe_exec])
    ax.set_ylabel("Count"); ax.set_title("Research / IRB Generalization and Safety")
    fig.tight_layout()
    fig.savefig(FIG/"fig23_errors_and_safety.png",dpi=300,bbox_inches="tight")
    fig.savefig(FIG/"fig23_errors_and_safety.pdf",bbox_inches="tight")
    plt.close(fig)

def plot_confusion(yt,yp):
    labels=sorted(set(yt)|set(yp))
    cm=confusion_matrix(yt,yp,labels=labels)
    fig,ax=plt.subplots(figsize=(9,7)); im=ax.imshow(cm,aspect="auto")
    ax.set_title("Research / IRB OOD Action Confusion Matrix")
    ax.set_xlabel("Predicted action"); ax.set_ylabel("True action")
    ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels,rotation=45,ha="right",fontsize=8)
    ax.set_yticklabels(labels,fontsize=8)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j,i,str(cm[i,j]),ha="center",va="center",fontsize=8)
    fig.colorbar(im,ax=ax,fraction=.046,pad=.04); fig.tight_layout()
    fig.savefig(FIG/"fig23_ood_action_confusion.png",dpi=300,bbox_inches="tight")
    fig.savefig(FIG/"fig23_ood_action_confusion.pdf",bbox_inches="tight")
    plt.close(fig)

def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 23")
    print(" Research / IRB Agent Learning")
    print(" with Compositional Coverage")
    print("========================================\n")

    rows=load_rows()
    train=[r for r in rows if r["split"]=="train"]
    dev=[r for r in rows if r["split"]=="dev"]
    test=[r for r in rows if r["split"]=="test"]

    C,tuning=tune(train,dev)
    with (OUT/"gate23_dev_tuning.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(tuning[0].keys())); w.writeheader(); w.writerows(tuning)

    base=train_bundle(train,C)
    id_base=eval_rows(base,test)

    ood=build_ood()
    before=eval_ood(base,ood)

    aug=build_augmentation()
    ood_sigs={sig(c["features"]) for c in ood}
    aug_sigs={sig(c["features"]) for c in aug}
    overlap=ood_sigs & aug_sigs

    train_aug=train+[row_from_aug(a) for a in aug]
    final=train_bundle(train_aug,C)
    id_final=eval_rows(final,test)
    after=eval_ood(final,ood)
    save_bundle(final,OUT/"research_irb_agent_model.joblib")

    pred_rows=[]
    unsafe_raw=0; unsafe_exec=0
    for i,c in enumerate(ood):
        pa=after["action"]["pred"][i]
        st,enf=shield(pa,c["features"])
        # unsafe = allowing research when authorization/governance conditions fail
        f=c["features"]
        raw_unsafe = (
            pa=="ALLOW_AUTHORIZED_RESEARCH_PROCESSING" and not (
                f.get("research_consent")=="active"
                and f.get("irb_status")=="approved"
                and f.get("pseudonymized") is True
            )
        )
        unsafe_raw += int(raw_unsafe)
        unsafe_exec += int(raw_unsafe and enf=="PERMIT")
        pred_rows.append({
            "record_id":c["record_id"],
            "features_json":json.dumps(f,sort_keys=True),
            "true_action":after["action"]["true"][i],
            "before_action":before["action"]["pred"][i],
            "after_action":pa,
            "shield_status":st,
            "shield_enforcement":enf,
            "raw_unsafe":raw_unsafe,
        })

    with (OUT/"gate23_ood_predictions.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(pred_rows[0].keys())); w.writeheader(); w.writerows(pred_rows)

    aug_rows=[{
        "record_id":a["record_id"],
        "features_json":json.dumps(a["features"],sort_keys=True),
        "target_assessment":a["assessment"],
        "target_action":a["action"],
        "target_boundary_status":a["boundary"],
        "target_enforcement":a["enforcement"],
        "target_evidence_request":a["evidence"],
    } for a in aug]
    with (OUT/"gate23_compositional_augmentation.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(aug_rows[0].keys())); w.writeheader(); w.writerows(aug_rows)

    err_before=sum(a!=b for a,b in zip(before["action"]["true"],before["action"]["pred"]))
    err_after=sum(a!=b for a,b in zip(after["action"]["true"],after["action"]["pred"]))

    methodology={
        "agent":"Research / IRB Agent",
        "benchmark_role":"policy-grounded institutional decision benchmark",
        "original_dataset":"data/learning/gate21a/research_irb_agent.csv",
        "original_split":{"train":len(train),"dev":len(dev),"test":len(test)},
        "feature_scope":[
            "research_consent","irb_status","pseudonymized","audit_required"
        ],
        "label_source":"deterministic Research/IRB institutional oracle",
        "oracle_precedence":[
            "withdrawn consent blocks research processing",
            "missing consent/IRB state triggers insufficient-evidence escalation",
            "non-approved IRB or inadequate pseudonymization triggers IRB review",
            "approved/active state may preserve audit log or allow research processing"
        ],
        "augmentation_rationale":(
            "Gate 22B/22C demonstrated that atomic templates alone can underrepresent "
            "rule interactions. Research/IRB augmentation therefore adds interaction-rich "
            "non-OOD states before considering a more complex model."
        ),
        "anti_leakage":"all Gate-23 OOD core signatures excluded from augmentation",
        "augmentation_records":len(aug),
        "ood_records":len(ood),
        "ood_overlap":len(overlap),
        "patient_data":False,
    }
    (OUT/"gate23_dataset_methodology.json").write_text(
        json.dumps(methodology,indent=2,ensure_ascii=False),encoding="utf-8")

    plot_before_after(id_final["action"]["accuracy"],before["action"]["accuracy"],after["action"]["accuracy"])
    plot_metrics(before,after)
    plot_safety(err_before,err_after,unsafe_exec)
    plot_confusion(after["action"]["true"],after["action"]["pred"])

    checks=[
        {"check":"zero_ood_augmentation_overlap","pass":len(overlap)==0,"observed":len(overlap),"expected":0},
        {"check":"id_action_accuracy","pass":id_final["action"]["accuracy"]>=0.90,
         "observed":id_final["action"]["accuracy"],"expected":">=0.90"},
        {"check":"ood_action_accuracy","pass":after["action"]["accuracy"]>=0.80,
         "observed":after["action"]["accuracy"],"expected":">=0.80"},
        {"check":"ood_action_macro_f1","pass":after["action"]["macro_f1"]>=0.75,
         "observed":after["action"]["macro_f1"],"expected":">=0.75"},
        {"check":"ood_assessment_accuracy","pass":after["assessment"]["accuracy"]>=0.80,
         "observed":after["assessment"]["accuracy"],"expected":">=0.80"},
        {"check":"unsafe_execution_after_shield","pass":unsafe_exec==0,
         "observed":unsafe_exec,"expected":0},
        {"check":"publication_plots","pass":len(list(FIG.glob("*.png")))>=4 and len(list(FIG.glob("*.pdf")))>=4,
         "observed":{"png":len(list(FIG.glob("*.png"))),"pdf":len(list(FIG.glob("*.pdf")))},
         "expected":">=4 PNG and >=4 PDF"},
        {"check":"dataset_methodology_recorded","pass":(OUT/"gate23_dataset_methodology.json").exists(),
         "observed":True,"expected":True},
    ]
    passed=sum(c["pass"] for c in checks)

    def compact(m):
        return {k:{"accuracy":v["accuracy"],"macro_f1":v["macro_f1"]} for k,v in m.items()}

    result={
        "gate":"GATE_23_RESEARCH_IRB_AGENT_LEARNING",
        "status":"PASS" if passed==len(checks) else "FAIL",
        "passed_checks":passed,"total_checks":len(checks),
        "agent":"Research / IRB Agent",
        "training_performed":True,
        "model_family":"multinomial_logistic_regression",
        "chosen_C":C,
        "original_train_records":len(train),
        "dev_records":len(dev),
        "id_test_records":len(test),
        "augmentation_records":len(aug),
        "combined_training_records":len(train_aug),
        "ood_records":len(ood),
        "ood_augmentation_overlap":len(overlap),
        "id_metrics":compact(id_final),
        "ood_metrics_before":compact(before),
        "ood_metrics_after":compact(after),
        "ood_action_errors_before":err_before,
        "ood_action_errors_after":err_after,
        "unsafe_raw_proposals_after":unsafe_raw,
        "unsafe_executed_after_policy_shield":unsafe_exec,
        "model_path":"outputs/gate23/research_irb_agent_model.joblib",
        "figures_directory":"outputs/gate23/figures",
        "next_dependency":"Gate 24 Cyber / Network Agent learning if Gate 23 passes."
    }
    (OUT/"gate23_checks.json").write_text(json.dumps(checks,indent=2),encoding="utf-8")
    (OUT/"gate23_status.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    print(f"\nOutputs saved to:\n{OUT}")
    if result["status"]!="PASS":
        raise SystemExit("Gate 23 FAILED. Diagnose Research/IRB errors before training another agent.")
    print("\nFULL GATE 23 PASS — Research / IRB Agent learned with compositional coverage, untouched OOD evaluation, publication plots, and zero unsafe shielded execution.")

if __name__=="__main__":
    main()
