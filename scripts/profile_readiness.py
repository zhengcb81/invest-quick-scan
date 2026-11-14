"""Compatibility entry for iqs_scan.tools.profile_readiness."""
import sys

from iqs_scan.tools import profile_readiness as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
