"""Run known-fixture DT/retrieval regression; no confirmation selection or tuning."""
from __future__ import annotations
import csv,importlib.metadata as metadata,json,platform,sys,time,threading,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
from .common import ROOT,DATA,OUT,CORPUS,MODEL,REVISION,ROLES,read,write,filehash,digest
from .tests import run_checks
from .retrieval import EvidenceService
from .digital_twin import ReleasedDigitalTwin
from .session import FoundationSession
from coordination30.engine import IntegratedSession,verify_receipts
from coordination30.common import source_cases

STRATEGIES=('REQUEST_ONLY','FAIR_STATEFUL_SELECTOR','INDEPENDENT_CONSTRAINT_PLANNER','MEDVERSE_HARMONIZER')
def csv_write(p,rows):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})

def verify_freeze():
    f=read(DATA/'freeze.json');checks=[]
    for rel,expected in f['files'].items():
        p=ROOT/rel;checks.append({'path':rel,'exists':p.is_file(),'unchanged':p.is_file() and filehash(p)==expected})
    if not all(c['unchanged'] for c in checks):raise RuntimeError('FROZEN_SOURCE_CHANGED: '+str([c['path'] for c in checks if not c['unchanged']]))
    old=read(ROOT/'docs/foundation31/BASELINE_FILE_HASHES.json')
    original=[{'path':rel,'unchanged':(ROOT/rel).is_file() and filehash(ROOT/rel)==expected} for rel,expected in old.items()]
    if not all(c['unchanged'] for c in original):raise RuntimeError('ORIGINAL_ARTIFACT_CHANGED')
    return {'new_frozen_files':len(checks),'unchanged_original_files':len(original),'checks':checks,'original_artifacts_changed':False}

def comparable(s):
    return {'phase':s['phase'],'committed':s['committed_ids'],'tokens':s['achieved_tokens'],'missing':s['missing_goals'],
        'disposition':s['selection']['disposition'],'roles':{r:{'observation':v['observation'],'own_proposals':v['own_proposals']} for r,v in s['roles'].items()},
        'receipts':[{k:r[k] for k in ['event','proposal_id','owner','actual_proposal','permitted','reason','modeled_side_effect']} for r in s['receipts']]}

def integration_regression(dest):
    rows=[];trace=[]
    for c in source_cases():
        for strategy in STRATEGIES:
            old=IntegratedSession(c['family_id'],strategy);new=FoundationSession(c['family_id'],strategy)
            for event in range(1,7):
                a=old.advance();b=new.advance();same=comparable(a)==comparable(b)
                rows.append({'family':c['family_id'],'prior_split':c['split'],'strategy':strategy,'event':event,
                    'same_modeled_behavior':same,'audit_chain_valid':verify_receipts(b['receipts']),
                    'core_measurements_received':b['foundation31']['digital_twin']['quality']['observed_core_count'],
                    'dt_status':b['foundation31']['digital_twin']['quality']['validity']})
                if c['family_id']=='C12' and strategy=='MEDVERSE_HARMONIZER':trace.append(b)
    csv_write(dest/'integration_regression.csv',rows);write(dest/'flagship_dt_trace.json',trace)
    return {'families':len(source_cases()),'strategies':len(STRATEGIES),'event_comparisons':len(rows),
            'unchanged_event_outcomes':sum(r['same_modeled_behavior'] for r in rows),
            'audit_chains_valid':all(r['audit_chain_valid'] for r in rows),
            'scope':'Known Gate29/30 cases. Observational noninterference regression, NOT new coordination confirmation.'}

def dt_trajectory(dest):
    d=ReleasedDigitalTwin();rows=[]
    def record(label):
        s=d.snapshot();rows.append({'label':label,'modeled_seconds':d.now,'released_event':d.release_event,
            'native_freshness':s['native_quality_diagnostic']['freshness'],
            'observed_core_freshness':s['quality']['minimum_core_freshness'],'status':s['quality']['validity'],
            'observed_fields':s['quality']['observed_core_count']})
    def fill(t,event):
        for domain,payload,owner in [('clinical',{'SpO2':97.,'heart_rate':81.},'hospital_agent'),
            ('network',{'packet_loss':.01,'rtt_ms':24.,'jitter_ms':4.},'cyber_network_agent'),
            ('security',{'certificate_status':'valid','session_origin':'normal'},'cyber_network_agent')]:
            d.ingest(event=event,modeled_seconds=t,observed_seconds=t,owner=owner,domain=domain,payload=payload,
                source_id='DEVELOPMENT_MODELED_S1_FIXTURE',message_id=f'{domain}-{t}')
    fill(0,1);record('Explicit S1 observations')
    d.tick(2,60);record('No new observations')
    d.tick(3,240);record('Telemetry aged')
    d.ingest(event=4,modeled_seconds=300,observed_seconds=300,owner='privacy_agent',domain='consent',
        payload={'review_note':'metadata only; no new telemetry or permission'},source_id='MODELED_PRIVACY',message_id='privacy-300')
    record('New consent metadata, old telemetry')
    d.ingest(event=5,modeled_seconds=360,observed_seconds=360,owner='cyber_network_agent',domain='security',
        payload={'certificate_status':'revoked'},source_id='MODELED_SECURITY',message_id='security-360')
    record('Technical provenance invalidated')
    fill(420,6);record('Fresh explicit modeled observations')
    csv_write(dest/'dt_fixture_trajectory.csv',rows);write(dest/'dt_fixture_final.json',d.snapshot());return rows

