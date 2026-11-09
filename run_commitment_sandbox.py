"""Gate 33 operator interface. Existing launchers remain unchanged."""
import sys
sys.dont_write_bytecode=True
from release33.server import main
if __name__=='__main__':main()
