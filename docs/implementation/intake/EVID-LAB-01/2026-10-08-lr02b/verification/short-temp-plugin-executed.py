"""Test-only Windows path adapter; no source bytes or product assertions change."""
import os
import sys
import tempfile
from pathlib import Path


def pytest_sessionstart(session):
    owned = Path(os.environ["E97_OWNED_ROOT"]).resolve()
    wanted = (owned / "lab/tests/conftest.py").resolve()
    modules = [module for module in list(sys.modules.values())
               if getattr(module, "__file__", None)
               and Path(module.__file__).resolve() == wanted]
    assert len(modules) == 1, "expected exact delivered conftest"
    original = modules[0].TEMP_ROOT
    assert original.is_relative_to(owned), "original temp root escaped"
    short = owned / "t"
    assert not short.exists(), "adapter must use a fresh exclusive root"
    short.mkdir()
    modules[0].TEMP_ROOT = short
    # The delivered temp_root fixture and atexit cleanup read TEMP_ROOT at call
    # time. Its old empty session root remains owned and is cleaned separately.
    for name in ("TEMP", "TMP", "TMPDIR"):
        os.environ[name] = str(short)
    tempfile.tempdir = str(short)
    session.config.option.basetemp = str(short / "basetemp")
