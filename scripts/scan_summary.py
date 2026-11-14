"""Compatibility entry for iqs_scan.tools.scan_summary."""
import sys

from iqs_scan.tools import scan_summary as _implementation

if __name__ == '__main__':
    sys.exit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
