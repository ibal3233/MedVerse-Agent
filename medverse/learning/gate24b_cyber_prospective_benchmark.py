from __future__ import annotations
from typing import Dict, Any, List
import hashlib, json

FUTURE_GROUPS = [5, 6, 7, 8]
REPS = [0, 1, 2]
CYBER_BASES = [
    ('healthy', {'certificate_status':'valid','packet_loss':0.01,'rtt_ms':40,'jitter_ms':5}, 'TELEMETRY_TRUST_ACCEPTABLE','PRESERVE_TECHNICAL_LOGS'),
    ('loss', {'certificate_status':'valid','packet_loss':0.27,'rtt_ms':420,'jitter_ms':90}, 'TELEMETRY_RELIABILITY_DEGRADED','MARK_TELEMETRY_UNVERIFIED'),
    ('cert', {'certificate_status':'mismatch','packet_loss':0.03,'rtt_ms':55,'jitter_ms':7}, 'DEVICE_IDENTITY_INTEGRITY_UNCERTAIN','VERIFY_DEVICE_IDENTITY'),
    ('session', {'certificate_status':'valid','packet_loss':0.02,'rtt_ms':50,'jitter_ms':6,'session_origin':'abnormal'}, 'DEVICE_IDENTITY_INTEGRITY_UNCERTAIN','ISOLATE_SUSPECT_SESSION'),
    ('alt_channel', {'certificate_status':'mismatch','packet_loss':0.20,'rtt_ms':700,'jitter_ms':150}, 'DEVICE_IDENTITY_INTEGRITY_UNCERTAIN','REQUEST_ALTERNATIVE_CHANNEL'),
    ('logs', {'certificate_status':'valid','packet_loss':0.08,'rtt_ms':80,'jitter_ms':15}, 'TELEMETRY_RELIABILITY_DEGRADED','PRESERVE_TECHNICAL_LOGS'),
]

def perturb_numeric(v, group, rep, scale=1.0):
    return round(v + (group-2)*scale + rep*(scale/5), 4)

def make_record_id(base_id, group, rep, features):
    raw=json.dumps({'agent':'cyber_network_agent','concept':'telemetry_security','base_id':base_id,'group':group,'rep':rep,'features':features},sort_keys=True)
    return 'G24B-'+hashlib.sha256(raw.encode()).hexdigest()[:18]

def build_prospective_records()->List[Dict[str,Any]]:
    rows=[]
    for g in FUTURE_GROUPS:
        for r in REPS:
            for base_id,f,assessment,action in CYBER_BASES:
                x=dict(f)
                x['packet_loss']=max(0,perturb_numeric(x['packet_loss'],g,r,0.0015))
                x['rtt_ms']=max(1,perturb_numeric(x['rtt_ms'],g,r,2.0))
                x['jitter_ms']=max(0,perturb_numeric(x['jitter_ms'],g,r,0.8))
                rows.append({
                    'record_id':make_record_id(base_id,g,r,x),'prospective_group':g,'rep':r,'base_scenario':base_id,
                    'features_json':json.dumps(x,sort_keys=True),'target_assessment':assessment,'target_action':action,
                    'target_boundary_status':'COMPLIANT','target_enforcement':'PERMIT','target_evidence_request':'',
                    'synthetic_policy_benchmark':True,'patient_data':False})
    return rows
