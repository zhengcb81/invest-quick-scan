"""Compatibility entry for iqs_scan.tools.profile_page."""
import sys

from iqs_scan.tools import profile_page as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
