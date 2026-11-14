"""Compatibility entry for iqs_scan.tools.compose_company_bank."""
import sys

from iqs_scan.tools import compose_company_bank as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
