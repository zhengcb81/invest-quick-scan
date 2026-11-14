"""Compatibility entry for iqs_scan.workbench.c06_authority."""
import sys

from iqs_scan.workbench import c06_authority as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
