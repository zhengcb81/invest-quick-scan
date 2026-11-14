"""Legacy script imports. Use iqs_scan public APIs for new code."""
from pathlib import Path
import sys

_script_dir = str(Path(__file__).resolve().parent)
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
