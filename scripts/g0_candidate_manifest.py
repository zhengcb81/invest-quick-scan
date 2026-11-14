"""Compatibility entry for iqs_scan.acceptance.g0_candidate_manifest."""
import sys

from iqs_scan.acceptance import g0_candidate_manifest as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
