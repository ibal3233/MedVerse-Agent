"""Local integrated operator workbench. Experimental timing is not enabled globally."""
from __future__ import annotations
import argparse,json,secrets,threading,mimetypes
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
from foundation31.server import Handler as FoundationHandler,Workbench as FoundationWorkbench
from foundation31.retrieval import EvidenceService
from foundation31 import server as foundation_server
from coordination30 import server as previous_server
from .common import ROOT,OUT,WEB,ROLES,ROLE_NAMES,STRATEGIES,read,families,verify_freeze
from .session import Workspace,WorkspaceError

class Workbench:
 def __init__(self):self.sessions={};self.lock=threading.RLock()
 def create(self,b):
  w=Workspace(b.get('family_id','P01'),b.get('branch_id','PROMPT'),b.get('strategy','MEDVERSE_COMMITMENT'))
  sid=secrets.token_urlsafe(18);token=secrets.token_urlsafe(26)
  with self.lock:
   if len(self.sessions)>=256:self.sessions.pop(next(iter(self.sessions)))
   self.sessions[sid]={'engine':w,'token':token}
  return {'session_id':sid,'token':token,'snapshot':w.snapshot()}
 def get(self,sid,token):
  r=self.sessions.get(sid)
  if r is None or not secrets.compare_digest(r['token'],token or ''):raise PermissionError('INVALID_LOCAL_SESSION_TOKEN')
  return r['engine']

ALLOWED={'session':{'family_id','branch_id','strategy'},'advance':{'session_id','expected_clock','auto_commit'},
 'commit':{'session_id','plan_id'},'change':{'session_id','kind'},'cancel':{'session_id'},
 'snapshot':{'session_id'},'role':{'session_id','role'},'export':{'session_id'}}
class Handler(FoundationHandler):
 server_version='MedVerseCommitmentWorkspace/1.0'
 def do_GET(self):
  path=urlparse(self.path).path
  if path in ('/','/index.html','/release33.js','/release33.css'):
   p=WEB/('index.html' if path in ('/','/index.html') else path[1:]);typ=mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
   return self.respond(200,p.read_bytes(),typ+'; charset=utf-8')
  if path=='/foundation':
   return self.respond(200,(foundation_server.WEB/'index.html').read_bytes(),'text/html; charset=utf-8')
  if path=='/api33/health':return self.respond(200,{'release':'Gate33','status':'READY','binding':'loopback only','default_retrieval':self.server.default_backend,'original_clinical_path':'/foundation','timing_enabled_in_original_clinical_path':False,'contract_review':'PENDING','simulated':True})
  if path=='/api33/config':
   return self.respond(200,{'roles':ROLE_NAMES,'strategies':STRATEGIES,'default_family':'P01','default_branch':'PROMPT',
    'families':[{'id':f['family_id'],'title':f['title'],'historical_split':f['split'],
      'continuations':[b['branch_id'] for b in f['branches']]} for f in families()],
    'scope':'Operator-configured known scenario replays. No future events or reference outcomes are inputs to the controller.'})
  if path=='/api33/results':
   paths=sorted(OUT.glob('*/status.json'));return self.respond(200,read(paths[-1]) if paths else {'status':'NOT_YET_EVALUATED'})
  return super().do_GET()
 def do_POST(self):
  path=urlparse(self.path).path
  if not path.startswith('/api33/'):return super().do_POST()
  op=path.rsplit('/',1)[-1]
  try:
   origin=self.headers.get('Origin');host=self.headers.get('Host','')
   if origin and origin not in ('http://'+host,'https://'+host):return self.respond(403,{'error':'CROSS_ORIGIN_REJECTED'})
   if op not in ALLOWED:return self.respond(404,{'error':'NOT_FOUND'})
   if 'application/json' not in self.headers.get('Content-Type',''):return self.respond(415,{'error':'JSON_REQUIRED'})
   n=int(self.headers.get('Content-Length','0'))
   if n<2 or n>20000:return self.respond(400,{'error':'INVALID_BODY_SIZE'})
   b=json.loads(self.rfile.read(n))
   if not isinstance(b,dict) or set(b)-ALLOWED[op]:return self.respond(400,{'error':'UNSUPPORTED_INPUT_FIELDS'})
   if op=='session':return self.respond(200,self.server.workspace.create(b))
   with self.server.workspace.lock:
    w=self.server.workspace.get(b.get('session_id',''),self.headers.get('X-Session-Token'))
    if op=='advance':value=w.advance(b.get('expected_clock'),b.get('auto_commit',True))
    elif op=='commit':value=w.commit(b.get('plan_id'))
    elif op=='change':value=w.change(b.get('kind'))
    elif op=='cancel':value=w.cancel()
    elif op=='export':return self.respond(200,w.export())
    elif op=='role':
     if b.get('role') not in ROLES:raise WorkspaceError('UNKNOWN_INSTITUTION')
     return self.respond(200,w.roles()[b['role']])
    else:value=w.snapshot()
   return self.respond(200,{'session_id':b['session_id'],'snapshot':value})
  except PermissionError as e:return self.respond(403,{'error':str(e)})
  except (ValueError,TypeError,KeyError) as e:return self.respond(400,{'error':str(e)})
  except Exception as e:return self.respond(500,{'error':type(e).__name__,'message':str(e)})

def make_server(port=0,backend='dense',allow_download=False,cache_folder=None):
 # Original routes keep their original state machines. This shares only a host and evidence service.
 previous_server.APP=FoundationWorkbench()
 s=ThreadingHTTPServer(('127.0.0.1',port),Handler);s.workspace=Workbench();s.default_backend=backend
 s.services={k:EvidenceService(k,local_only=not allow_download,cache_folder=cache_folder) for k in ('dense','bm25')}
 return s

def main(argv=None):
 p=argparse.ArgumentParser(description='Team MedVerse: optional modeled commitment workspace + unchanged original DT/evidence application')
 p.add_argument('--port',type=int,default=8765);p.add_argument('--open',action='store_true');p.add_argument('--backend',choices=('dense','bm25'),default='dense')
 p.add_argument('--allow-download',action='store_true');p.add_argument('--model-cache');a=p.parse_args(argv)
 verify_freeze();s=make_server(a.port,a.backend,a.allow_download,a.model_cache);url=f'http://127.0.0.1:{s.server_port}'
 print('Team MedVerse Gate33:',url,flush=True)
 print('Commitment contracts are modeled and review-pending. Original clinical path: '+url+'/foundation',flush=True)
 print('Selected retrieval:',a.backend,'; no automatic fallback. No external clinical actions.',flush=True)
 if a.open:
  import webbrowser;webbrowser.open(url)
 try:s.serve_forever()
 except KeyboardInterrupt:pass
 finally:s.server_close()
if __name__=='__main__':main()
