"""Loopback-only integrated workbench. Real institutional credentials are out of scope."""
from __future__ import annotations
import argparse,json,mimetypes,secrets,threading,time
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
from final_validation.server import Handler as LegacyHandler
from .common import ROOT,OUT,ROLES,LABELS,source_cases,load
from .engine import IntegratedSession,IntegrationError
WEB=Path(__file__).parent/'web'
class Workbench:
 def __init__(self):self.sessions={};self.lock=threading.RLock()
 def create(self,body):
  ident=secrets.token_urlsafe(18);token=secrets.token_urlsafe(26)
  engine=IntegratedSession(body.get('family_id','C12'),body.get('strategy','MEDVERSE_HARMONIZER'),body.get('mode','PROGRESSIVE'))
  with self.lock:
   if len(self.sessions)>300:self.sessions.pop(next(iter(self.sessions)))
   self.sessions[ident]={'engine':engine,'token':token}
  return {'session_id':ident,'token':token,'snapshot':engine.snapshot()}
 def record(self,body,token):
  rec=self.sessions.get(body.get('session_id',''))
  if not rec or not secrets.compare_digest(rec['token'],token or ''):raise PermissionError('INVALID_LOCAL_SESSION_TOKEN')
  return rec
APP=Workbench()
ALLOWED={
 '/api30/session':{'family_id','strategy','mode'},
 '/api30/advance':{'session_id','auto_commit'},
 '/api30/commit':{'session_id','plan_id'},
 '/api30/change':{'session_id','kind'},
 '/api30/cancel':{'session_id'},
 '/api30/export':{'session_id'},
 '/api30/view':{'session_id','role'},
 '/api30/snapshot':{'session_id'},
}
class Handler(LegacyHandler):
 server_version='MedVerseIntegrated/2.0'
 def do_GET(self):
  path=urlparse(self.path).path
  try:
   if path=='/api30/health':return self.respond(200,{'status':'READY','version':'Gate30-integrated-v1','simulated':True,'selector':'unmodified coordination29.selectors','external_actions':False})
   if path=='/api30/config':return self.respond(200,{'roles':ROLES,'strategies':LABELS,'scenarios':[{'id':c['family_id'],'name':c['motif'].replace('_',' '),'track':c['track'],'previous_split':c['split']} for c in source_cases()],'default_family':'C12','purpose':'Integration regression on previously used scenario models; not new confirmation','retrieval':'Lexical bilingual BM25; no dense-embedding claim'})
   if path=='/api30/results':
    files=sorted(OUT.glob('*/status.json'))
    if not files:return self.respond(200,{'status':'NOT_YET_EVALUATED'})
    p=files[-1];v=load(p)
    for key,name in [('case_metrics','snapshot_metrics.json'),('progressive_metrics','progressive_metrics.json'),('tables','concise_results.json')]:
     if (p.parent/name).exists():v[key]=load(p.parent/name)
    return self.respond(200,v)
   if path.startswith('/api/'):return super().do_GET()
   if path.startswith('/results/'):
    rel=path[len('/results/'):];target=(OUT/rel).resolve()
    if not target.is_relative_to(OUT.resolve()) or not target.is_file() or target.suffix not in {'.png','.pdf','.csv','.json'}:return self.respond(404,{'error':'NOT_FOUND'})
   else:
    rel='index.html' if path=='/' else path.lstrip('/');target=(WEB/rel).resolve()
    if not target.is_relative_to(WEB.resolve()) or not target.is_file():return self.respond(404,{'error':'NOT_FOUND'})
   typ=mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
   return self.respond(200,target.read_bytes(),typ+('; charset=utf-8' if typ.startswith(('text/','application/javascript')) else ''))
  except Exception as e:return self.respond(500,{'error':type(e).__name__,'message':str(e)})
 def do_POST(self):
  path=urlparse(self.path).path
  if not path.startswith('/api30/'):return super().do_POST()
  try:
   origin=self.headers.get('Origin');host=self.headers.get('Host','')
   if origin and origin not in {'http://'+host,'https://'+host}:return self.respond(403,{'error':'CROSS_ORIGIN_REJECTED'})
   n=int(self.headers.get('Content-Length','0'))
   if n<2 or n>200000:return self.respond(400,{'error':'INVALID_BODY_SIZE'})
   if 'application/json' not in self.headers.get('Content-Type',''):return self.respond(415,{'error':'JSON_REQUIRED'})
   body=json.loads(self.rfile.read(n))
   if path not in ALLOWED:return self.respond(404,{'error':'NOT_FOUND'})
   if not isinstance(body,dict) or set(body)-ALLOWED[path]:return self.respond(400,{'error':'UNSUPPORTED_INPUT_FIELDS'})
   if path=='/api30/session':return self.respond(200,APP.create(body))
   with APP.lock:
    rec=APP.record(body,self.headers.get('X-Session-Token'));engine=rec['engine']
    if path=='/api30/advance':
     auto=body.get('auto_commit',True)
     if not isinstance(auto,bool):raise IntegrationError('AUTO_COMMIT_MUST_BE_BOOLEAN')
     value=engine.advance(auto)
    elif path=='/api30/commit':value=engine.commit(body.get('plan_id'))
    elif path=='/api30/change':value=engine.change(body.get('kind'))
    elif path=='/api30/cancel':engine.cancel();value=engine.snapshot()
    elif path=='/api30/export':return self.respond(200,engine.export())
    elif path=='/api30/view':
     role=body.get('role')
     if role not in ROLES:raise IntegrationError('UNKNOWN_INSTITUTION')
     return self.respond(200,engine.snapshot()['roles'][role])
    else:value=engine.snapshot()
   return self.respond(200,{'session_id':body['session_id'],'snapshot':value})
  except PermissionError as e:return self.respond(403,{'error':str(e)})
  except (IntegrationError,ValueError,TypeError) as e:return self.respond(400,{'error':str(e)})
  except Exception as e:return self.respond(500,{'error':type(e).__name__,'message':str(e)})

def make_server(port=0):return ThreadingHTTPServer(('127.0.0.1',port),Handler)
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--open',action='store_true');a=p.parse_args(argv)
 s=make_server(a.port);url='http://127.0.0.1:'+str(s.server_address[1])
 print('Team MedVerse integrated workbench:',url,flush=True)
 print('New runtime: Gate 29 selection + progressive release + final revalidation. All actions are modeled. Ctrl+C stops.',flush=True)
 if a.open:
  import webbrowser;webbrowser.open(url)
 try:s.serve_forever()
 except KeyboardInterrupt:pass
 finally:s.server_close()
if __name__=='__main__':main()
