"""Compatibility entry for iqs_scan.execution.shared_company_engine."""
import sys

from iqs_scan.execution import shared_company_engine as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
