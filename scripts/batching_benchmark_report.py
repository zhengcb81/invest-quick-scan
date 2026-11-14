"""Compatibility entry for iqs_scan.experiments.batching_benchmark_report."""
import sys

from iqs_scan.experiments import batching_benchmark_report as _implementation

if __name__ == '__main__':
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
