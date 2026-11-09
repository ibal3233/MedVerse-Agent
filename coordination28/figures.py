"""Optional plotting; not part of the frozen runtime. Requires matplotlib."""
from pathlib import Path
import csv,json

def find_run(root):
    candidates=[]
    for folder in (root/'outputs/gate28_coordination').iterdir():
        status_path=folder/'status.json'
        if folder.is_dir() and status_path.exists():
            status=json.loads(status_path.read_text())
            if status.get('stage')=='all':candidates.append((folder.name,folder,status))
    if not candidates:raise FileNotFoundError('No full Gate 28 experiment is available.')
    _,folder,status=max(candidates,key=lambda item:item[0])
    if status.get('engineering_integrity')!='PASS':
        raise RuntimeError('Latest full run failed; do not silently plot an older successful run.')
    return folder

def make_figures(root=None):
    import matplotlib.pyplot as plt
    import numpy as np
    root=Path(root) if root else Path(__file__).resolve().parents[1]
    run=find_run(root);s=json.loads((run/'status.json').read_text())
    dest=root/'outputs/gate28_coordination/figures';dest.mkdir(exist_ok=True)
    rows=s['strategy_summary']
    labels=['Snapshot\nonce','Sequential\nonce','Stateful\nfixed point','Dependency\nordered','Dependency\nedges removed']
    fig,ax=plt.subplots(figsize=(9.1,4.7))
    bars=ax.bar(labels,[100*r['macro_family_completion_fraction'] for r in rows],width=0.6)
    ax.bar_label(bars,labels=[f"{100*r['macro_family_completion_fraction']:.1f}%" for r in rows],padding=4)
    ax.set_ylim(0,114);ax.set_ylabel('Completion averaged equally across workflow families (%)')
    ax.set_title('Gate 28: proposal-order robustness',pad=14)
    ax.grid(axis='y',alpha=0.2);ax.set_axisbelow(True)
    fig.text(.5,.015,'Eight previously seen modeled families; 318 distinct family-schedule pairs per configuration.\n'
             'Correlated delivery-order perturbations, not 318 independent clinical cases.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.085,1,1))
    for suffix in ('png','pdf'):fig.savefig(dest/f'Gate28_Order_Robustness.{suffix}',dpi=300,bbox_inches='tight')
    plt.close(fig)
    fix=next(r for r in rows if r['strategy']=='STATEFUL_FIXED_POINT')
    graph=next(r for r in rows if r['strategy']=='DEPENDENCY_ORDERED')
    fig,ax=plt.subplots(figsize=(7.8,4.6))
    bars=ax.bar(['Fair stateful retry','Dependency ordering'],[fix['total_validation_calls'],graph['total_validation_calls']],width=.5)
    ax.bar_label(bars,labels=[f"{fix['total_validation_calls']:,}",f"{graph['total_validation_calls']:,}"],padding=5)
    ax.set_ylim(0,max(fix['total_validation_calls'],graph['total_validation_calls'])*1.18)
    ax.set_ylabel('Total validator calls (preflight + final revalidation)')
    ax.set_title('Equal completion; modest revalidation reduction',pad=14)
    ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.text(.5,.015,'318/318 schedules completed by both methods. Dependency ordering saves 126 calls (1.03%).\n'
             'This is an operation-count result, not a measured end-to-end latency advantage.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.09,1,1))
    for suffix in ('png','pdf'):fig.savefig(dest/f'Gate28_Validation_Effort.{suffix}',dpi=300,bbox_inches='tight')
    plt.close(fig)
    print('Saved two Gate 28 result figures as PNG and PDF:',dest)
    return dest

if __name__=='__main__':make_figures()
