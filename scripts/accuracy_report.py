"""Compatibility entry for iqs_scan.experiments.accuracy_report."""
import sys

from iqs_scan.experiments import accuracy_report as _implementation

if __name__ == '__main__':
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
