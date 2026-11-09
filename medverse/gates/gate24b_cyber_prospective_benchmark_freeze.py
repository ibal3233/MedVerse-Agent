from __future__ import annotations
from pathlib import Path
from collections import Counter
import csv, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import matplotlib.pyplot as plt
import numpy as np
from medverse.learning.gate24b_cyber_prospective_benchmark import build_prospective_records,FUTURE_GROUPS,CYBER_BASES
OUT=ROOT/'outputs'/'gate24b'; FIG=OUT/'figures'; DATA_OUT=ROOT/'data'/'learning'/'gate24b'
OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(parents=True,exist_ok=True); DATA_OUT.mkdir(parents=True,exist_ok=True)
ORIGINAL=ROOT/'data'/'learning'/'gate21a'/'cyber_network_agent.csv'

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(65536),b''): h.update(chunk)
    return h.hexdigest()

def plot_group_sizes(rows):
    c=Counter(r['prospective_group'] for r in rows)
    fig,ax=plt.subplots(figsize=(7.2,4.6)); ax.bar([f'g{g}' for g in FUTURE_GROUPS],[c[g] for g in FUTURE_GROUPS]); ax.set_ylabel('Prospective records'); ax.set_title('Gate 24B Prospective Cyber/Network Group Sizes'); fig.tight_layout(); fig.savefig(FIG/'fig24b_group_sizes.png',dpi=300,bbox_inches='tight'); fig.savefig(FIG/'fig24b_group_sizes.pdf',bbox_inches='tight'); plt.close(fig)

def plot_action_support(rows):
    labels=sorted({r['target_action'] for r in rows}); x=np.arange(len(labels)); w=0.18
    fig,ax=plt.subplots(figsize=(10,5.4))
    for i,g in enumerate(FUTURE_GROUPS):
        c=Counter(r['target_action'] for r in rows if r['prospective_group']==g); ax.bar(x+(i-1.5)*w,[c.get(k,0) for k in labels],w,label=f'g{g}')
    ax.set_ylabel('Records'); ax.set_title('Prospective Action-Class Support by Future Group'); ax.set_xticks(x); ax.set_xticklabels(labels,rotation=30,ha='right',fontsize=8); ax.legend(); fig.tight_layout(); fig.savefig(FIG/'fig24b_action_support.png',dpi=300,bbox_inches='tight'); fig.savefig(FIG/'fig24b_action_support.pdf',bbox_inches='tight'); plt.close(fig)

def plot_numeric_drift(rows):
    for key in ['packet_loss','rtt_ms','jitter_ms']:
        vals=[]
        for g in FUTURE_GROUPS:
            vals.append(float(np.mean([json.loads(r['features_json'])[key] for r in rows if r['prospective_group']==g])))
        fig,ax=plt.subplots(figsize=(7.5,4.6)); ax.plot([f'g{g}' for g in FUTURE_GROUPS],vals,marker='o'); ax.set_ylabel(f'Mean {key}'); ax.set_title(f'Prospective Cyber/Network Drift: {key}'); fig.tight_layout(); fig.savefig(FIG/f'fig24b_drift_{key}.png',dpi=300,bbox_inches='tight'); fig.savefig(FIG/f'fig24b_drift_{key}.pdf',bbox_inches='tight'); plt.close(fig)

