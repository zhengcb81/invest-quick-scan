"""Compatibility entry for iqs_scan.tools.scoring_rubrics."""
import sys

from iqs_scan.tools import scoring_rubrics as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
