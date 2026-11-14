"""Compatibility entry for iqs_scan.execution.owner_admission_subject."""
import sys

from iqs_scan.execution import owner_admission_subject as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
