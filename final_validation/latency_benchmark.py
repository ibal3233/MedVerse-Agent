"""Descriptive repeated timing. No selection, warm-up 2; repetitions 30 per family/config."""
from __future__ import annotations
import random,time,statistics
from .common import DATA,OUT,read_json,write_json
from .engine import Session
from .validate import check_freeze,write_csv

def main():
 check_freeze();families=[f for f in read_json(DATA/'workflow_families.json')['families'] if f['split']=='CONFIRMATION'];strategies=['LOCAL_FILTER','STATEFUL_FILTER','MEDVERSE','DENY_ALL'];rows=[];rng=random.Random(27031)
 for rep in range(-2,30):
  jobs=[(f,s) for f in families for s in strategies];rng.shuffle(jobs)
  for f,strategy in jobs:
   session=Session(strategy=strategy)
   for event in f['events']:
    start=time.perf_counter_ns();result=session.advance(event);ms=(time.perf_counter_ns()-start)/1e6
    if rep>=0:rows.append({'family_id':f['family_id'],'strategy':strategy,'repetition':rep,'event_id':event['id'],'full_modeled_event_ms':ms,'coordination_only_ms':result['cycle']['latency_ms']})
 summary=[]
 for strategy in strategies:
  vals=sorted(r['full_modeled_event_ms'] for r in rows if r['strategy']==strategy)
  summary.append({'strategy':strategy,'timed_events':len(vals),'mean_ms':statistics.mean(vals),'stdev_ms':statistics.stdev(vals),'p50_ms':statistics.median(vals),'p95_ms':vals[int(.95*(len(vals)-1))],'p99_ms':vals[int(.99*(len(vals)-1))]})
 write_csv(OUT/'timing/raw_event_timings.csv',rows);write_json(OUT/'timing/summary.json',{'warmups_per_family_configuration':2,'repetitions':30,'family_count':len(families),'ordering_seed':27031,'scope':'Local modeled event intake + coordination + authorization + in-memory audit + snapshot. Excludes LLM, embedding computation, external network, human latency and real hospital operations. Repetitions are not new cases.','summary':summary});print(summary)
if __name__=='__main__':main()
