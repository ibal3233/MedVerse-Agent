"""Additional release validation. Historical Gates 1-26 are not modified or retrained."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from final_validation.validate import main
if __name__=='__main__':main()
