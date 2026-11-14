"""Compatibility entry for iqs_scan.acceptance.parallel_handoff_cli."""
import sys

from iqs_scan.acceptance import parallel_handoff_cli as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
