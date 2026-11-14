"""Compatibility entry for iqs_scan.acceptance.observation_import_preflight."""
import sys

from iqs_scan.acceptance import observation_import_preflight as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
