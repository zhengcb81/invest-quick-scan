"""Compatibility entry for iqs_scan.experiments.batching_benchmark_archive."""
import sys

from iqs_scan.experiments import batching_benchmark_archive as _implementation

if __name__ == '__main__':
    from iqs_scan.foundation.api import run_diagnostic_command

    raise SystemExit(run_diagnostic_command(_implementation.main))
else:
    sys.modules[__name__] = _implementation
