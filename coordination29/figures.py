"""Run-local PNG/PDF exports and direct display without forcing a backend."""
from __future__ import annotations
import csv
from datetime import datetime,timezone
from pathlib import Path
from .common import ROOT, OUT, STRATEGIES, LABELS, load, save, filehash


def require_matplotlib():
    try:
        import matplotlib.pyplot
    except ImportError as exc:
        raise RuntimeError('Matplotlib is required for automatic figures. Install it in your experiment environment, or use --no-plots explicitly.') from exc


def resolve_run(run=None):
    if run is None:
        matches=sorted(p.parent for p in OUT.glob('*/status.json'))
        if not matches:raise FileNotFoundError('No saved Gate 29 run.')
        return matches[-1]
    p=Path(run)
    if p.name=='status.json':p=p.parent
    if not p.is_absolute():p=OUT/p
    if not (p/'status.json').is_file():raise FileNotFoundError(p/'status.json')
    return p


def make_figures(run=None,show=True,dpi=300):
    require_matplotlib()
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from textwrap import wrap
    run=resolve_run(run);status=load(run/'status.json')
    if status['confirmation_families']==0:
        print('Development-only results: confirmation plots are not applicable.');return None
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    dest=run/'figures'/('display_'+stamp);dest.mkdir(parents=True,exist_ok=False)
    plots=[]
    summaries=status['confirmation_summary'];x=list(range(len(summaries)))
    fig,ax=plt.subplots(figsize=(9.2,5.3))
    bars=ax.bar(x,[100*(r['feasible_workflow_recall'] or 0) for r in summaries],width=.6)
    ax.bar_label(bars,labels=[f"{r['completed_feasible']}/{r['reference_feasible_families']}" for r in summaries],padding=5)
    ax.set_xticks(x,[LABELS[r['strategy']] for r in summaries]);ax.set_ylim(0,115)
    ax.set_ylabel('Reference-feasible workflows completed (%)')
    ax.set_title('Gate 29: choosing an authorized workflow')
    ax.grid(axis='y',alpha=.22);ax.set_axisbelow(True)
    fig.text(.5,.02,'Fourteen internally authored confirmation families. Requested-path-only is a scope control.\nCapable selectors retain ties. Reference outcomes do not establish clinical/legal validity.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.10,1,1));plots.append(('01_Feasible_Workflow_Recall',fig))
    fig,ax=plt.subplots(figsize=(9.2,5.3))
    width=.34
    for off,key,label in [(-width/2,'optimal_partial_or_complete','Reference-optimal complete or partial plan'),
                          (width/2,'disposition_correct','Correct evidence/authority disposition')]:
        b=ax.bar([i+off for i in x],[r[key] for r in summaries],width,label=label)
        ax.bar_label(b,padding=4,fontsize=9)
    ax.set_xticks(x,[LABELS[r['strategy']] for r in summaries]);ax.set_ylim(0,max(r['confirmation_families'] for r in summaries)+3)
    ax.set_ylabel('Confirmation families');ax.set_title('Useful partial plans and uncertainty handling')
    ax.legend(loc='upper left',fontsize=8);ax.grid(axis='y',alpha=.22);ax.set_axisbelow(True)
    fig.text(.5,.02,'Objective: preserve feasible clinical review, satisfy joint obligations, then minimize disclosure and steps.\nClinical and technical obligations can remain satisfied while research access is held.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.10,1,1));plots.append(('02_Reference_Outcome_Agreement',fig))
    with (run/'workspace_adapter_tests.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    grouped=[]
    for name in ('DIRECT_JSON','MAPPED_KEYS'):
        rr=[r for r in rows if r['adapter']==name];pos=[r for r in rr if r['variant']=='complete'];neg=[r for r in rr if r['variant']!='complete']
        grouped.append((name,sum(r['accepted']=='True' for r in pos),len(pos),sum(r['accepted']=='False' for r in neg),len(neg)))
    fig,ax=plt.subplots(figsize=(8.8,5.2))
    for off,nums,denoms,label in [(-.18,[g[1] for g in grouped],[g[2] for g in grouped],'Valid exchanges accepted'),
                                 (.18,[g[3] for g in grouped],[g[4] for g in grouped],'Invalid context rejected')]:
        values=[100*n/d if d else 0 for n,d in zip(nums,denoms)]
        bars=ax.bar([i+off for i in range(2)],values,.34,label=label)
        ax.bar_label(bars,labels=[f'{n}/{d}' for n,d in zip(nums,denoms)],padding=5)
    ax.set_xticks([0,1],['Direct JSON adapter','Mapped-key adapter']);ax.set_ylim(0,135)
    ax.set_ylabel('Correct receiving-side decisions (%)');ax.set_title('Policy-context handoff tests')
    ax.legend(loc='upper left',fontsize=9);ax.grid(axis='y',alpha=.22);ax.set_axisbelow(True)
    fig.text(.5,.02,'One omitted or changed context field at a time; correlated probes, not additional patients.\nTwo local adapters are not a full ITU conformance test or authenticated remote integration.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.10,1,1));plots.append(('03_Workspace_Context_Handoffs',fig))
    outputs=[]
    for name,fig in plots:
        fig.savefig(dest/(name+'.png'),dpi=dpi,bbox_inches='tight')
        fig.savefig(dest/(name+'.pdf'),bbox_inches='tight')
        outputs += [name+'.png',name+'.pdf']
    # Programmatic report uses the same installed matplotlib dependency, not a browser.
    report=dest/'Gate29_Workflow_Choice_Report.pdf'
    def text_page(pdf,title,sections):
        page=plt.figure(figsize=(8.27,11.69));page.text(.09,.94,'TEAM MEDVERSE | GATE 29',fontsize=11,weight='bold')
        page.text(.09,.895,title,fontsize=17,weight='bold');y=.84
        for heading,body in sections:
            page.text(.09,y,heading,fontsize=12,weight='bold');y-=.027
            for line in wrap(body,width=90):
                page.text(.09,y,line,fontsize=10);y-=.019
            y-=.025
        page.text(.09,.04,'Run: '+status['run_id']+' | modeled scenarios; no clinical/legal deployment validation',fontsize=8)
        pdf.savefig(page);plt.close(page)
    with PdfPages(report) as pdf:
        text_page(pdf,'Workflow choice: experiment and limits',[
            ('Terminology','Reference outcomes are the acceptable complete or partial workflows under the frozen modeling specification. The independent reference evaluator checks them by exhaustive subset enumeration. It is separately implemented from the methods under test, but authored by the same developer; no external expert endorsement is implied.'),
            ('Design',f"{status['development_families']} development and {status['confirmation_families']} internal confirmation families; {status['strategy_executions']} method executions. Whole matching dependency skeletons were grouped before comparative evaluation. Policy and action primitives remain shared."),
            ('Question','Can institution-owned alternative actions satisfy clinical, research, authority and DT-context obligations when the originally requested path cannot? The requested-path-only control is not a strong general planner. Fair stateful search and a separate constraint planner have the same authorized inputs and objective.'),
            ('Engineering and evidence',f"Engineering: {status['engineering_integrity']}; {status['checks_passed']}/{status['checks_total']} development checks. All new execution receipts were checked separately. Earlier project files preserved: {status['original_files_preserved']}/{status['original_files_checked']}. No classifiers were trained or loaded."),
            ('Important boundary','This is an additive deterministic research module, not a replacement for the live interface or its historical gates. Source snapshots are carried forward candidate records; substantive Korean applicability and clinical review remain pending. There is no new retrieval, signature-security, clinical-outcome, or full ITU conformance claim.')])
        for _,fig in plots:pdf.savefig(fig,bbox_inches='tight')
        text_page(pdf,'Interpretation and next dependencies',[
            ('Capable comparisons',f"Capable selectors agree with the reference objective and disposition: {status['capable_selectors_match_reference_objective_and_disposition']}. Capable selectors tie: {status['all_capable_selectors_tie']}. A tie is retained, not converted to a superiority claim. Any benefit over the original-request control demonstrates alternative choice within this finite action library."),
            ('Temporal revalidation',f"{status['temporal_probes_reject_changed_authority']}/{status['temporal_probes']} change-before-commit probes rejected the affected final action. These are perturbations of the same families, not independent clinical cases. Modeled approvals cannot authorize an action after epoch, purpose, or policy binding changes."),
            ('Workspace handoffs',f"{status['adapter_reference_agreement']}/{status['adapter_tests']} receiving-side decisions matched the separate implementation. Invalid or incomplete context accepted: {status['adapter_corrupted_or_missing_context_accepts']}. Explicit timestamps use an event-distance modeling assumption, not a clinical freshness threshold."),
            ('Source and institutional review','Interpretation review remains HOLD pending qualified Korean-policy and clinical reviewers. Clinical care-continuity obligations are explicitly modeled, not derived from a statute that sets a triage threshold. International WHO/OECD/ITU materials are comparison context, not Korean authorization.'),
            ('Next dependency','Review and sign off the scenario contracts and reference outcomes; then separately integrate the tested selection module into the progressive UI with commit-time revalidation. Do not use these snapshot results as proof of a deployed end-to-end medical workflow. Any post-confirmation repair needs a new version and fresh confirmation.')])
    outputs.append(report.name)
    save(dest/'plot_manifest.json',{'run_id':status['run_id'],'source_status_sha256':filehash(run/'status.json'),
        'files':{p:filehash(dest/p) for p in outputs},'show_requested':show,'dpi':dpi,'backend':str(plt.get_backend())})
    print('Figures and report saved:',dest)
    if show:plt.show()
    else:
        for _,fig in plots:plt.close(fig)
    return dest
