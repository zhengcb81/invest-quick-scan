"""Compatibility entry for iqs_scan.tools.bank_manifest_preflight."""
import sys

from iqs_scan.tools import bank_manifest_preflight as _implementation

if __name__ == '__main__':
    sys.exit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
