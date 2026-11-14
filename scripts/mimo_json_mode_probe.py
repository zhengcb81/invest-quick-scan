"""Compatibility entry for iqs_scan.experiments.mimo_json_mode_probe."""
import sys

from iqs_scan.experiments import mimo_json_mode_probe as _implementation

if __name__ == '__main__':
    _implementation.cli()
else:
    sys.modules[__name__] = _implementation
