"""Single entry point: evaluate, save evidence, export PDF/PNG, display plots."""
from pathlib import Path
import sys,argparse,json
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def main(argv=None):
 from release33.common import OUT,read
 p=argparse.ArgumentParser(description='Gate33: unchanged commitment engine through progressive HTTP/UI')
 p.add_argument('--no-show',action='store_true');p.add_argument('--no-plots',action='store_true')
 p.add_argument('--plot-only',action='store_true');p.add_argument('--run');p.add_argument('--browser',action='store_true')
 a=p.parse_args(argv)
 if a.plot_only:
  candidates=sorted(OUT.glob('*/status.json'))
  if a.run:
   run=(OUT/a.run).resolve()
   if not run.is_relative_to(OUT.resolve()) or not (run/'status.json').is_file():raise FileNotFoundError('Unknown run')
  else:
   if not candidates:raise FileNotFoundError('No measured run available')
   run=candidates[-1].parent
  status=read(run/'status.json')
 else:
  from release33.evaluate import evaluate
  status,run=evaluate()
 if a.browser:
  from release33.browser_check import main as check_browser
  check_browser(run)
 figdir=None
 if not a.no_plots:
  try:
   from release33.figures import make_figures
   figdir=make_figures(run,show=not a.no_show)
  except ModuleNotFoundError as e:
   print('Evidence saved; plotting dependency missing:',e)
   print('Install matplotlib, then run this same script with --plot-only --run '+run.name)
 print(json.dumps(status,indent=2));print('Raw evidence:',run)
 return status,run,figdir
if __name__=='__main__':main()
