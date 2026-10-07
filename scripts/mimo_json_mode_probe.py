"""Compatibility entry for the hardened adaptive JSON-off experiment."""
import sys
import mimo_pilot_extension as e

if __name__=='__main__':
    sys.argv.extend(['--kind','jsonoff'])
    e.main()
