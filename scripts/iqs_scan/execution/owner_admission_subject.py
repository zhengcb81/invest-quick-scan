"""Retired historical subject generator; use StockWiki's public subject CLI.

The old experiment generated verified payloads from a ticker and fixed period.
Its implementation remains in Git history. This compatibility command parses
old arguments only to direct callers to the actual identity/subject owner.
"""
from __future__ import annotations

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--out")
    parser.add_argument("--scope-as-of")
    parser.add_argument("--apply", action="store_true")
    parser.parse_args(argv)
    raise SystemExit("Legacy subject generation is retired; use StockWiki analysis-subject-import with an explicit verified entity/security and independently established subject payload")
