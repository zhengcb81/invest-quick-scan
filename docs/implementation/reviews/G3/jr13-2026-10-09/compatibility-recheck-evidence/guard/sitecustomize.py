"""QA-C06-02 subprocess guard: synthetic only, no provider calls."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

OWNED = Path(os.environ["E97_OWNED_ROOT"]).resolve()
KEY_LEDGER = OWNED / "key-opens.jsonl"
NET_LEDGER = OWNED / "network-attempts.jsonl"
_pair_sockets = []


def _inside(raw):
    if isinstance(raw, int):
        return True
    path = Path(os.fsdecode(raw)).resolve()
    if path == Path(os.devnull).resolve():
        return True
    return path.is_relative_to(OWNED)


def _append(ledger, payload):
    with Path(ledger).open("a", encoding="utf-8") as stream:
        stream.write(payload + "\n")


def audit(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "socket.bind", "socket.sendto"}:
        # Windows asyncio's internal socketpair: the exact ephemeral loopback
        # bind (127.0.0.1 or ::1, port 0) and connects to exactly that socket.
        # No external address, listener or model/search HTTP is admitted, so
        # the pair never counts as a network attempt.
        if event == "socket.bind" and args[1] in {("127.0.0.1", 0), ("::1", 0)}:
            _pair_sockets.append(args[0])
            return
        if event == "socket.connect":
            for sock in _pair_sockets:
                try:
                    if sock.getsockname() == args[1]:
                        return
                except OSError:
                    pass
        _append(NET_LEDGER, event)
        raise PermissionError("network is forbidden in this test root")
    if event == "open":
        mode, flags = args[1], args[2]
        writing = (isinstance(mode, str) and any(ch in mode for ch in "wax+")) or (
            isinstance(flags, int)
            and flags
            & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        )
        if writing:
            if not _inside(args[0]):
                raise PermissionError("write outside the owned test root")
        elif not isinstance(args[0], int) and Path(os.fsdecode(args[0])).name == "llm_apis.json":
            _append(KEY_LEDGER, os.fsdecode(args[0]))
    if event in {"os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.utime"}:
        if not _inside(args[0]):
            raise PermissionError("write outside the owned test root")
    if event in {"os.rename", "os.replace", "os.link", "os.symlink"}:
        if not (_inside(args[0]) and _inside(args[1])):
            raise PermissionError("write outside the owned test root")
    if event in {"os.system", "os.exec", "os.posix_spawn"}:
        raise PermissionError("shell execution is forbidden in this test root")
    if event == "subprocess.Popen":
        executable, argv, cwd, env = args
        same_python = (
            (Path(executable).resolve() == Path(sys.executable).resolve())
            if executable
            else (
                isinstance(argv, str)
                and argv.startswith(subprocess.list2cmdline([sys.executable]) + " ")
            )
        )
        if not same_python:
            raise PermissionError("only Python child processes are allowed")
        if cwd is None or not Path(cwd).resolve().is_relative_to(OWNED):
            raise PermissionError("child cwd outside the owned test root")
        if env is None or not Path(env.get("E97_OWNED_ROOT", "__missing__")).resolve().is_relative_to(OWNED):
            raise PermissionError("child guard not inherited")
        if any(key.upper().endswith("_API_KEY") for key in env):
            raise PermissionError("credentials in the child environment")


sys.addaudithook(audit)

