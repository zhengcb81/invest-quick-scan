"""Compatibility entry for iqs_scan.tools.identity_contract_cli."""
import sys

from iqs_scan.tools import identity_contract_cli as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