def retrieval_regression(dest,allow_download=False,cache_folder=None):
    services={b:EvidenceService(b,local_only=not allow_download,cache_folder=cache_folder) for b in ['bm25','dense']}
    queries=read(ROOT/'data/final_validation/query_families.json')['records']
    results={};metrics=[]
    for backend,service in services.items():
        rows=[];blocked=None;details=[]
        for f in queries:
            for lang in ['en','ko']:
                t=time.perf_counter();s=service.search(f[lang],f['role']);duration=(time.perf_counter()-t)*1000
                if s['status']=='BLOCKED_DENSE_BACKEND':blocked=s;break
                ids=[h['chunk_id'] for h in s['hits']];expected=f['expected_any']
                ranks=[i+1 for i,pid in enumerate(ids) if pid in expected]
                rows.append({'backend':backend,'family_id':f['family_id'],'previous_split':f['split'],'role':f['role'],
                    'language':lang,'query':f[lang],'target_source_ids':expected,'retrieved_ids':ids,
                    'rank_at3':min(ranks) if ranks else None,'hit_at3':bool(ranks),'top1':bool(ranks and min(ranks)==1),
                    'latency_ms':duration,'retrieval_status':s['status']})
                details.append({'family_id':f['family_id'],'language':lang,'previous_split':f['split'],'result':s})
            if blocked:break
        if blocked:
            write(dest/f'{backend}_blocked.json',blocked)
            results[backend]={'status':'BLOCKED_DEPENDENCY_OR_MODEL','model':service.dense.metadata,'reason':blocked['error'],
                'performance_measured':False,'fallback_used':False,'n_scored_queries':0}
            continue
        csv_write(dest/f'{backend}_query_metrics.csv',rows);write(dest/f'{backend}_query_traces.json',details)
        summary=[]
        for split in ['DEV','CONFIRMATION']:
            for lang in ['en','ko']:
                rr=[r for r in rows if r['previous_split']==split and r['language']==lang]
                row={'backend':backend,'historical_split':split,'language':lang,'n':len(rr),
                     'top1_n':sum(r['top1'] for r in rr),'recall3_n':sum(r['hit_at3'] for r in rr)}
                row['top1']=row['top1_n']/len(rr) if rr else None;row['recall3']=row['recall3_n']/len(rr) if rr else None
                summary.append(row);metrics.append(row)
        both=sum(all(r['hit_at3'] for r in rows if r['family_id']==f['family_id']) for f in queries if f['split']=='CONFIRMATION')
        results[backend]={'status':'EXECUTED','performance_measured':True,'n_scored_queries':len(rows),
            'scope':'Previously used bilingual intent families; regression/reproduction, not fresh confirmation.',
            'normalization':'original unit embeddings' if backend=='dense' else 'BM25 non-semantic scores',
            'confirmation_pairs_both_hit':both,'summary':summary,'fallback_used':False}
        if backend=='dense':results[backend]['model']=deepcopy(service.dense.metadata)
    csv_write(dest/'retrieval_summary.csv',metrics)
    counts=[]
    for role in ROLES:
        r=services['bm25'].search('research privacy records',role)
        counts.append({'role':role,'corpus_records':len(services['bm25'].records),'eligible_for_role':r.get('eligible_count',0)})
    csv_write(dest/'role_evidence_coverage.csv',counts)
    return results,counts

