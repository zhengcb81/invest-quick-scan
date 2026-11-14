"""Compatibility entry for iqs_scan.acceptance.stockwiki_g2b_acceptance."""
import sys

from iqs_scan.acceptance import stockwiki_g2b_acceptance as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
