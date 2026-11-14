"""Compatibility entry for iqs_scan.questions.module_registry."""
import sys

from iqs_scan.questions import module_registry as _implementation

sys.modules[__name__] = _implementation
