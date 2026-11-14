"""Compatibility entry for iqs_scan.foundation.json_io."""
import sys

from iqs_scan.foundation import json_io as _implementation

sys.modules[__name__] = _implementation
