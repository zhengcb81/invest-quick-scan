"""Compatibility entry for iqs_scan.experiments.applic_pipeline_check."""
import sys

from iqs_scan.experiments import applic_pipeline_check as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
