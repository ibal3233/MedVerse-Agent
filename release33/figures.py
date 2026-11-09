"""Presentation of measured integration results. No scientific thresholds are changed."""
from datetime import datetime,timezone
import csv, json
from pathlib import Path
from .common import read,save,ROLE_NAMES

def make_figures(run,show=True,dpi=300):
 from foundation31.runtime_support import configure_plotting,display_figures
 info=configure_plotting(show)
 import matplotlib.pyplot as plt
 from matplotlib.backends.backend_pdf import PdfPages
 import numpy as np
 run=Path(run);s=read(run/'status.json');exports=read(run/'http_exports.json')
 dest=run/'figures'/('display_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));dest.mkdir(parents=True)
 figures=[]
 # The same live mechanism can preserve an alternative or lose a valid earlier opportunity.
 fig,ax=plt.subplots(figsize=(10,5.4))
 targets=[('P01/PROMPT/EAGER','Prompt alternative / eager'),('P01/PROMPT/MEDVERSE_COMMITMENT','Prompt alternative / MedVerse'),
          ('P04/NO_REPLACEMENT/EAGER','Later revocation / eager'),('P04/NO_REPLACEMENT/MEDVERSE_COMMITMENT','Later revocation / MedVerse')]
 points={'WAIT':([],[]),'COMMIT':([],[]),'BLOCK / ESCALATE':([],[])}
 for row,(key,label) in enumerate(targets):
  tr=exports[key]['runtime_trace']['snapshot'];actions=tr['current']['case']['actions']
  # Specific primary obligation, not preparations or coincident ancillary actions.
  ids={a['id'] for a in actions if (a['kind']=='CLINICAL_REVIEW' if key.startswith('P01') else a['kind']=='RESEARCH_VIEW')}
  achieved_event=min((r['event'] for r in tr['receipts'] if r['permitted'] and r['stage']=='COMMIT' and r['proposal_id'] in ids), default=10**9)
  for e in tr['events']:
   if e['event']>achieved_event:continue  # Omit reconsideration of unused alternatives after this obligation is met.
   for d in e['decisions']:
    if d['proposal_id'] not in ids:continue
    kind='WAIT' if d['decision']=='WAIT' else ('BLOCK / ESCALATE' if d['decision'] in ('BLOCK','ESCALATE') else None)
    if kind:points[kind][0].append(e['event']);points[kind][1].append(row)
  for r in tr['receipts']:
   if r['permitted'] and r['stage']=='COMMIT' and r['proposal_id'] in ids:points['COMMIT'][0].append(r['event']);points['COMMIT'][1].append(row)
 for kind,marker in [('WAIT','D'),('COMMIT','o'),('BLOCK / ESCALATE','x')]:
  ax.scatter(*points[kind],marker=marker,s=85,label=kind,zorder=3)
 ax.set_yticks(range(4),[l for _,l in targets]);ax.invert_yaxis();ax.set_xticks(range(1,7));ax.set_xlim(.6,6.4);ax.set_xlabel('Released model event (not clinical time)')
 ax.set_title('Commitment timing: preserve an alternative or lose an earlier opportunity',pad=14);ax.grid(alpha=.2);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.18),ncol=3,frameon=False)
 fig.text(.5,.015,'P01 tracks clinical review; P04 tracks research release. Each lane stops once its obligation is achieved.\nCOMMIT markers are actual HTTP receipts, not proposals. All unselected-proposal traces remain in the raw export.',ha='center',fontsize=9)
 fig.tight_layout(rect=(0,.13,1,1));figures.append(('01_Commitment_Tradeoff_Timeline',fig))
 # No faux accuracy: show observed counts and inactive opportunities explicitly.
 fig,ax=plt.subplots(figsize=(10,4.8))
 keys=[('proposal_event_opportunities','Decision\nopportunities'),('WAIT','WAIT\ndecisions'),('prepared','PREPARE\neffects'),('committed','COMMIT\neffects'),('BLOCK_or_ESCALATE','BLOCK /\nESCALATE decisions')]
 rows=s['role_summary']
 for j,(key,label) in enumerate(keys):
  values=[r[key] for r in rows]
  ax.scatter([j]*len(rows),range(len(rows)),s=[35+v*1.7 for v in values],alpha=.5,marker='o')
  for i,v in enumerate(values):ax.annotate(str(v),(j,i),xytext=(14,0),textcoords='offset points',ha='left',va='center',fontsize=11)
 ax.set_xticks(range(len(keys)),[v for _,v in keys]);ax.set_yticks(range(len(rows)),[ROLE_NAMES[r['role']] for r in rows]);ax.invert_yaxis();ax.set_xlim(-.4,4.8);ax.set_title('Institutional contributions in the measured progressive workflows',pad=18);ax.grid(axis='y',alpha=.2)
 fig.text(.5,.015,'MedVerse commitment: 32 known continuations across 8 prefix families. Reconsideration is counted per event.\nCounts are correlated opportunities/effects; a large count is not stronger coverage or better performance.',ha='center',fontsize=9)
 fig.tight_layout(rect=(0,.11,1,1));figures.append(('02_Institutional_Evidence_Matrix',fig))
 # Timings remain local descriptive instrumentation, not a utility-normalized speed contest.
 with (run/'event_comparisons.csv').open(encoding='utf-8-sig') as f:events=list(csv.DictReader(f))
 fig,ax=plt.subplots(figsize=(8.8,4.8))
 for name,label,style in [('EAGER','Eager commitment','-'),('FAIR_BOUNDED_WAIT','Fair bounded wait','--'),('MEDVERSE_COMMITMENT','MedVerse commitment',':')]:
  values=sorted(float(r['http_ms']) for r in events if r['strategy']==name)
  ax.step(values,np.arange(1,len(values)+1)/len(values),where='post',label=label,linestyle=style)
 ax.set_ylim(0,1.02);ax.set_xscale('log');ax.set_xlabel('Loopback HTTP event response (ms, logarithmic axis)');ax.set_ylabel('Empirical cumulative fraction');ax.set_title('Measured operator-response distribution');ax.grid(alpha=.2);ax.legend(frameon=False)
 fig.text(.5,.015,'240 event calls per controller; one known-case replay, without randomized repetition.\nIncludes serialization and UI projection; excludes external network, LLM and human latency. No speed-superiority claim.',ha='center',fontsize=9)
 fig.tight_layout(rect=(0,.13,1,1));figures.append(('03_HTTP_Response_ECDF',fig))
 for name,fig in figures:fig.savefig(dest/(name+'.png'),dpi=dpi,bbox_inches='tight');fig.savefig(dest/(name+'.pdf'),bbox_inches='tight')
 compact=[]
 for r in s['strategy_summary']:
  compact.append({'controller':r['strategy'],'complete_within_model_limits':f"{r['completed_branches']}/32",'clinical_on_time_when_feasible':f"{r['clinical_on_time_in_feasible']}/30",'proposal_wait_steps':r['total_proposal_wait_steps'],'invalid_new_commits':r['invalid_commits']})
 with (dest/'compact_results.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,compact[0].keys());w.writeheader();w.writerows(compact)
 text='| Controller | Complete / 32 | Clinical / 30 | Wait steps | Invalid commits |\n|---|---:|---:|---:|---:|\n'
 for r in compact:text+='| '+' | '.join(str(v) for v in r.values())+' |\n'
 (dest/'compact_results.md').write_text(text,encoding='utf-8')
 # A portable concise report requires only Matplotlib, like the preceding gates.
 with PdfPages(dest/'Gate33_Concise_Integration_Report.pdf') as pdf:
  page=plt.figure(figsize=(8.27,11.69));axp=page.add_axes([.08,.07,.84,.86]);axp.axis('off')
  axp.text(0,1,'TEAM MEDVERSE  /  GATE 33',fontsize=11,fontweight='bold')
  axp.text(0,.95,'Commitment workspace integration',fontsize=21,fontweight='bold')
  axp.text(0,.91,'Experimental timing is visible, inspectable and causally replayed.',fontsize=10)
  axp.text(0,.855,f"Integrity: {s['engineering_integrity']}  |  {s['identical_events']}/{s['event_comparisons']} identical event states  |  {s['identical_traces']}/{s['trace_comparisons']} identical traces",fontsize=11,fontweight='bold')
  table=axp.table(cellText=[[r['controller'].replace('_',' ').title(),r['complete_within_model_limits'],r['clinical_on_time_when_feasible'],r['proposal_wait_steps'],r['invalid_new_commits']] for r in compact],colLabels=['Controller','Complete','Clinical','Wait steps','Invalid'],cellLoc='left',colLoc='left',colWidths=[.44,.15,.15,.15,.11],bbox=[0,.63,1,.16])
  table.auto_set_font_size(False);table.set_fontsize(8.5)
  axp.text(0,.60,'Known Gate 32 cases; 32 correlated confirmation-history continuations, not clinical patients.',fontsize=8)
  y=.55
  chunks=[('What changed','An operator interface now releases one event, exposes the actual timing disposition,\nshows each institution\'s contracts, and exports proposal-to-effect receipts.\nThe unchanged original clinical / Digital Twin application remains separately accessible.'),
   ('What did not change','No controller, selector, deadline, observation, reference outcome or policy was retuned.\nFour gains and three losses versus eager commitment remain. The capable timing\ncontrol still ties. C01/C02 were not retrospectively repaired.'),
   ('Measured integration',f"{s['checks_passed']}/{s['checks_total']} wrapper checks; {s['same_history_passed']}/{s['same_history_checks']} same-history comparisons;\n{s['change_no_side_effect']}/{s['change_before_commit_probes']} precommit-change probes without new effects;\n{s['original_clinical_events_unchanged']}/{s['original_clinical_event_checks']} original clinical event outcomes preserved."),
   ('Evidence boundaries','Modeled contracts and authority only. Clinical/legal review is pending. Role projections\nare operator views, not evidence of authenticated remote peer isolation. This is known-\ninput integration regression, not new confirmation or clinical deployment validation.')]
  for title,body in chunks:
   axp.text(0,y,title,fontsize=11,fontweight='bold');axp.text(0,y-.032,body,fontsize=9,va='top',linespacing=1.5);y-=.127
  axp.text(0,-.005,'Run '+s['run_id']+'  |  Raw CSV/JSON and unchanged predecessor hashes accompany this report.',fontsize=7)
  pdf.savefig(page);plt.close(page)
  for _,fig in figures:pdf.savefig(fig,bbox_inches='tight')
 display=display_figures([f for _,f in figures],show,info);save(dest/'presentation_manifest.json',{'source_run':s['run_id'],'display':display,'scientific_results_changed':False,'files':[p.name for p in dest.iterdir() if p.is_file()]})
 print('Saved 3 non-bar figures, concise PDF and editable table:',dest)
 return dest
