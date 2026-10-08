"""Run the ORIGINAL SW-READY-01 acceptance cases against the SW-REPAIR-02 tree.

Reuses the 总控 guard *semantics* of
``invest-quick-scan/docs/implementation/reviews/SW-READY-01/guarded_tests.py``
without modifying that script and without writing into IQS ``runs/``: this
runner pins its own export root under ``StockWiki/runs/swr02-acceptance-*``,
treats the exported runtime as read-only source, and keeps every write, rename,
rmtree, subprocess and socket inside that one root through the same audit-hook
approach. The counterexample file itself is the ORIGINAL
``acceptance_cases.py`` (SHA256 asserted below), never a re-implementation.

Usage::

    python -B -X utf8 docs/handoff/SW-REPAIR-02/run_frozen_acceptance.py \
        --work-root <StockWiki>/runs/swr02-acceptance-<unique>
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

ACCEPTANCE_REL = "docs/implementation/reviews/SW-READY-01/acceptance_cases.py"
ACCEPTANCE_SHA256 = "72b2e1250947a705f87426557ccdf8b09121d761ba09ae89da3df152db81d452"
IQS_ROOT = Path("C:/Users/郑曾波/Projects/invest-quick-scan")
STOCKWIKI_ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--runtime-sha", default="", help="optional expected runtime manifest sha")
    args = parser.parse_args()

    own = args.work_root.resolve()
    if (
        not own.is_relative_to(STOCKWIKI_ROOT / "runs")
        or not own.name.startswith("swr02-acceptance-")
        or not (own / "runtime" / "stockwiki").is_dir()
        or not (own / "export-manifest.json").is_file()
    ):
        raise ValueError("own StockWiki/runs/swr02-acceptance-* export root required")

    acceptance = IQS_ROOT / ACCEPTANCE_REL
    digest = hashlib.sha256(acceptance.read_bytes()).hexdigest()
    if digest != ACCEPTANCE_SHA256:
        raise ValueError(f"original counterexample file changed: {digest}")
    manifest_sha = hashlib.sha256((own / "export-manifest.json").read_bytes()).hexdigest()
    if args.runtime_sha and manifest_sha != args.runtime_sha:
        raise ValueError(f"export manifest drift: {manifest_sha}")

    for name in tuple(os.environ):
        if name.endswith(("API_KEY", "API_TOKEN")):
            del os.environ[name]
    for name in ("TMP", "TEMP", "TMPDIR"):
        os.environ[name] = str(own / "temp")
    (own / "temp").mkdir(exist_ok=True)
    # The ORIGINAL file reads this variable by name; the value is OUR StockWiki
    # root, never an IQS runs/ path (this package must not write there).
    os.environ["IQS_SW_READY_WORK_ROOT"] = str(own)
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(own / "runtime"), str(own / "runtime" / "tests")]

    def path_ok(value) -> None:
        if isinstance(value, int):
            return
        raw = os.fsdecode(value)
        if raw.startswith("\\\\?\\"):
            raw = raw[4:]
        if not Path(raw).resolve().is_relative_to(own):
            raise PermissionError("swr02_guard_outside_write")

    def audit(event, a_args):  # noqa: ANN001 - mirrors the 总控 guard hook
        if event == "open":
            path, mode, flags = a_args
            if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int)
                and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            ):
                path_ok(path)
        elif event in ("os.mkdir", "os.remove", "os.rmdir", "shutil.rmtree"):
            path_ok(a_args[0])
        elif event in ("os.rename", "os.replace", "os.link", "os.symlink"):
            path_ok(a_args[0])
            path_ok(a_args[1])
        elif (
            event.startswith("socket.")
            or event == "subprocess.Popen"
            or event == "os.system"
            or event.startswith("winreg.")
        ):
            raise PermissionError("swr02_guard_network_process_registry")

    sys.addaudithook(audit)

    canary = own.parent / "swr02-guard-canary.txt"
    assert not canary.exists()
    try:
        canary.write_text("must not write", encoding="utf-8")
        raise AssertionError("outside write allowed")
    except PermissionError:
        pass
    import socket

    try:
        socket.getaddrinfo("example.com", 443)
        raise AssertionError("DNS allowed")
    except PermissionError:
        pass
    print("swr02_guard_canaries_passed", flush=True)
    print(f"export_manifest_sha256={manifest_sha}", flush=True)

    os.chdir(own / "runtime")
    import pytest

    return pytest.main(
        [
            "-q",
            str(acceptance),
            "--rootdir",
            str(own),
            "--basetemp",
            str(own / "pytest"),
            "--override-ini",
            "cache_dir=" + str(own / "cache"),
            "--override-ini",
            "log_file=" + str(own / "pytest.log"),
            "--tb=short",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
