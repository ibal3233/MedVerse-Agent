"""Optional original embedding-backend evaluation; no lexical fallback, no selection.
Run on a machine with the original SentenceTransformer dependency and model available.
"""
from __future__ import annotations
import argparse,time,importlib.util
from .common import DATA,OUT,read_json,write_json
from .knowledge import PolicyCorpus
from .validate import check_freeze,write_csv

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',default='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2');p.add_argument('--local-only',action='store_true');a=p.parse_args();check_freeze()
 dest=OUT/'optional_dense'
 if importlib.util.find_spec('sentence_transformers') is None:
  status={'status':'BLOCKED_DEPENDENCY','model':a.model,'fallback_used':False,'reason':'sentence-transformers is not installed. No original dense retrieval result is claimed.'};write_json(dest/'status.json',status);print(status);return
 try:
  from sentence_transformers import SentenceTransformer
  import numpy as np
  model=SentenceTransformer(a.model,device='cpu',local_files_only=a.local_only);kb=PolicyCorpus();cache={};rows=[]
  for f in read_json(DATA/'query_families.json')['records']:
   role=f['role']
   if role not in cache:
    recs=[r for r in kb.records if kb.eligibility(r,role)=='ELIGIBLE_REFERENCE'];emb=model.encode([kb.text(r) for r in recs],normalize_embeddings=True,convert_to_numpy=True);cache[role]=(recs,emb)
   recs,emb=cache[role]
   for lang in ['en','ko']:
    start=time.perf_counter_ns();q=model.encode([f[lang]],normalize_embeddings=True,convert_to_numpy=True)[0];scores=emb@q;ids=[recs[int(i)]['chunk_id'] for i in np.argsort(-scores)[:3]]
    rows.append({'family_id':f['family_id'],'split':f['split'],'language':lang,'expected':f['expected_any'],'retrieved':ids,'recall_at3_hit':bool(set(ids)&set(f['expected_any'])),'latency_ms':(time.perf_counter_ns()-start)/1e6})
  write_csv(dest/'queries.csv',rows);status={'status':'EXECUTED','model':a.model,'fallback_used':False,'n_queries':len(rows),'selection_performed':False,'confirmation_recall_at3':sum(r['recall_at3_hit'] for r in rows if r['split']=='CONFIRMATION')/sum(r['split']=='CONFIRMATION' for r in rows)}
 except Exception as e:status={'status':'BLOCKED_ENVIRONMENT','model':a.model,'fallback_used':False,'error':repr(e)}
 write_json(dest/'status.json',status);print(status)
if __name__=='__main__':main()
