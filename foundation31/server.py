"""Additive local UI using original DT classes and explicit retrieval backends."""
from __future__ import annotations
import argparse,json,mimetypes,secrets,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
from coordination30.server import Handler as BaseHandler,Workbench as BaseWorkbench
from coordination30 import server as old_server
from .session import FoundationSession
from .retrieval import EvidenceService,RetrievalError
from .common import OUT,read,MODEL,REVISION
WEB=Path(__file__).parent/'web'
class Workbench(BaseWorkbench):
    def create(self,body):
        ident=secrets.token_urlsafe(18);token=secrets.token_urlsafe(26)
        engine=FoundationSession(body.get('family_id','C12'),body.get('strategy','MEDVERSE_HARMONIZER'),body.get('mode','PROGRESSIVE'))
        with self.lock:
            if len(self.sessions)>300:self.sessions.pop(next(iter(self.sessions)))
            self.sessions[ident]={'engine':engine,'token':token}
        return {'session_id':ident,'token':token,'snapshot':engine.snapshot()}
class Handler(BaseHandler):
    server_version='MedVerseFoundation/1.0'
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api31/health':
            return self.respond(200,{'release':'Gate31','dt_module':'medverse.digital_twin.model.PatientDigitalTwin',
                'default_retrieval':self.server.default_backend,'model_id':MODEL,'pinned_revision':REVISION,
                'dense_load_status':'NOT_REQUESTED' if self.server.services['dense'].dense.model is None and not self.server.services['dense'].dense._load_error else ('BLOCKED' if self.server.services['dense'].dense._load_error else 'LOADED'),
                'fallback_used':False,'legacy_commitment_behavior':'UNCHANGED','simulated':True})
        if path=='/api31/results':
            runs=sorted(OUT.glob('*/status.json'))
            return self.respond(200,read(runs[-1]) if runs else {'status':'NOT_YET_EVALUATED'})
        if path in {'/','/index.html','/app.js','/style.css','/bridge.js'}:
            p=WEB/('index.html' if path=='/' else path[1:])
            if not p.is_file():return self.respond(404,{'error':'NOT_FOUND'})
            return self.respond(200,p.read_bytes(),(mimetypes.guess_type(p.name)[0] or 'application/octet-stream')+'; charset=utf-8')
        return super().do_GET()
    def do_POST(self):
        path=urlparse(self.path).path
        if path not in {'/api/search','/api31/search'}:return super().do_POST()
        try:
            origin=self.headers.get('Origin');host=self.headers.get('Host','')
            if origin and origin not in {'http://'+host,'https://'+host}:return self.respond(403,{'error':'CROSS_ORIGIN_REJECTED'})
            if 'application/json' not in self.headers.get('Content-Type',''):return self.respond(415,{'error':'JSON_REQUIRED'})
            n=int(self.headers.get('Content-Length','0'))
            if n<2 or n>20000:raise RetrievalError('INVALID_BODY_SIZE')
            b=json.loads(self.rfile.read(n))
            if not isinstance(b,dict) or set(b)-{'query','role','jurisdiction','top_k','backend'}:raise RetrievalError('UNSUPPORTED_INPUT_FIELDS')
            backend=b.get('backend',self.server.default_backend)
            if backend not in self.server.services:raise RetrievalError('UNKNOWN_BACKEND')
            r=self.server.services[backend].search(b.get('query'),b.get('role','privacy_agent'),b.get('top_k',3),b.get('jurisdiction','KR'))
            return self.respond(200,r)
        except (RetrievalError,ValueError,TypeError) as e:return self.respond(400,{'error':str(e)})
        except Exception as e:return self.respond(500,{'error':type(e).__name__,'message':str(e)})

def make_server(port=0,backend='dense',allow_download=False,cache_folder=None):
    # Reuses the inherited endpoints in this *process*, never edits original source files.
    # Run old/new launchers in separate processes/ports, as documented.
    old_server.APP=Workbench()
    s=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    s.default_backend=backend
    s.services={k:EvidenceService(k,local_only=not allow_download,cache_folder=cache_folder) for k in ['dense','bm25']}
    return s

def main(argv=None):
    p=argparse.ArgumentParser(description='Original DT + explicitly selected evidence backend; modeled local sandbox')
    p.add_argument('--port',type=int,default=8765);p.add_argument('--open',action='store_true')
    p.add_argument('--backend',choices=['dense','bm25'],default='dense')
    p.add_argument('--allow-download',action='store_true',help='Explicitly allow pinned public model download when absent')
    p.add_argument('--model-cache');a=p.parse_args(argv)
    s=make_server(a.port,a.backend,a.allow_download,a.model_cache);url=f'http://127.0.0.1:{s.server_port}'
    print('Team MedVerse Gate31:',url,flush=True)
    print('Original project-local DT adapter; backend:',a.backend,'; no automatic fallback; commitment logic unchanged.',flush=True)
    if a.open:
        import webbrowser;webbrowser.open(url)
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:s.server_close()
if __name__=='__main__':main()
