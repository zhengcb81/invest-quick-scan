"""Compatibility entry for iqs_scan.tools.route_store_handoff."""
import sys

from iqs_scan.tools import route_store_handoff as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
