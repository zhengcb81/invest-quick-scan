"""Compatibility entry for iqs_scan.tools.pipeline_review_apply."""
import sys

from iqs_scan.tools import pipeline_review_apply as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
