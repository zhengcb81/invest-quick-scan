"""Compatibility entry for iqs_scan.foundation.search_receipt."""
import sys

from iqs_scan.foundation import search_receipt as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
