"""One entry point: verify, evaluate, save, export PDF/PNG, display.

No dense fallback. '--allow-download' explicitly permits pinned public weights.
Known inputs are regression, not a fresh confirmation study.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
sys.dont_write_bytecode=True

def main(argv=None):
    import argparse,json
    from foundation31.common import OUT,read
    from foundation31.evaluate import main_evaluation,verify_freeze
    p=argparse.ArgumentParser()
    p.add_argument('--allow-download',action='store_true');p.add_argument('--model-cache')
    p.add_argument('--no-show',action='store_true');p.add_argument('--no-plots',action='store_true')
    p.add_argument('--plot-only',action='store_true');p.add_argument('--run')
    a=p.parse_args(argv)
    if a.plot_only:
        verify_freeze()
        if a.run:
            dest=(OUT/a.run).resolve()
            if not dest.is_relative_to(OUT.resolve()):raise ValueError('Invalid run path')
        else:
            choices=sorted(OUT.glob('*/status.json'))
            if not choices:raise FileNotFoundError('No saved Gate31 run')
            dest=choices[-1].parent
        status=read(dest/'status.json')
    else:
        print('Gate 31: original DT / pinned evidence bridge. Prior commitment logic unchanged.',flush=True)
        status,dest=main_evaluation(a.allow_download,a.model_cache)
    figures=None
    if not a.no_plots:
        try:
            from foundation31.figures import make_figures
            figures=make_figures(dest,not a.no_show)
        except ImportError as e:
            print('Plotting unavailable; raw measurements preserved. Install matplotlib, then --plot-only. Detail:',e)
    print(json.dumps(status,indent=2,ensure_ascii=False));print('Raw evidence:',dest)
    return status,dest,figures
if __name__=='__main__':main()
