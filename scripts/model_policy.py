"""Compatibility entry for iqs_scan.providers.model_policy."""
import sys

from iqs_scan.providers import model_policy as _implementation

if __name__ == '__main__':
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
