"""Compatibility entry for iqs_scan.tools.facts_authority_build."""
import sys

from iqs_scan.tools import facts_authority_build as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
