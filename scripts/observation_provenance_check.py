"""Compatibility entry for iqs_scan.tools.observation_provenance_check."""
import sys

from iqs_scan.tools import observation_provenance_check as _implementation

if __name__ == '__main__':
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
