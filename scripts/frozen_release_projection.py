"""Compatibility entry for iqs_scan.questions.frozen_release_projection."""
import sys

from iqs_scan.questions import frozen_release_projection as _implementation

sys.modules[__name__] = _implementation
