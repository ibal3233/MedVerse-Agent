"""HTTP client shared by validation/replay; not used to inject authority records."""
import json
from urllib.request import Request,urlopen
from urllib.error import HTTPError
class Client:
 def __init__(self,url):self.url=url;self.session=None
 def call(self,path,body=None,token=None,extra_headers=None):
  h={'Content-Type':'application/json'}
  if token is not None:h['X-Session-Token']=token
  if extra_headers:h.update(extra_headers)
  req=Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=h)
  try:
   with urlopen(req,timeout=40) as r:return r.status,json.load(r)
  except HTTPError as e:return e.code,json.load(e)
 def start(self,family='C12',strategy='MEDVERSE_HARMONIZER',mode='PROGRESSIVE'):
  status,v=self.call('/api30/session',{'family_id':family,'strategy':strategy,'mode':mode})
  if status!=200:raise RuntimeError((status,v))
  self.session=v;return v['snapshot']
 def post(self,path,**kw):
  status,v=self.call(path,{'session_id':self.session['session_id'],**kw},self.session['token'])
  if status!=200:raise RuntimeError((path,status,v))
  return v if path=='/api30/export' else v.get('snapshot',v)