def main():
    print('\n========================================\n MedVerse-Agent - Gate 24B\n Prospective Cyber / Network\n Confirmation Benchmark Freeze\n========================================\n')
    rows=build_prospective_records(); benchmark_path=DATA_OUT/'cyber_network_prospective_groups_g5_g8.csv'
    with benchmark_path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    benchmark_hash=sha256(benchmark_path)
    with ORIGINAL.open('r',encoding='utf-8-sig',newline='') as f: orig=list(csv.DictReader(f))
    original_features={r['features_json'] for r in orig}; overlap=sum(r['features_json'] in original_features for r in rows)
    group_counts=Counter(r['prospective_group'] for r in rows); action_counts=Counter(r['target_action'] for r in rows); assessment_counts=Counter(r['target_assessment'] for r in rows)
    action_by_group={str(g):dict(Counter(r['target_action'] for r in rows if r['prospective_group']==g)) for g in FUTURE_GROUPS}
    protocol={
        'protocol_id':'MEDVERSE-G24B-CYBER-PROSPECTIVE-GROUPS-v1','status':'PRE_FROZEN_BEFORE_PREPROCESSING_REPAIR_TRAINING','training_performed':False,
        'source_semantics':'Exact six-scenario Cyber/Network Gate-21A generator semantics extended prospectively from g0-g4 to g5-g8.',
        'prospective_groups':FUTURE_GROUPS,'records_per_group':{str(g):group_counts[g] for g in FUTURE_GROUPS},'total_records':len(rows),
        'future_training_rule':'Fit only on Gate-21A TRAIN g0-g2; select hyperparameters on DEV g3 only; g4 remains diagnostic-only.',
        'future_confirmation_rule':'After preprocessing and C are fixed using TRAIN/DEV only, evaluate once on g5-g8. Do not use g5-g8 for selection.',
        'authorized_repair':{'numeric_preprocessing':'TRAIN-fitted standardization of packet_loss, rtt_ms, jitter_ms','categorical_preprocessing':'explicit __MISSING__ for absent session_origin','model_family':'multinomial_logistic_regression'},
        'hyperparameter_grid':[0.01,0.03,0.1,0.3,1.0,3.0,10.0],
        'training_history_required':True,'training_history_definition':['group-wise cumulative learning curve','train-vs-dev hyperparameter path','solver convergence iterations'],
        'confirmation_thresholds':{'prospective_action_accuracy':0.90,'prospective_action_macro_f1':0.85,'prospective_assessment_accuracy':0.90,'prospective_assessment_macro_f1':0.80,'all_action_class_recall_minimum':0.80},
        'claim_boundary':'Synthetic prospective generator-shift benchmark derived from frozen scenario semantics; not external network telemetry or clinical data.',
        'opened_gate24_test_status':'DIAGNOSTIC_ONLY','patient_data':False,'benchmark_sha256':benchmark_hash}
    (OUT/'gate24b_frozen_protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    (OUT/'gate24b_freeze_manifest.json').write_text(json.dumps({'protocol_id':protocol['protocol_id'],'benchmark_file':str(benchmark_path.relative_to(ROOT)).replace('\\','/'),'benchmark_sha256':benchmark_hash,'created_before_repair_training':True,'training_performed_in_gate24b':False,'records':len(rows),'unique_record_ids':len({r['record_id'] for r in rows}),'exact_feature_overlap_with_gate21a':overlap},indent=2),encoding='utf-8')
    (OUT/'gate24b_class_support.json').write_text(json.dumps({'total_action_counts':dict(action_counts),'total_assessment_counts':dict(assessment_counts),'action_counts_by_group':action_by_group,'base_scenario_counts':dict(Counter(r['base_scenario'] for r in rows))},indent=2),encoding='utf-8')
    plot_group_sizes(rows); plot_action_support(rows); plot_numeric_drift(rows)
    expected_actions={x[3] for x in CYBER_BASES}; expected_assessments={x[2] for x in CYBER_BASES}
    checks=[
        {'check':'expected_record_count','pass':len(rows)==72,'observed':len(rows),'expected':72},
        {'check':'balanced_future_groups','pass':all(group_counts[g]==18 for g in FUTURE_GROUPS),'observed':{str(g):group_counts[g] for g in FUTURE_GROUPS},'expected':'18 per group'},
        {'check':'all_action_classes_present_each_group','pass':all(set(action_by_group[str(g)])==expected_actions for g in FUTURE_GROUPS),'observed':action_by_group,'expected':sorted(expected_actions)},
        {'check':'all_assessment_classes_present','pass':set(assessment_counts)==expected_assessments,'observed':sorted(assessment_counts),'expected':sorted(expected_assessments)},
        {'check':'no_exact_feature_reuse','pass':overlap==0,'observed':overlap,'expected':0},
        {'check':'unique_record_ids','pass':len({r['record_id'] for r in rows})==72,'observed':len({r['record_id'] for r in rows}),'expected':72},
        {'check':'benchmark_hash_recorded','pass':len(benchmark_hash)==64,'observed':benchmark_hash,'expected':'SHA256'},
        {'check':'protocol_frozen_before_training','pass':protocol['status']=='PRE_FROZEN_BEFORE_PREPROCESSING_REPAIR_TRAINING' and protocol['training_performed'] is False,'observed':{'status':protocol['status'],'training_performed':protocol['training_performed']},'expected':'pre-frozen, no training'},
        {'check':'publication_outputs','pass':len(list(FIG.glob('*.png')))>=5 and len(list(FIG.glob('*.pdf')))>=5,'observed':{'png':len(list(FIG.glob('*.png'))),'pdf':len(list(FIG.glob('*.pdf')))},'expected':'>=5 PNG and >=5 PDF'}]
    passed=sum(c['pass'] for c in checks)
    status={'gate':'GATE_24B_CYBER_PROSPECTIVE_BENCHMARK_FREEZE','status':'PASS' if passed==len(checks) else 'FAIL','passed_checks':passed,'total_checks':len(checks),'training_performed':False,'protocol_id':protocol['protocol_id'],'prospective_groups':FUTURE_GROUPS,'prospective_records':len(rows),'records_per_group':{str(g):group_counts[g] for g in FUTURE_GROUPS},'action_classes':sorted(action_counts),'assessment_classes':sorted(assessment_counts),'exact_feature_overlap_with_gate21a':overlap,'benchmark_sha256':benchmark_hash,'opened_gate24_test_status':'DIAGNOSTIC_ONLY','new_benchmark_status':'PRE_FROZEN_BEFORE_REPAIR_TRAINING','training_history_required_in_gate24c':True,'figures_directory':'outputs/gate24b/figures','next_dependency':'Gate 24C: apply TRAIN-fitted scaling + explicit session_origin missing category, DEV-only C selection, retain training-history plots, then evaluate once on frozen g5-g8.'}
    (OUT/'gate24b_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8'); (OUT/'gate24b_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    print(json.dumps(status,indent=2)); print(f'\nBenchmark saved to:\n{benchmark_path}\nSHA256:\n{benchmark_hash}\n\nOutputs saved to:\n{OUT}')
    if status['status']!='PASS': raise SystemExit('Gate 24B FAILED. Do not train repair until prospective benchmark is valid.')
    print('\nFULL GATE 24B PASS — Fresh Cyber/Network prospective groups g5-g8 are frozen before repair training.')
if __name__=='__main__': main()
