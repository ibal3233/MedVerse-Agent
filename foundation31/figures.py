"""Measured non-bar outputs; no fabricated dense performance or aggregate trust score."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
import csv,json,textwrap
from .common import read,write,digest
from .runtime_support import configure_plotting,display_figures,next_dependency

def _csv(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def make_figures(run_dir,show=True,dpi=300):
    display_info=configure_plotting(show)
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    r=Path(run_dir);s=read(r/'status.json')
    out=r/'figures'/('display_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    out.mkdir(parents=True,exist_ok=False);figures=[];paths=[]
    def save(fig,name):
        for ext in ['png','pdf']:
            p=out/(name+'.'+ext);fig.savefig(p,dpi=dpi,bbox_inches='tight');paths.append(str(p.relative_to(r)))
        figures.append(fig)
    rows=_csv(r/'dt_fixture_trajectory.csv')
    fig,ax=plt.subplots(figsize=(9.1,4.9))
    t=[float(x['modeled_seconds']) for x in rows]
    ax.plot(t,[float(x['native_freshness']) for x in rows],marker='o',linestyle='--',label='Native latest-observation diagnostic')
    ax.plot(t,[float(x['observed_core_freshness']) for x in rows],marker='s',label='Oldest required observed-field freshness')
    ax.annotate('New consent metadata\n(no new telemetry)',xy=(300,1),xytext=(165,.78),arrowprops={'arrowstyle':'->'},fontsize=9)
    ax.set(xlabel='Declared model time (seconds; not a clinical deadline)',ylabel='Freshness diagnostic',ylim=(0,1.13),
           title='An unrelated update must not make old telemetry appear fresh')
    ax.legend(loc='lower left',fontsize=9);ax.grid(axis='y',alpha=.2)
    fig.text(.5,.015,'Explicit S1 development fixture. Native rules unchanged; adapter tracks per-field provenance.\nNo real patient observations, diagnosis, or action permission is established.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.1,1,1));save(fig,'01_DT_Observation_Freshness')
    for backend in ['bm25','dense']:
        p=r/f'{backend}_query_metrics.csv'
        if not p.exists():continue
        rows=[x for x in _csv(p) if x['previous_split']=='CONFIRMATION']
        fams=sorted({x['family_id'] for x in rows});lut={(x['family_id'],x['language']):x for x in rows}
        fig,ax=plt.subplots(figsize=(9,6.3))
        for i,f in enumerate(fams):
            en=float(lut[(f,'en')]['rank_at3'] or 4);ko=float(lut[(f,'ko')]['rank_at3'] or 4)
            ax.plot([en,ko],[i+.12,i-.12],linewidth=1,alpha=.6)
        ax.scatter([float(lut[(f,'en')]['rank_at3'] or 4) for f in fams],[i+.12 for i in range(len(fams))],marker='o',s=45,label='English')
        ax.scatter([float(lut[(f,'ko')]['rank_at3'] or 4) for f in fams],[i-.12 for i in range(len(fams))],marker='D',s=36,label='Korean')
        ax.set_yticks(range(len(fams)),fams);ax.invert_yaxis();ax.set_xticks([1,2,3,4],['1','2','3','Not in top 3'])
        ax.set_xlim(.65,4.3);ax.grid(axis='x',alpha=.2);ax.legend(loc='upper center',bbox_to_anchor=(.5,1.085),ncol=2,fontsize=9)
        ax.set_xlabel('Rank of the frozen target source (lower is better)')
        ax.set_title('Paired Korean / English target-source retrieval · '+('BM25 lexical' if backend=='bm25' else 'Pinned multilingual MiniLM'),pad=38)
        fig.text(.5,.012,'20 previously evaluated intent families, paired across languages; this is regression, not fresh confirmation.\nEqual aggregate Recall@3 need not imply identical per-query success. Target labels were not revised.',ha='center',fontsize=9)
        fig.tight_layout(rect=(0,.09,1,1));save(fig,'02_Paired_Language_Ranks_'+backend)
    cov=s['role_evidence_coverage'];labels=['Hospital','Cyber / Network','Privacy','Research / IRB','Regulator']
    fig,ax=plt.subplots(figsize=(9,4.6))
    for i,row in enumerate(cov):
        ax.plot([row['eligible_for_role'],row['corpus_records']],[i,i],linestyle=':',alpha=.5)
        ax.annotate(str(row['eligible_for_role']),(row['eligible_for_role'],i),xytext=(0,9),textcoords='offset points',ha='center')
    ax.scatter([x['corpus_records'] for x in cov],range(len(cov)),marker='o',label='Candidate corpus records')
    ax.scatter([x['eligible_for_role'] for x in cov],range(len(cov)),marker='D',label='Eligible for this role / snapshot')
    ax.set_yticks(range(len(cov)),labels);ax.invert_yaxis();ax.set_xlim(0,48);ax.set_xlabel('Curated records (shared records can serve multiple roles)')
    ax.set_ylim(len(cov)-.4,-.6);ax.set_title('Institutional evidence scope before ranking',pad=38);ax.grid(axis='x',alpha=.2);ax.legend(loc='upper center',bbox_to_anchor=(.5,1.12),ncol=2,fontsize=8)
    fig.text(.5,.015,'Counts measure configured retrieval scope, not completeness of Korean law or agent accuracy.\nPolicy applicability and executable interpretations still require review.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.12,1,1));save(fig,'03_Role_Evidence_Scope')
    summary=plt.figure(figsize=(8.27,11.69));summary.text(.09,.94,'TEAM MEDVERSE',fontsize=12,weight='bold')
    summary.text(.09,.895,'Gate 31 | DT and evidence bridge',fontsize=20,weight='bold')
    summary.text(.09,.86,'Measured integration checkpoint · '+s['run_id'],fontsize=10)
    reg=s['integration_regression'];bm=s['retrieval']['bm25'];dr=s['retrieval']['dense']
    lines=[
        ('What changed','The original PatientDigitalTwin class is connected through an observation-aware, per-session adapter. Source-filtered retrieval has explicit dense and lexical modes, with exact-ID lookup and source-linked evidence.'),
        ('Engineering results',f"Checks: {s['checks_passed']}/{s['checks_total']}. HTTP checks: {s['http_checks_passed']}/{s['http_checks_total']}. Identical workflow outcomes: {reg['unchanged_event_outcomes']}/{reg['event_comparisons']}. Original files unchanged: {s['original_files_unchanged']}."),
        ('Dense backend status',dr['status']+'. '+('No semantic retrieval accuracy is claimed. No silent BM25 fallback.' if not dr['performance_measured'] else 'Pinned model actually executed; inspect separate raw query results.')),
        ('What the DT test establishes','Demonstration defaults are not observed data. New consent metadata cannot freshen older telemetry. Receiving-envelope metadata is not converted into unprovided patient measurements.'),
        ('Language measurements','Known Korean/English question pairs are replayed with their original target labels. The diagrams show per-question ranks, not only aggregate recall. Corpus source dates are recorded metadata, not newly verified legal applicability.'),
        ('What has NOT changed','Gate 30 action selection and commitment are preserved. The two C01/C02 progressive failures and capable-method ties remain. This checkpoint does not implement commit-versus-wait control or trained-agent inference.'),
        ('Next dependency',next_dependency(dr)),
        ('Claim boundary','Local modeled engineering evidence. No clinical deployment, independent legal review, real authorization, general multilingual capability, or ITU conformance is established.')]
    y=.81
    for title,body in lines:
        summary.text(.09,y,title,fontsize=12,weight='bold');y-=.026
        wrapped=textwrap.wrap(body,88)
        summary.text(.09,y,'\n'.join(wrapped),fontsize=9.5,va='top',linespacing=1.4)
        y-=.0185*len(wrapped)+.024
    report=out/'Gate31_Foundation_Report.pdf'
    with PdfPages(report) as pdf:
        pdf.savefig(summary)
        for fig in figures:pdf.savefig(fig,bbox_inches='tight')
    paths.append(str(report.relative_to(r)))
    compact=[{'measure':'Engineering checks','result':f"{s['checks_passed']}/{s['checks_total']}"},
             {'measure':'Known event outcomes unchanged','result':f"{reg['unchanged_event_outcomes']}/{reg['event_comparisons']}"},
             {'measure':'Dense backend','result':dr['status']},
             {'measure':'Commitment timing repair','result':'NOT_IN_THIS_RELEASE'}]
    for b,v in s['retrieval'].items():
        for row in v.get('summary',[]):
            if row['historical_split']=='CONFIRMATION':compact.append({'measure':f'{b} {row["language"]} target Recall@3','result':f'{row["recall3_n"]}/{row["n"]}'})
    from .evaluate import csv_write
    csv_write(out/'compact_results.csv',compact)
    (out/'compact_results.md').write_text('| Measure | Result |\n|---|---|\n'+'\n'.join(f'| {x["measure"]} | {x["result"]} |' for x in compact),encoding='utf-8')
    print('Saved measured non-bar figures, PDF report and compact table:',out)
    plt.close(summary)
    display_info=display_figures(figures,show,display_info)
    write(out/'presentation_manifest.json',{'source_run':s['run_id'],'status_sha256':digest(s),'files':paths,'dense_status':dr['status'],'data_changed':False,'display':display_info,'compatibility_patch':'1.0.1'})
    print('Plot display:',display_info['display_status'],'| Backend:',display_info['backend_after'])
    return out
