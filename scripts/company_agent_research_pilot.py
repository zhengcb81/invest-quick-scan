"""Compatibility entry for iqs_scan.experiments.company_agent_research_pilot."""
import sys

from iqs_scan.experiments import company_agent_research_pilot as _implementation

if __name__ == '__main__':
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
