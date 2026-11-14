"""Compatibility entry for iqs_scan.foundation.metric_coordinates."""
import sys

from iqs_scan.foundation import metric_coordinates as _implementation

sys.modules[__name__] = _implementation
