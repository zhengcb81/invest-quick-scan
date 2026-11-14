"""Compatibility entry for iqs_scan.experiments.applic_llm_compare."""
import sys

from iqs_scan.experiments import applic_llm_compare as _implementation

if __name__ == '__main__':
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
