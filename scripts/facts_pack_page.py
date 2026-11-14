"""Compatibility entry for iqs_scan.tools.facts_pack_page."""
import sys

from iqs_scan.tools import facts_pack_page as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
