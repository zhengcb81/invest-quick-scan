import os, socket, sqlite3
from pathlib import Path
from urllib.parse import urlsplit, unquote
OWN=Path(os.environ["IQS_W15_OWN"]).resolve()
def denied(*args, **kwargs): raise RuntimeError("W15 offline: network denied")
socket.socket.connect=denied
socket.socket.connect_ex=denied
socket.socket.sendto=denied
_connect=sqlite3.connect
def connect(database, *args, **kwargs):
    if database != ":memory:":
        text=str(database)
        if text.startswith("file:"):
            parsed=urlsplit(text)
            if parsed.netloc or parsed.fragment: raise RuntimeError("W15 offline: URI authority denied")
            text=unquote(parsed.path)
            if len(text)>3 and text[0]=="/" and text[2]==":": text=text[1:]
        if not Path(text).resolve().is_relative_to(OWN): raise RuntimeError("W15 offline: foreign database denied")
    return _connect(database, *args, **kwargs)
sqlite3.connect=connect
