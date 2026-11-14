"""Compatibility entry for iqs_scan.tools.one_click."""
import sys

from iqs_scan.tools import one_click as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