def http_checks(dest):
    from .server import make_server
    s=make_server(0,backend='bm25');th=threading.Thread(target=s.serve_forever,daemon=True);th.start()
    base=f'http://127.0.0.1:{s.server_port}';rows=[];session=None
    def req(path,body=None,token=None):
        headers={'Content-Type':'application/json'}
        if token:headers['X-Session-Token']=token
        q=urllib.request.Request(base+path,json.dumps(body).encode() if body is not None else None,headers=headers)
        with urllib.request.urlopen(q,timeout=20) as resp:return json.loads(resp.read())
    def check(name,value):rows.append({'check':name,'passed':bool(value)})
    try:
        health=req('/api31/health');check('backend_identity',health['default_retrieval']=='bm25')
        session=req('/api30/session',{'family_id':'C12','strategy':'MEDVERSE_HARMONIZER'})
        token=session['token'];sid=session['session_id']
        check('empty_initial_dt',session['snapshot']['foundation31']['digital_twin']['observation_count']==0)
        exported=[]
        for e in range(1,7):
            r=req('/api30/advance',{'session_id':sid},token)['snapshot'];exported.append(r)
        check('progressive_adapter',r['foundation31']['digital_twin']['released_event']==6)
        check('no_fabricated_vitals',r['foundation31']['digital_twin']['state']['clinical']=={})
        check('original_action_path_completes',not r['missing_goals'])
        check('research_has_no_patient_context','patient_context' not in r['foundation31']['role_views']['research_irb_agent']['state'])
        sr=req('/api31/search',{'query':'KR-NONEXISTENT-999','backend':'dense'})
        check('unknown_exact_without_dense',sr['status']=='UNKNOWN_EXACT_CITATION' and not sr['hits'])
        sr=req('/api31/search',{'query':'가명정보 과학적 연구','backend':'bm25','role':'privacy_agent'})
        check('explicit_lexical_backend',sr['backend']=='lexical_bilingual_bm25_v1' and sr['hits'])
        check('official_source_links',all(h.get('official_url') for h in sr['hits']))
        export=req('/api30/export',{'session_id':sid},token)
        check('dt_in_actual_export','foundation31' in export['snapshot'])
        try:req('/api30/snapshot',{'session_id':sid},'wrong');check('session_token_required',False)
        except urllib.error.HTTPError as e:check('session_token_required',e.code==403)
        write(dest/'http_flagship_trace.json',exported);write(dest/'http_export.json',export)
    finally:s.shutdown();s.server_close();th.join(timeout=5)
    write(dest/'http_checks.json',rows);return rows

def main_evaluation(allow_download=False,cache_folder=None):
    integrity=verify_freeze();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    dest=OUT/stamp;dest.mkdir(parents=True,exist_ok=False)
    write(dest/'freeze_check.json',integrity)
    packages={}
    for p in ['numpy','matplotlib','sentence-transformers','transformers','torch','huggingface-hub']:
        try:packages[p]=metadata.version(p)
        except metadata.PackageNotFoundError:packages[p]='NOT_INSTALLED'
    write(dest/'environment.json',{'python':sys.version,'platform':platform.platform(),'packages':packages,'argv':sys.argv})
    checks=run_checks();write(dest/'engineering_checks.json',checks)
    if not all(c['passed'] for c in checks):
        write(dest/'status.json',{'gate':'GATE31','engineering_integrity':'FAIL','checks':checks});raise RuntimeError(f'Engineering check failed; evidence retained at {dest}')
    regression=integration_regression(dest);trajectory=dt_trajectory(dest)
    retrieval,coverage=retrieval_regression(dest,allow_download,cache_folder);http=http_checks(dest)
    valid=regression['event_comparisons']==regression['unchanged_event_outcomes'] and regression['audit_chains_valid'] and all(r['passed'] for r in http)
    s={'gate':'GATE_31_DT_AND_EVIDENCE_FOUNDATION','run_id':stamp,'engineering_integrity':'PASS' if valid else 'FAIL',
       'checks_passed':sum(r['passed'] for r in checks),'checks_total':len(checks),
       'http_checks_passed':sum(r['passed'] for r in http),'http_checks_total':len(http),
       'original_files_unchanged':integrity['unchanged_original_files'],'integration_regression':regression,
       'retrieval':retrieval,'role_evidence_coverage':coverage,'source_corpus_sha256':filehash(CORPUS),
       'dense_execution_status':retrieval['dense']['status'],
       'training_performed':False,'tuning_performed':False,'new_clinical_observations':False,
       'commitment_controller_changed':False,'c01_c02_progressive_limitations':'RETAINED_UNCHANGED',
       'model_revision':REVISION,'clinical_legal_review':'PENDING',
       'next_dependency':'Execute dense path locally, then implement frozen-design Gate32 commitment controller; current gate does NOT repair eager commits.'}
    write(dest/'status.json',s);return s,dest
