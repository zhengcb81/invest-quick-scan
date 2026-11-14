"""Compatibility entry for iqs_scan.acceptance.verified_evidence_audit."""
import sys

from iqs_scan.acceptance import verified_evidence_audit as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
