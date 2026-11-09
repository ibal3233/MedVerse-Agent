"""Measured non-bar figures and compact report; saves then displays by default."""
from __future__ import annotations
import csv,json,textwrap
from pathlib import Path
from datetime import datetime,timezone
from .common import load,save,hashfile,STRATEGIES,LABELS

def make_figures(run,show=True,dpi=300):
 from foundation31.runtime_support import configure_plotting,display_figures
 display_info=configure_plotting(show)
 import matplotlib.pyplot as plt
 from matplotlib.backends.backend_pdf import PdfPages
 run=Path(run);status=load(run/'status.json');traces=load(run/'raw_traces.json');refs=load(run/'reference_outcomes.json')
 with (run/'case_metrics.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 confirm=[r for r in rows if r['split']=='CONFIRMATION'];families=sorted({r['family'] for r in confirm});summary=status['summary']
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');dest=run/'figures'/('display_'+stamp);dest.mkdir(parents=True,exist_ok=False)
 figures=[];paths=[]
 # Figure 1: family-wise map, not independent branch counts disguised as sample size.
 fig,ax=plt.subplots(figsize=(9.0,5.9));methods=list(STRATEGIES)+['FULL_INFORMATION_REFERENCE']
 for x,method in enumerate(methods):
  ys=[];ns=[]
  for i,family in enumerate(families):
   r=[r for r in confirm if r['family']==family and r['strategy']=='EAGER'];n=len(r)
   if method=='FULL_INFORMATION_REFERENCE':wins=sum(refs[family+'/'+z['branch']]['complete_within_declared_limits'] for z in r)
   else:wins=sum(z['complete_within_limits']=='True' for z in confirm if z['family']==family and z['strategy']==method)
   ys.append(i);ns.append(wins);ax.text(x+.13,i,f'{wins}/{n}',va='center',fontsize=10)
  ax.scatter([x]*len(ys),ys,s=[45+22*n for n in ns],marker='s' if x==3 else 'o',label=None)
 ax.set_yticks(range(len(families)),[f+': '+next(r['title'] for r in confirm if r['family']==f) for f in families],fontsize=8.5)
 ax.set_xticks(range(4),['Eager\ncommit','Fair\nbounded wait','MedVerse\ncommitment','Full information\n(noncausal bound)'])
 ax.invert_yaxis();ax.set_xlim(-.35,3.65);ax.set_ylim(len(families)-.5,-.5);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
 ax.set_title('Workflow completion within declared event limits',pad=15)
 fig.text(.5,.025,'Eight internally authored prefix families; four correlated continuations per family.\nThe full-information column is an evaluation-only upper bound, not a deployable baseline.',ha='center',fontsize=8.5)
 fig.tight_layout(rect=(0,.09,1,.98));figures.append(('01_Commitment_Outcome_Map',fig))
 # Figure 2: completion / wait cost. Coincident fair results are explicitly grouped.
 fig,ax=plt.subplots(figsize=(8.8,4.9));groups={}
 for s in summary:groups.setdefault((s['mean_proposal_wait_steps'],s['completion_fraction']),[]).append(s)
 for i,((x,y),ss) in enumerate(groups.items()):
  ax.scatter([x],[100*y],s=90,marker=['o','D','s'][i%3])
  name=' / '.join(LABELS[s['strategy']] for s in ss)
  label=f"{name}\n{ss[0]['completed_branches']}/{ss[0]['branch_continuations']} complete"
  ax.annotate(label,(x,100*y),xytext=(12,12 if i%2==0 else -35),textcoords='offset points',fontsize=9)
 ax.set_xlabel('Mean proposal-wait steps per continuation (not clinical waiting time)');ax.set_ylabel('Complete within declared limits (%)')
 ax.set_ylim(0,105);maxx=max(s['mean_proposal_wait_steps'] for s in summary);ax.set_xlim(-.3,max(2,maxx+2.7));ax.grid(alpha=.2);ax.set_axisbelow(True)
 ax.set_title('Completion gains must be read alongside the cost of waiting')
 fig.text(.5,.025,f"Paired gains over eager: {status['paired_completion_gains']}; losses: {status['paired_completion_losses']}. "
          f"Fair/MedVerse ties: {status['fair_bounded_wait_ties']}/{status['comparison_branches']}.\nModel event steps are declared engineering assumptions, not clinical timing recommendations.",ha='center',fontsize=8.7)
 fig.tight_layout(rect=(0,.10,1,.98));figures.append(('02_Completion_Wait_Tradeoff',fig))
 # Figure 3: actual effects and recorded WAITs from one explicitly labelled continuation.
 fig,ax=plt.subplots(figsize=(9,5.7));lanes=[];points={'WAIT':[],'PREPARE':[],'COMMIT':[]}
 for method in STRATEGIES:
  trace=traces['P01/PROMPT/'+method]['snapshot']
  for category in ['Clinical review','Technical containment','Preparation']:
   idx=len(lanes);lanes.append(LABELS[method]+' | '+category)
   for event in trace['events']:
    for d in event['decisions']:
     a=next(a for a in trace['current']['case']['actions'] if a['id']==d['proposal_id'])
     relevant=(category=='Clinical review' and a['kind']=='CLINICAL_REVIEW') or (category=='Technical containment' and a['kind']=='QUARANTINE_STREAM')
     if relevant and d['decision']=='WAIT':points['WAIT'].append((event['event'],idx))
   for r in trace['receipts']:
    if not r['permitted']:continue
    relevant=(category=='Clinical review' and r['actual_proposal']['kind']=='CLINICAL_REVIEW') or (category=='Technical containment' and r['actual_proposal']['kind']=='QUARANTINE_STREAM') or (category=='Preparation' and r['stage']=='PREPARE')
    if relevant:points['PREPARE' if r['stage']=='PREPARE' else 'COMMIT'].append((r['event'],idx))
 for label,marker in [('WAIT','D'),('PREPARE','s'),('COMMIT','o')]:
  if points[label]:xs,ys=zip(*points[label]);ax.scatter(xs,ys,marker=marker,s=65,label=label)
 ax.set_yticks(range(len(lanes)),lanes,fontsize=8);ax.invert_yaxis();ax.set_xticks(range(1,7));ax.set_xlim(.6,6.4)
 ax.set_xlabel('Released event index');ax.set_title('Prompt alternative: preparation is not clinical completion')
 ax.grid(axis='both',alpha=.18);ax.set_axisbelow(True);ax.legend(loc='upper right',fontsize=8)
 fig.text(.5,.02,'Measured P01/PROMPT trace. Markers show actual permitted effects or recorded waits.\nOther branches include late, absent and denied alternatives; the example is not the aggregate result.',ha='center',fontsize=8.5)
 fig.tight_layout(rect=(0,.10,1,.98));figures.append(('03_Commitment_Event_Timeline',fig))
 for name,fig in figures:
  for suffix in ['png','pdf']:
   path=dest/(name+'.'+suffix);fig.savefig(path,dpi=dpi,bbox_inches='tight');paths.append(path)
 # Plain editable table accompanies figures.
 table=['| Controller | Completion | Clinical on time (feasible) | Mean proposal-wait steps | Invalid commits |',
        '|---|---:|---:|---:|---:|']
 for s in summary:table.append(f"| {LABELS[s['strategy']]} | {s['completed_branches']}/{s['branch_continuations']} | {s['clinical_on_time_in_feasible']}/{s['clinical_feasible_branches']} | {s['mean_proposal_wait_steps']:.2f} | {s['invalid_commits']} |")
 table+=['','32 correlated continuation branches from 8 modeled prefix families. No clinical/legal validation. Fair ties and adverse branches retained.']
 (dest/'compact_results_table.md').write_text('\n'.join(table),encoding='utf-8')
 # One concise text page + the three measured figures. No fixed performance claims.
 cover=plt.figure(figsize=(8.27,11.69));cover.text(.075,.94,'TEAM MEDVERSE  |  GATE 32',fontsize=17,weight='bold')
 cover.text(.075,.90,'Bounded commitment under partial information',fontsize=13)
 paragraphs=[
 ('Decision','Timing is evaluated separately from authorization. COMMIT, bounded WAIT and authorized PREPARE use only released information. The unchanged Gate 29 selector and validator are shared by all methods; preparations cannot create care, disclosure or approval.'),
 ('Design',f"4 development prefix families / 8 branches; 8 internal confirmation prefix families / 32 branches. {status['controller_runs']} method runs. One common event-clock model; all branch variants remain grouped. No model training, new legal interpretation, or patient data."),
 ('Results','; '.join(f"{LABELS[s['strategy']]}: {s['completed_branches']}/32 complete, {s['mean_proposal_wait_steps']:.2f} mean proposal-wait steps" for s in summary)+'.'),
 ('Integrity',f"{status['development_checks_passed']}/{status['development_checks_total']} development checks; {status['same_history_checks_passed']}/{status['same_history_checks']} identical-history checks; {status['precommit_no_side_effect']}/{status['precommit_probes']} change-before-commit probes without effects. {status['known_legacy_events_unchanged']}/{status['known_legacy_event_comparisons']} historical event outcomes preserved."),
 ('Interpretation',f"Against eager commitment, MedVerse improves {status['paired_completion_gains']} branches and loses {status['paired_completion_losses']}. It ties the capable bounded-wait control on {status['fair_bounded_wait_ties']}/32 branches. These are engineering results, not proof of unique superiority or optimal behavior under unknown futures."),
 ('Critical boundary','The old C01/C02 cases contain no declared review conditions justifying delay. They remain unchanged. New timing-contract evidence must not be presented as repairing those old cases. Earlier disclosures and commitments are never erased after later revocation.'),
 ('Outstanding work','Qualified clinical/Korean-policy review, fresh independent scenario authorship, and integration of the tested commitment module into the final clinical workspace and video. The original DT/retrieval implementation is preserved; this experiment does not reload or reevaluate dense embeddings.'),
 ('Reproduce','Run medverse/gates/gate32_commitment_control.py. It verifies frozen files, evaluates, saves evidence, exports PNG/PDF figures and this report, and displays the figures. Native Windows/Spyder execution is not independently tested here.')]
 y=.86
 for title,text in paragraphs:
  cover.text(.075,y,title,fontsize=10.5,weight='bold');y-=.023
  lines=textwrap.wrap(text,98);cover.text(.075,y,'\n'.join(lines),fontsize=9.3,va='top',linespacing=1.4);y-=.018*len(lines)+.025
 cover.text(.075,.035,'Source run: '+status['run_id']+'  |  Modeled effects only',fontsize=8)
 report=dest/'Gate32_Commitment_Report.pdf'
 with PdfPages(report) as pdf:
  pdf.savefig(cover)
  for _,fig in figures:pdf.savefig(fig,bbox_inches='tight')
 plt.close(cover);paths.append(report)
 display_result=display_figures([f for _,f in figures],show,display_info)
 save(dest/'presentation_manifest.json',{'run_id':status['run_id'],'source_status_sha256':hashfile(run/'status.json'),
   'outputs':{p.name:hashfile(p) for p in paths},'display':display_result,'no_metrics_changed':True})
 print('Saved three non-bar figures, compact table and four-page report:',dest)
 return dest
