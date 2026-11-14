"""Compatibility entry for iqs_scan.execution.search_exposure_contract."""
import sys

from iqs_scan.execution import search_exposure_contract as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
