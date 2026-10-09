"""Test-controller isolation checks, never an application feature or OS claim."""
import socket
import sqlite3

import pytest


@pytest.mark.parametrize("host", ["127.0.0.1", "192.0.2.1"])
def test_ordinary_network_connect_is_denied(host):
    with socket.socket() as client:
        with pytest.raises(RuntimeError, match="W15 offline: network denied"):
            client.connect((host, 443))


def test_windows_stdlib_socketpair_ipc_is_allowed_and_closed():
    left, right = socket.socketpair()
    try:
        left.sendall(b"IPC")
        assert right.recv(3) == b"IPC"
    finally:
        left.close()
        right.close()


def test_foreign_sqlite_never_opens():
    with pytest.raises(RuntimeError, match="W15 offline: foreign database denied"):
        sqlite3.connect("C:/w15-foreign-database-denied.sqlite")
