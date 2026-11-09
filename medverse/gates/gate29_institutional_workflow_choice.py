"""Gate 29: run the frozen workflow-choice study; save evidence and show PNG/PDF plots.

Run this file directly in Spyder. No separate plotting launcher is required.
--stage all (default), dev, or confirm; --no-show saves without display;
--no-plots is an explicit no-Matplotlib mode; --plot-only --run RUN_ID reuses results.
Do not regenerate a freeze after inspecting results.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['all','dev','confirm'],default='all')
    p.add_argument('--no-show',action='store_true');p.add_argument('--no-plots',action='store_true')
    p.add_argument('--plot-only',action='store_true');p.add_argument('--run')
    p.add_argument('--dpi',type=int,default=300)
    args=p.parse_args(argv)
    if args.dpi<=0:p.error('--dpi must be positive')
    if args.run and not args.plot_only:p.error('--run requires --plot-only')
    if args.plot_only and args.no_plots:p.error('--plot-only cannot be combined with --no-plots')
    from coordination29.evaluate import run,verify_freeze
    from coordination29.common import save,load
    verify_freeze()
    if not args.no_plots:
        from coordination29.figures import make_figures,require_matplotlib,resolve_run
        require_matplotlib()
    if args.plot_only:
        dest=resolve_run(args.run);return load(dest/'status.json'),dest,make_figures(dest,not args.no_show,args.dpi)
    print('Gate 29 | Institutional workflow choice | independent reference outcomes | automatic figures')
    status,dest=run(args.stage);figures=None
    if not args.no_plots:
        try:
            figures=make_figures(dest,show=not args.no_show,dpi=args.dpi)
            save(dest/'presentation_status.json',{'status':'EXPORTED' if figures else 'NOT_APPLICABLE_DEV_ONLY','figures':str(figures),'scientific_status_unchanged':True})
        except Exception as exc:
            save(dest/'presentation_status.json',{'status':'FAILED','error':repr(exc),'scientific_status_unchanged':True})
            print('Raw results remain saved. Use --plot-only after resolving the plotting error.',file=sys.stderr)
            raise
    return status,dest,figures

if __name__=='__main__':main()
