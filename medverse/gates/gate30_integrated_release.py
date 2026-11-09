"""Single entry point: evaluate through HTTP, save raw results, export and show figures."""
from pathlib import Path
import sys,argparse
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--no-show',action='store_true');p.add_argument('--no-plots',action='store_true');p.add_argument('--plot-only',action='store_true');p.add_argument('--run');a=p.parse_args(argv)
 from coordination30.common import OUT,load
 if a.plot_only:
  if a.run:
   dest=(OUT/a.run).resolve()
   if not dest.is_relative_to(OUT.resolve()):raise ValueError('Invalid run identifier')
  else:
   dirs=sorted(p.parent for p in OUT.glob('*/status.json'))
   if not dirs:raise FileNotFoundError('No evaluated Gate 30 run')
   dest=dirs[-1]
  status=load(dest/'status.json')
 else:
  from coordination30.evaluate import run
  status,dest=run()
 figures=None
 if not a.no_plots:
  try:
   from coordination30.figures import make_figures
   figures=make_figures(dest,show=not a.no_show)
  except ImportError as e:
   print('Evaluation saved. Plotting dependency unavailable:',e)
   print('Install matplotlib and rerun this script with --plot-only --run',dest.name)
 print('Gate 30:',status['engineering_integrity'],'| run:',dest)
 return status,dest,figures
if __name__=='__main__':main()
