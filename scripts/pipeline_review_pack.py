"""Compatibility entry for iqs_scan.experiments.pipeline_review_pack."""
import sys

from iqs_scan.experiments import pipeline_review_pack as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
