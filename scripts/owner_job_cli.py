"""Compatibility entry for iqs_scan.execution.owner_job_cli."""
import sys

from iqs_scan.execution import owner_job_cli as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
