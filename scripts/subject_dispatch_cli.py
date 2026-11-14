"""Compatibility entry for iqs_scan.execution.subject_dispatch_cli."""
import sys

from iqs_scan.execution import subject_dispatch_cli as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
