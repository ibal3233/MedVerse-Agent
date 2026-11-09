"""Gate 30 integrated sandbox. The archived run_final_sandbox.py remains unchanged."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from coordination30.server import main
if __name__=='__main__':main()
