"""Credential-free test processes: sockets denied and all writes confined."""
import atexit
import json
import os
from pathlib import Path
import socket
import sys
from urllib.parse import parse_qs, urlsplit


def deny(*args, **kwargs):
    raise AssertionError("isolated continuation tests prohibit network")

socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.create_connection = deny

def _resolved(value):
    text=os.fsdecode(value)
    # The original artifact writer uses the Win32 extended path spelling for
    # long names. Normalize only that spelling; traversal/symlinks still resolve.
    if text.startswith("\\\\?\\"):
        text=text[4:]
        if text.startswith("UNC\\"):
            text="\\\\"+text[4:]
    result=str(Path(text).resolve())
    if result.startswith("\\\\?\\"):
        result=result[4:]
        if result.startswith("UNC\\"):
            result="\\\\"+result[4:]
    return Path(result)

_own = _resolved(os.environ.get("IQS_CONTINUATION_OWN") or os.environ["IQS_C06_OWN"])
if _own.name == "runtime":
    _own = _own.parent
_seen = set()
_denied = []


def _is_null_device(value):
    return not isinstance(value, int) and value is not None and _resolved(value) == _resolved(os.devnull)

def _inside(value):
    if isinstance(value, int) or value is None or _is_null_device(value):
        return True
    return _resolved(value).is_relative_to(_own)


def _assert_write(value, event):
    if not _inside(value):
        _denied.append({"event":event,"path":str(_resolved(value))})
        raise AssertionError("isolated continuation write outside owned candidate: " + event)
    if not isinstance(value, int) and value is not None and not _is_null_device(value):
        _seen.add((event, str(_resolved(value).relative_to(_own))))


def _audit(event, args):
    if event == "open":
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
        if writing:
            _assert_write(path, event)
    elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.truncate", "os.utime"}:
        _assert_write(args[0], event)
    elif event in {"os.rename", "os.link", "os.symlink"}:
        _assert_write(args[0], event)
        _assert_write(args[1], event)
    elif event == "sqlite3.connect":
        database = os.fsdecode(args[0])
        if database == ":memory:":
            return
        if database.startswith("file:") and parse_qs(urlsplit(database).query).get("mode") == ["ro"]:
            _seen.add(("sqlite_readonly", database.split("?", 1)[0]))
            return
        _assert_write(database, event)

sys.addaudithook(_audit)


def _report():
    # No SQL, answer, request, environment or credential values are retained.
    target = _own / "evidence" / ("isolation-" + str(os.getpid()) + ".json")
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({"protocol": "iqs.test_write_audit/1.0.0", "pid": os.getpid(), "network": "denied", "outside_write_denials": list(_denied), "write_targets": sorted([list(v) for v in _seen]), "all_writes_confined": not _denied}), encoding="utf8")

atexit.register(_report)
