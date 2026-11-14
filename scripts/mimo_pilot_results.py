"""Compatibility entry for iqs_scan.experiments.mimo_pilot_results."""
import sys

from iqs_scan.experiments import mimo_pilot_results as _implementation

if __name__ == '__main__':
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
