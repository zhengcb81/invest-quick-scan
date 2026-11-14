"""Compatibility entry for iqs_scan.workbench.dashboard_owner."""
import sys

from iqs_scan.workbench import dashboard_owner as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.worker_main())
else:
    sys.modules[__name__] = _implementation
