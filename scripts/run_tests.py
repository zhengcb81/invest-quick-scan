"""Compatibility entry for iqs_scan.tools.run_tests."""
import sys

from iqs_scan.tools import run_tests as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
