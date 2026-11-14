"""Compatibility entry for the hardened adaptive JSON-off experiment."""
import sys
from . import mimo_pilot_extension as e


def cli():
    sys.argv.extend(['--kind','jsonoff'])
    e.main()
