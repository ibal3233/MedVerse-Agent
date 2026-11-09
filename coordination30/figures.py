"""Presentation only: no changes to measurements or experiment thresholds.

Three single-axis figures, no bar charts, PDF/300-dpi PNG exports and a concise table.
Uses the current Matplotlib backend; the main gate displays by default.
"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import csv,json
from .common import ROOT,load,save,filehash,STRATEGIES,LABELS

def make_figures(run_dir,show=True,dpi=300):
 import matplotlib.pyplot as plt
 from matplotlib.backends.backend_pdf import PdfPages
 from matplotlib.lines import Line2D
 run_dir=Path(run_dir);status=load(run_dir/'status.json');sr=load(run_dir/'snapshot_metrics.json');pr=load(run_dir/'progressive_metrics.json');fr=load(run_dir/'family_final_outcomes.json');lat=load(run_dir/'latency_samples.json')
 destination=run_dir/'figures'/('display_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));destination.mkdir(parents=True)
 rows=[r for r in sr if r['prior_split']=='CONFIRMATION'];families=list(dict.fromkeys(r['family_id'] for r in rows))
 names={'D02':'Containment / acknowledgement','D03':'Denied request / restricted view','C01':'Session isolation / late care route','C02':'Containment choice / late route','C03':'No authorized clinical route','C04':'Pending handoff authority','C05':'Joint disclosure restriction','C06':'Revoked original authority','C07':'Task-adequate alternative','C08':'Missing research evidence','C09':'Stale DT / fresh alternative','C10':'Policy binding / oversight','C11':'Recipient mismatch','C12':'Cross-institution flagship'}
 short=['Requested\npath only','Fair stateful\nselector','Independent\nplanner','MedVerse\nharmonizer']
 figures=[]
 # Paired glyph matrix: each cell contains full-information snapshot then progressive final.
 fig,ax=plt.subplots(figsize=(10,6.5))
 groups={k:[] for k in ('complete','partial','miss','late')}
 for y,fid in enumerate(families):
  for x,strategy in enumerate(STRATEGIES):
   a=next(r for r in rows if r['family_id']==fid and r['strategy']==strategy)
   b=next(r for r in fr if r['family_id']==fid and r['strategy']==strategy)
   for offset,is_complete,is_snapshot in [(-.13,a['complete'],True),(.13,b['final_complete'],False)]:
    if is_complete:kind='complete'
    elif not a['reference_feasible']:kind='partial'
    elif not is_snapshot and strategy!='REQUEST_ONLY':kind='late'
    else:kind='miss'
    groups[kind].append((x+offset,y))
 markers={'complete':'o','partial':'s','miss':'x','late':'^'}
 legends={'complete':'Complete workflow','partial':'Partial / held: no complete snapshot solution','miss':'Available full workflow not completed','late':'Later alternative blocked by earlier commitment'}
 for kind,points in groups.items():
  if points:ax.scatter([p[0] for p in points],[p[1] for p in points],s=48,marker=markers[kind],label=legends[kind])
 ax.set_yticks(range(len(families)),[f'{f}  {names[f]}' for f in families],fontsize=9)
 ax.set_xticks(range(4),short,fontsize=10);ax.set_xlim(-.55,3.55);ax.set_ylim(len(families)-.5,-.75)
 ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.tick_params(axis='y',length=0)
 ax.set_title('Snapshot correctness survives integration; late alternatives remain a challenge',fontsize=13,pad=20)
 ax.text(.5,1.015,'Within each pair: snapshot (left)  →  progressive final state (right)',transform=ax.transAxes,ha='center',fontsize=9)
 ax.legend(loc='upper center',bbox_to_anchor=(.42,-.16),ncol=2,frameon=False,fontsize=8.2,columnspacing=1.5)
 fig.text(.5,.014,'14 known families; 10 have a complete snapshot solution. Capable methods tie.\nC01/C02 expose irreversible online choices; retained failures, not retuned cases.',ha='center',fontsize=9)
 fig.subplots_adjust(left=.32,right=.985,top=.87,bottom=.25)
 figures.append(('01_Paired_Workflow_Outcome_Map',fig))
 # Actual event-to-effect timeline, no invented action timestamps.
 records=[r for r in pr if r['family_id']=='C12' and r['strategy']=='MEDVERSE_HARMONIZER']
 obligations=[('clinical_review_done','Clinical review'),('stream_isolated','Affected stream isolated'),('handoff_ack','Clinical handoff acknowledged'),('dt_received','DT context received'),('limited_privacy_ok','Privacy attestation committed'),('limited_basis_ok','Research attestation committed'),('research_done','Restricted research view released')]
 fig,ax=plt.subplots(figsize=(9.5,4.8))
 for i,(token,label) in enumerate(obligations):
  got=[r['event'] for r in records if token in r['achieved_tokens']]
  if got:
   ax.plot(got,[i]*len(got),marker='o',linewidth=2,markersize=6)
   ax.annotate(f'E{got[0]}', (got[0],i),xytext=(-14,9),textcoords='offset points',fontsize=9)
 ax.set_yticks(range(len(obligations)),[x[1] for x in obligations],fontsize=10);ax.set_ylim(len(obligations)-.5,-.7)
 ax.set_xticks(range(1,7),['E1\nConcern','E2\nClinical–cyber\ncontracts','E3\nOriginal\nresearch request','E4\nDT transfer','E5\nAlternative /\nprivacy review','E6\nResearch\nauthority'],fontsize=9)
 ax.set_xlim(.8,6.25);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
 ax.set_title('Clinical work proceeds before research disclosure is authorized',fontsize=13,pad=16)
 fig.text(.5,.015,'C12 actual HTTP trace: clinical review commits at event 2; the restricted research view at event 6.\nDots represent achieved modeled effects, not diagnoses or real clinical actions.',ha='center',fontsize=9)
 fig.subplots_adjust(left=.30,right=.97,top=.87,bottom=.24)
 figures.append(('02_Progressive_Commitment_Timeline',fig))
 # Observed latency distribution, not an artificially smooth model or comparative speed claim.
 fig,ax=plt.subplots(figsize=(8.7,4.8))
 for strategy,line in zip(STRATEGIES,[':','--','-.','-']):
  values=sorted(r['http_latency_ms'] for r in lat if r['strategy']==strategy)
  ax.step(values,[(i+1)/len(values) for i in range(len(values))],where='post',linestyle=line,label=LABELS[strategy],linewidth=1.8)
 ax.set_xlabel('Loopback HTTP event response (ms)');ax.set_ylabel('Empirical cumulative fraction');ax.set_ylim(0,1.03);ax.set_xlim(left=0)
 ax.set_title('Observed response-time distribution—not an equal-utility speed ranking',fontsize=12,pad=14)
 ax.legend(loc='lower right',fontsize=9,frameon=False);ax.grid(alpha=.18)
 fig.text(.5,.015,'60 event calls per configuration; 10 C12 replays, warmup excluded, randomized configuration order.\nIncludes JSON and loopback HTTP; excludes external network, model inference and human response.',ha='center',fontsize=8.7)
 fig.subplots_adjust(left=.11,right=.97,top=.88,bottom=.24)
 figures.append(('03_HTTP_Response_ECDF',fig))
 paths=[]
 with PdfPages(destination/'Gate30_Results_Figures.pdf') as pdf:
  for name,figure in figures:
   for extension in ('png','pdf'):
    path=destination/(name+'.'+extension);figure.savefig(path,dpi=dpi,bbox_inches='tight');paths.append(path)
   pdf.savefig(figure,bbox_inches='tight')
 table=[]
 for row in status['summary']:
  table.append({'Configuration':LABELS[row['strategy']], 'Snapshot feasible complete':f"{row['snapshot_feasible_completed']}/{row['snapshot_feasible_families']}", 'Progressive final complete (same 10)':f"{row['progressive_complete_final_families']}/{row['snapshot_feasible_families']}", 'Per-step reference agreement':f"{row['progressive_reference_matches']}/{row['progressive_steps']}", 'Invalid new commits':row['invalid_commits'], 'HTTP median ms':round(row['timing']['p50_ms'],2), 'HTTP p95 ms':round(row['timing']['p95_ms'],2)})
 save(run_dir/'concise_results.json',table)
 with (destination/'Concise_Performance_Table.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
 md='# Gate 30 - compact performance table\n\n'+ '| '+' | '.join(table[0])+' |\n'+'|'+'|'.join(['---']*len(table[0]))+'|\n'
 for r in table:md+='| '+' | '.join(map(str,r.values()))+' |\n'
 md+='\nFourteen known families, ten snapshot-feasible. Progressive completion is 8/10 for all capable methods. Four families are appropriately partial/held; C01/C02 additionally lose complete solutions after irreversible earlier commitments. Per-step agreement is conditional on the committed prefix, not globally optimal foresight. No independent clinical/legal validity or strict algorithmic superiority is established.\n'
 (destination/'Concise_Performance_Table.md').write_text(md,encoding='utf-8')
 inputs=['status.json','snapshot_metrics.json','progressive_metrics.json','family_final_outcomes.json','latency_samples.json']
 if not (run_dir/'status_measurements.json').exists():(run_dir/'status_measurements.json').write_bytes((run_dir/'status.json').read_bytes())
 manifest={'source_run':run_dir.name,'inputs':{n:filehash(run_dir/n) for n in inputs},'outputs':{p.name:filehash(p) for p in paths},'presentation_only':True,'new_measurements':False}
 save(destination/'presentation_manifest.json',manifest)
 status['presentation_files']=[str(p.relative_to(run_dir)) for p in paths]
 if (run_dir/'browser_validation.json').exists():status['browser_status']=load(run_dir/'browser_validation.json')['status']
 save(run_dir/'status.json',status)
 print('Saved 3 non-bar figures, PNG/PDF, and compact table:',destination)
 if show:plt.show()
 else:
  for _,f in figures:plt.close(f)
 return destination
