"""Compatibility entry for iqs_scan.tools.bank_lint."""
import sys

from iqs_scan.tools import bank_lint as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
