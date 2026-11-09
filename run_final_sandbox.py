"""Run directly or with Spyder %runfile .../run_final_sandbox.py --wdir."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from final_validation.server import main
if __name__=='__main__':main()
