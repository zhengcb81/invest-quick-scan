"""Compatibility entry for iqs_scan.providers.provider_transport."""
import sys

from iqs_scan.providers import provider_transport as _implementation

sys.modules[__name__] = _implementation
