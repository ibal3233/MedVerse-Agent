"""Gate 32: verify, evaluate, save, export PNG/PDF and display automatically."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
sys.dont_write_bytecode=True

def main(argv=None):
 import argparse,json
 from commitment32.common import OUT,load
 from commitment32.evaluate import evaluate,verify_freeze
 p=argparse.ArgumentParser(description='Causal bounded commitment; previous gates remain unchanged.')
 p.add_argument('--no-show',action='store_true');p.add_argument('--no-plots',action='store_true')
 p.add_argument('--plot-only',action='store_true');p.add_argument('--run')
 a=p.parse_args(argv)
 if a.plot_only:
  verify_freeze()
  if a.run:
   dest=(OUT/a.run).resolve()
   if not dest.is_relative_to(OUT.resolve()):raise ValueError('Invalid run directory')
  else:
   runs=sorted(OUT.glob('*/status.json'))
   if not runs:raise FileNotFoundError('No completed Gate 32 run')
   dest=runs[-1].parent
  status=load(dest/'status.json')
 else:
  print('Gate 32: commitment timing only; original selector and policy validator retained.',flush=True)
  status,dest=evaluate()
 figs=None
 if not a.no_plots:
  try:
   from commitment32.figures import make_figures
   figs=make_figures(dest,show=not a.no_show)
  except ImportError as e:
   print('Raw evidence saved. Plotting requires Matplotlib. Re-run --plot-only after installation. Detail:',e)
 print(json.dumps(status,ensure_ascii=False,indent=2));print('Raw evidence:',dest)
 return status,dest,figs
if __name__=='__main__':main()
