import os, socket, sqlite3
from pathlib import Path
OWN=Path(os.environ["IQS_W15_OWN"]).resolve()
def denied(*args, **kwargs): raise RuntimeError("W15 offline: network denied")
socket.socket.connect=denied
socket.socket.connect_ex=denied
socket.socket.sendto=denied
_connect=sqlite3.connect
def connect(database, *args, **kwargs):
    if database != ":memory:":
        text=str(database)
        if text.startswith("file:"): raise RuntimeError("W15 offline: URI database denied")
        if not Path(database).resolve().is_relative_to(OWN): raise RuntimeError("W15 offline: foreign database denied")
    return _connect(database, *args, **kwargs)
sqlite3.connect=connect
