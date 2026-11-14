"""Compatibility entry for iqs_scan.experiments.company_agent_contrast_launcher."""
import sys

from iqs_scan.experiments import company_agent_contrast_launcher as _implementation

if __name__ == '__main__':
    _implementation.cli()
else:
    sys.modules[__name__] = _implementation
