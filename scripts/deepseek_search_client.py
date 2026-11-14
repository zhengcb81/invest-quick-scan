"""Compatibility entry for iqs_scan.experiments.deepseek_search_client."""
import sys

from iqs_scan.experiments import deepseek_search_client as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
