"""Run only the two disclosed same-chain segment cases."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import OWN, pytest
source = Path(__file__).parent / 'segment_cases.py'
(OWN / 'segment_cases.py').write_bytes(source.read_bytes())
pytest('segment-two', [str(OWN / 'segment_cases.py')])
