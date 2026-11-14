"""Compatibility entry for iqs_scan.workbench.workbench_snapshot_cli."""
import sys

from iqs_scan.workbench import workbench_snapshot_cli as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
