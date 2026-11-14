"""Compatibility entry for iqs_scan.execution.task_receipts."""
import sys

from iqs_scan.execution import task_receipts as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
