"""Compatibility entry for iqs_scan.experiments.zai_route_diagnostic."""
import sys

from iqs_scan.experiments import zai_route_diagnostic as _implementation

if __name__ == '__main__':
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
