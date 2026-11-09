from pathlib import Path
import subprocess,sys,json,time,urllib.request,venv,tempfile,os
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[2];out=root/'outputs/final_validation'
temporary=tempfile.TemporaryDirectory(prefix='medverse-clean-');venv_path=Path(temporary.name)
venv.EnvBuilder(with_pip=False).create(venv_path)
python=venv_path/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
log=(out/'clean_runtime_server.log').open('w')
p=subprocess.Popen([str(python),'-I','-B',str(root/'run_final_sandbox.py'),'--port','8766'],stdout=log,stderr=subprocess.STDOUT)
checks=[]
def check(n,b):checks.append({'check':n,'pass':bool(b)})
def req(path,body=None,token=''):
 data=json.dumps(body).encode() if body else None
 q=urllib.request.Request('http://127.0.0.1:8766'+path,data=data,headers={'Content-Type':'application/json','X-Session-Token':token})
 with urllib.request.urlopen(q,timeout=5) as r:return json.loads(r.read())
try:
 for _ in range(50):
  try:h=req('/api/health');break
  except Exception:time.sleep(.1)
 else:raise RuntimeError('Clean server failed')
 check('server_launch_without_third_party_packages',h['external_execution']==False)
 d=req('/api/session',{'family_id':'WF05'});token=d['token'];id=d['session_id']
 for _ in range(6):d=req('/api/advance',{'session_id':id},token)
 snap=d['snapshot'];check('six_events_replayed',d['released_events']==6)
 check('clinical_review_committed',any(x['action']=='REQUEST_CLINICAL_REVIEW' for x in snap['effects']))
 check('minimized_view_committed',any(x['action']=='RELEASE_MINIMIZED_VIEW' for x in snap['effects']))
 check('audit_chain_valid',snap['audit_chain_valid'])
 results=req('/api/search',{'query':'KR-PIPA-ART28-2-PSEUDONYM-001','role':'privacy_agent'});check('exact_corpus_lookup_available',results['status']=='EXACT_MATCH')
 report={'status':'PASS' if all(x['pass'] for x in checks) else 'FAIL','checks':checks,'environment':'Fresh venv without pip or third-party packages; isolated Python (-I -B). Linux/Python 3.13.5.','scope':'Runtime and local HTTP replay, not a Windows/Spyder test and not a fresh learned-model validation.'}
 (out/'clean_runtime_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:
 p.terminate();p.wait(timeout=10);log.close();temporary.cleanup()
