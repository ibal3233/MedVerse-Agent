"""Serve a read-only presentation gallery alongside the unchanged Gate33 runtime."""
from __future__ import annotations
import argparse, json, mimetypes, webbrowser
from pathlib import Path
from urllib.parse import urlparse
from release33.server import Handler as OriginalHandler, make_server
from release33.common import verify_freeze
ROOT=Path(__file__).resolve().parents[1]
WEB=Path(__file__).parent/'web'
ALLOWED={p.name for p in WEB.iterdir() if p.is_file()}
class PresentationHandler(OriginalHandler):
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/presentation/local_status.json':
            return self.respond(200,{'ncc_csv_present':(ROOT/'data/external/ncc_cancer_incidence.csv').is_file(),
                'dt_module_present':(ROOT/'medverse/digital_twin/model.py').is_file(),
                'ncc_in_live_gate33_runtime':False,'source':'release-file inspection, not patient data'})
        if path in {'/presentation','/presentation/'}:
            return self.respond(200,(WEB/'index.html').read_bytes(),'text/html; charset=utf-8')
        if path.startswith('/presentation/'):
            name=path.removeprefix('/presentation/')
            if name not in ALLOWED:return self.respond(404,{'error':'PRESENTATION_ASSET_NOT_FOUND'})
            p=WEB/name
            return self.respond(200,p.read_bytes(),mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
        return super().do_GET()
def main(argv=None):
    p=argparse.ArgumentParser(description='Original MedVerse sandbox plus read-only DT/data/result explanation gallery')
    p.add_argument('--port',type=int,default=8765)
    p.add_argument('--backend',choices=('dense','bm25'),default='dense')
    p.add_argument('--allow-download',action='store_true')
    p.add_argument('--model-cache')
    p.add_argument('--open',action='store_true')
    a=p.parse_args(argv)
    verify_freeze()
    server=make_server(a.port,a.backend,a.allow_download,a.model_cache)
    server.RequestHandlerClass=PresentationHandler
    url=f'http://127.0.0.1:{server.server_port}'
    print('Original commitment workspace:',url,flush=True)
    print('Original DT workspace:',url+'/foundation',flush=True)
    print('Read-only presentation gallery:',url+'/presentation',flush=True)
    print('Backend:',a.backend,'— no silent fallback; no original experiment modified.',flush=True)
    if a.open:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
