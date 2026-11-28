"""Compatibility entry for iqs_scan.experiments.applic_pipeline_check."""
import sys

from iqs_scan.experiments import applic_pipeline_check as _implementation

if __name__ == '__main__':
    from iqs_scan.foundation.api import run_diagnostic_command

    raise SystemExit(run_diagnostic_command(_implementation.main))
else:
    sys.modules[__name__] = _implementation
