"""Short filesystem locks that the kernel releases on process death."""

from contextlib import ExitStack, contextmanager
import os
import time

from .json_io import physical_path


class ControlBusyError(OSError):
    pass


@contextmanager
def control_lock(path, *, timeout_seconds=0.0):
    """Acquire immediately by default, or wait until the caller's deadline."""
    path = physical_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not 0 <= timeout_seconds < float("inf"):
        raise ValueError("control lock wait must be finite and nonnegative")
    deadline = time.monotonic() + timeout_seconds
    with path.open("a+b") as stream, ExitStack() as acquired:
        while True:
            try:
                acquired.enter_context(_kernel_lock(stream))
                break
            except ControlBusyError:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise
                time.sleep(min(0.01, remaining))
        yield


@contextmanager
def _kernel_lock(stream):
    if os.name == "nt":
        import msvcrt

        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise ControlBusyError("local_control_busy") from exc
        try:
            # Windows lets us lock byte zero before the file has contents.
            if os.fstat(stream.fileno()).st_size == 0:
                stream.write(b"0")
                stream.flush()
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ControlBusyError("local_control_busy") from exc
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
