"""Independent review guard: imported by every Python child."""
import atexit
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
COPY = ROOT / "csc"
ALLOWED = (ROOT,)
events = {"network_attempts": 0, "external_write_attempts": 0, "external_writes": 0}

def checked(path):
    if isinstance(path, int) or path is None:
        return
    if os.fsdecode(path).lower() in ("nul", "\\\\.\\nul"):
        return  # pytest's null log sink is a device, not an external file.
    p = Path(os.fsdecode(path)).resolve()
    if not any(p == root or p.is_relative_to(root) for root in ALLOWED):
        events["external_write_attempts"] += 1
        raise PermissionError(f"independent guard blocks external write: {p}")

def audit(event, args):
    if event in ("socket.connect", "socket.getaddrinfo", "socket.bind", "socket.sendto"):
        events["network_attempts"] += 1
        raise PermissionError("independent guard blocks network")
    if event == "open":
        path, mode, flags = args
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            checked(path)
    elif event in ("os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.utime", "os.truncate"):
        checked(args[0])
    elif event in ("os.rename", "os.link", "os.symlink"):
        checked(args[0]); checked(args[1])

sys.dont_write_bytecode = True
sys.addaudithook(audit)

def save():
    path = ROOT / "guard-logs" / f"guard-{os.getpid()}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"pid": os.getpid(), **events}), encoding="utf8")
atexit.register(save)
