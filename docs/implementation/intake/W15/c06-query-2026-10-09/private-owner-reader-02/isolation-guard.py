import os, socket, sqlite3, sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
OWN=Path(os.environ["IQS_C06_OWN"]).resolve()
def denied(*args, **kwargs): raise RuntimeError("C06 offline: network denied")
_socket_connect=socket.socket.connect
_pair_code=socket._fallback_socketpair.__code__
def guarded_connect(self, address):
    # Windows asyncio's stdlib socketpair needs exactly its own local listener.
    # Ordinary localhost HTTP and every non-loopback connection remain denied.
    frame=sys._getframe(1)
    if frame.f_code is _pair_code and frame.f_locals.get("csock") is self:
        listener=frame.f_locals.get("lsock")
        if (listener is not None and isinstance(address, tuple) and len(address)==2
                and address[0] in {"127.0.0.1", "::1"}
                and listener.getsockname()[:2]==address
                and listener.getsockopt(socket.SOL_SOCKET,socket.SO_ACCEPTCONN)==1):
            return _socket_connect(self,address)
    return denied(self,address)
socket.socket.connect=guarded_connect
socket.socket.connect_ex=denied
socket.socket.sendto=denied
_connect=sqlite3.connect
def connect(database, *args, **kwargs):
    if database != ":memory:":
        text=str(database)
        if text.startswith("file:"):
            parsed=urlsplit(text)
            if parsed.netloc or parsed.fragment: raise RuntimeError("C06 offline: URI authority denied")
            text=unquote(parsed.path)
            if len(text)>3 and text[0]=="/" and text[2]==":": text=text[1:]
        if not Path(text).resolve().is_relative_to(OWN): raise RuntimeError("C06 offline: foreign database denied")
    return _connect(database, *args, **kwargs)
sqlite3.connect=connect
