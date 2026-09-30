"""Test-only isolation support for opt-in live end-to-end tests.

This module never downloads data, calls a provider, or starts a product runtime.
Live tests must configure the owning public entrypoint to use these run-local
directories, register every created file, and provide a read-only observer for
the protected pre/post state.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import stat
import tempfile
from typing import Any, Callable
import uuid


class IsolationError(RuntimeError):
    """Raised when a live test cannot prove safe ownership or cleanup."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        common = os.path.commonpath((str(path), str(parent)))
    except ValueError:
        return False
    return os.path.normcase(common) == os.path.normcase(str(parent))


def _is_link_or_reparse(path: Path) -> bool:
    """Recognize symlinks and Windows directory junctions/reparse points."""
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        if callable(is_junction) and is_junction():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        return bool(attributes & reparse_flag)
    except FileNotFoundError:
        return False


def _iter_regular_files(root: Path):
    """Walk without following symlinks, junctions, or other reparse points."""
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    if _is_link_or_reparse(path):
                        raise IsolationError(
                            f"run tree contains a link or reparse point: {path.name}"
                        )
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(path)
                    elif entry.is_file(follow_symlinks=False):
                        yield path
                    else:
                        raise IsolationError(f"run tree contains a special file: {path.name}")
        except OSError as exc:
            raise IsolationError(f"cannot safely inspect run directory {directory}") from exc


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise IsolationError("state observer must return finite JSON data") from exc


class LiveE2ESandbox:
    """Own one temporary live-test run and remove only hash-verified artifacts.

    `state_observer` should return a bounded, read-only snapshot of external
    protected state (for example repository status, configured user-profile
    files, production DB identity, and non-run process identities). Never put
    credentials or raw LLM responses in this snapshot.
    """

    DIRECTORY_NAMES = ("workspace", "sqlite", "downloads", "exchange", "logs")
    OWNER_FILE = ".run-owner.json"
    MANIFEST_FILE = "run-manifest.json"

    def __init__(self, *, base_dir: str | Path | None = None,
                 state_observer: Callable[[], Any] | None = None,
                 stop_timeout_seconds: float = 5.0):
        system_temp = Path(tempfile.gettempdir()).resolve(strict=True)
        requested_base = Path(base_dir) if base_dir is not None else system_temp
        self.base_dir = requested_base.resolve(strict=True)
        if not _path_is_within(self.base_dir, system_temp):
            raise IsolationError("live sandbox base must be inside the system temporary root")
        if not self.base_dir.is_dir():
            raise IsolationError("live sandbox base must be a directory")

        self._state_observer = state_observer or (lambda: {})
        self._before_state = _canonical_json(self._state_observer())
        self._stop_timeout_seconds = stop_timeout_seconds
        self.run_id = uuid.uuid4().hex
        self.owner_id = secrets.token_hex(16)
        self.root = Path(tempfile.mkdtemp(
            prefix=f"invest-quick-scan-live-{self.run_id}-", dir=self.base_dir
        )).resolve(strict=True)
        if self.root.parent != self.base_dir:
            raise IsolationError("temporary run root escaped its configured base")
        root_stat = self.root.stat()
        self._root_identity = (root_stat.st_dev, root_stat.st_ino)

        self.paths = {name: self.root / name for name in self.DIRECTORY_NAMES}
        for directory in self.paths.values():
            directory.mkdir()

        self._owner_path = self.root / self.OWNER_FILE
        self._manifest_path = self.root / self.MANIFEST_FILE
        self._owner_bytes = _canonical_json({
            "schema_version": "1.0.0",
            "run_id": self.run_id,
            "owner_id": self.owner_id,
        }) + b"\n"
        with self._owner_path.open("xb") as owner_stream:
            owner_stream.write(self._owner_bytes)
            owner_stream.flush()
            os.fsync(owner_stream.fileno())
        self._manifest: dict[str, Any] = {
            "schema_version": "1.0.0",
            "run_id": self.run_id,
            "owner_id": self.owner_id,
            "root": str(self.root),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": [],
            "processes": [],
        }
        self._process_handles: list[tuple[subprocess.Popen[Any], str]] = []
        self._cleaned = False
        self._write_manifest()

    def path(self, name: str) -> Path:
        """Return one of the dedicated run-local component directories."""
        try:
            return self.paths[name]
        except KeyError as exc:
            raise IsolationError(f"unknown sandbox directory: {name}") from exc

    def assert_run_path(self, path: str | Path) -> Path:
        """Resolve a configured write path and fail if it can escape this run."""
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        lexical = Path(os.path.abspath(candidate))
        if not _path_is_within(lexical, self.root):
            raise IsolationError("configured write path is outside this run")
        resolved = lexical.resolve(strict=False)
        if not _path_is_within(resolved, self.root):
            raise IsolationError("configured write path resolves outside this run")
        if not any(_path_is_within(resolved, directory.resolve(strict=True))
                   for directory in self.paths.values()):
            raise IsolationError("configured write path must use a dedicated run subdirectory")
        current = lexical
        while current != self.root:
            if _is_link_or_reparse(current):
                raise IsolationError("configured write path contains a link or reparse point")
            current = current.parent
        return resolved

    def register_artifact(self, path: str | Path, *, action: str,
                          component_owner: str) -> dict[str, Any]:
        """Register one completed file before cleanup may remove it."""
        if not action.strip() or not component_owner.strip():
            raise IsolationError("artifact action and component owner are required")
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = Path(os.path.abspath(candidate))
        if not _path_is_within(candidate, self.root):
            raise IsolationError("artifact is outside this run")
        if candidate in (self._owner_path, self._manifest_path):
            raise IsolationError("sandbox control files cannot be registered as artifacts")
        resolved = candidate.resolve(strict=True)
        if not _path_is_within(resolved, self.root):
            raise IsolationError("artifact resolves outside this run")
        if not any(_path_is_within(resolved, directory.resolve(strict=True))
                   for directory in self.paths.values()):
            raise IsolationError("artifact is outside the dedicated run subdirectories")
        current = candidate
        while current != self.root:
            if _is_link_or_reparse(current):
                raise IsolationError("artifact path contains a link or reparse point")
            current = current.parent
        if not resolved.is_file():
            raise IsolationError("only regular files can be registered as artifacts")
        if resolved.stat().st_nlink > 1:
            raise IsolationError("hard-linked files are unsafe to register as run artifacts")

        relative = resolved.relative_to(self.root).as_posix()
        if any(item["path"] == relative for item in self._manifest["artifacts"]):
            raise IsolationError("artifact path was already registered")
        content = resolved.read_bytes()
        record = {
            "path": relative,
            "action": action,
            "component_owner": component_owner,
            "run_id": self.run_id,
            "owner_id": self.owner_id,
            "size_bytes": len(content),
            "sha256": _sha256(content),
        }
        self._manifest["artifacts"].append(record)
        try:
            self._write_manifest()
        except Exception:
            self._manifest["artifacts"].pop()
            raise
        return dict(record)

    def register_existing_files(self, *, action: str,
                                component_owner: str) -> list[dict[str, Any]]:
        """Register all files left under run directories after an API returns.

        Call this after closing SQLite handles and stopping workers. Symlinks,
        unknown root files, or files outside the five declared areas fail closed.
        """
        registered: list[dict[str, Any]] = []
        known = {item["path"] for item in self._manifest["artifacts"]}
        for top in self.paths.values():
            for candidate in _iter_regular_files(top):
                relative = candidate.relative_to(self.root).as_posix()
                if relative in known:
                    continue
                registered.append(self.register_artifact(
                    candidate, action=action, component_owner=component_owner
                ))
                known.add(relative)
        return registered

    def start_process(self, args: list[str] | tuple[str, ...], *,
                      component_owner: str, cwd: str | Path | None = None,
                      env: dict[str, str] | None = None,
                      stdout: int | Any = subprocess.DEVNULL,
                      stderr: int | Any = subprocess.DEVNULL) -> subprocess.Popen[Any]:
        """Start and own a foreground child; cleanup never targets a PID alone.

        Existing processes cannot be registered. Use an owner-provided adapter
        for a managed process tree; do not attach or terminate pre-existing PIDs.
        """
        if not component_owner.strip():
            raise IsolationError("component owner is required for a test process")
        if (not isinstance(args, (list, tuple)) or not args
                or not all(isinstance(part, str) for part in args)):
            raise IsolationError("test processes require a non-empty argv sequence")
        process_cwd = self.assert_run_path(
            cwd if cwd is not None else self.path("workspace")
        )
        if not process_cwd.is_dir():
            raise IsolationError("test process cwd must be an existing run-local directory")
        process = subprocess.Popen(
            args, cwd=process_cwd, env=env, stdin=subprocess.DEVNULL,
            stdout=stdout, stderr=stderr,
        )
        try:
            self._record_owned_process(process, component_owner=component_owner)
        except Exception:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=self._stop_timeout_seconds)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=self._stop_timeout_seconds)
            raise
        return process

    def _record_owned_process(self, process: subprocess.Popen[Any], *,
                              component_owner: str) -> None:
        if process.pid is None:
            raise IsolationError("started child has no process identity")
        if any(existing is process for existing, _ in self._process_handles):
            raise IsolationError("process handle was already registered")
        args_digest = _sha256(repr(process.args).encode("utf-8", errors="replace"))
        process_record = {
            "pid": process.pid,
            "component_owner": component_owner,
            "run_id": self.run_id,
            "owner_id": self.owner_id,
            "args_sha256": args_digest,
        }
        self._manifest["processes"].append(process_record)
        try:
            self._write_manifest()
        except Exception:
            self._manifest["processes"].pop()
            raise
        self._process_handles.append((process, component_owner))

    def _write_manifest(self) -> None:
        self._verify_root_identity()
        self._verify_owner_file()
        manifest_present = self._manifest_path.exists() or _is_link_or_reparse(
            self._manifest_path
        )
        if hasattr(self, "_manifest_sha256"):
            if not manifest_present:
                raise IsolationError("run manifest disappeared before update")
            self._verify_regular_control_file(self._manifest_path)
            if _sha256(self._manifest_path.read_bytes()) != self._manifest_sha256:
                raise IsolationError("run manifest changed before update")
        elif manifest_present:
            raise IsolationError("unexpected manifest exists during run initialization")

        payload = json.dumps(self._manifest, ensure_ascii=False, sort_keys=True,
                             indent=2, allow_nan=False).encode("utf-8") + b"\n"
        fd, pending_name = tempfile.mkstemp(prefix=".manifest-pending-", dir=self.root)
        pending_path = Path(pending_name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            self._verify_root_identity()
            self._verify_owner_file()
            if hasattr(self, "_manifest_sha256"):
                self._verify_regular_control_file(self._manifest_path)
                if _sha256(self._manifest_path.read_bytes()) != self._manifest_sha256:
                    raise IsolationError("run manifest changed during update")
            os.replace(pending_path, self._manifest_path)
        except Exception:
            if pending_path.exists() and not _is_link_or_reparse(pending_path):
                pending_path.unlink()
            raise
        self._manifest_sha256 = _sha256(payload)

    def _verify_root_identity(self) -> None:
        if (_is_link_or_reparse(self.root)
                or self.root.resolve(strict=True) != self.root
                or self.root.parent != self.base_dir):
            raise IsolationError("run root identity changed")
        root_stat = self.root.stat()
        if (root_stat.st_dev, root_stat.st_ino) != self._root_identity:
            raise IsolationError("run root file identity changed")

    @staticmethod
    def _verify_regular_control_file(path: Path) -> None:
        if _is_link_or_reparse(path):
            raise IsolationError("sandbox control file is a link or reparse point")
        file_stat = path.stat()
        if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
            raise IsolationError("sandbox control file is not a unique regular file")

    def _verify_owner_file(self) -> None:
        self._verify_regular_control_file(self._owner_path)
        if self._owner_path.read_bytes() != self._owner_bytes:
            raise IsolationError("sandbox owner marker changed")

    def _verify_control_files(self) -> None:
        self._verify_root_identity()
        if self.root.parent != self.base_dir or not self.root.name.startswith(
                f"invest-quick-scan-live-{self.run_id}-"):
            raise IsolationError("run root does not match its recorded owner and run id")
        self._verify_owner_file()
        self._verify_regular_control_file(self._manifest_path)
        manifest_bytes = self._manifest_path.read_bytes()
        if _sha256(manifest_bytes) != self._manifest_sha256:
            raise IsolationError("run manifest changed after the harness wrote it")
        stored = json.loads(manifest_bytes.decode("utf-8"))
        if (stored.get("run_id") != self.run_id
                or stored.get("owner_id") != self.owner_id
                or Path(stored.get("root", "")).resolve(strict=True) != self.root):
            raise IsolationError("run manifest identity does not match this sandbox")

    def _stop_owned_processes(self) -> None:
        for process, _component_owner in self._process_handles:
            if process.poll() is not None:
                continue
            process.terminate()
            try:
                process.wait(timeout=self._stop_timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=self._stop_timeout_seconds)
                except subprocess.TimeoutExpired as exc:
                    raise IsolationError(
                        f"could not stop registered run process pid={process.pid}"
                    ) from exc

    def _verify_external_state(self) -> None:
        after = _canonical_json(self._state_observer())
        if after != self._before_state:
            raise IsolationError(
                "protected external state drifted during the live test; run directory preserved"
            )

    def _verify_inventory(self) -> list[Path]:
        self._verify_control_files()
        artifacts = self._manifest.get("artifacts")
        if not isinstance(artifacts, list):
            raise IsolationError("run manifest artifact inventory is invalid")
        registered: dict[str, dict[str, Any]] = {}
        for record in artifacts:
            if (not isinstance(record, dict)
                    or record.get("run_id") != self.run_id
                    or record.get("owner_id") != self.owner_id):
                raise IsolationError("artifact owner or run id does not match")
            relative = record.get("path")
            if not isinstance(relative, str) or not relative or relative in registered:
                raise IsolationError("artifact path is missing or duplicated")
            candidate = self.root / Path(relative)
            if not _path_is_within(Path(os.path.abspath(candidate)), self.root):
                raise IsolationError("artifact inventory path escapes the run")
            current = candidate
            while current != self.root:
                if _is_link_or_reparse(current):
                    raise IsolationError("artifact inventory contains a link or reparse point")
                current = current.parent
            resolved = candidate.resolve(strict=True)
            if not _path_is_within(resolved, self.root):
                raise IsolationError("artifact inventory resolves outside the run")
            if not any(_path_is_within(resolved, directory.resolve(strict=True))
                       for directory in self.paths.values()):
                raise IsolationError("artifact inventory escapes the dedicated run areas")
            content = resolved.read_bytes()
            if (not resolved.is_file()
                    or resolved.stat().st_nlink > 1
                    or len(content) != record.get("size_bytes")
                    or _sha256(content) != record.get("sha256")):
                raise IsolationError(
                    f"artifact changed since registration: {relative}; run directory preserved"
                )
            registered[relative] = record

        actual_files: set[str] = set()
        for candidate in _iter_regular_files(self.root):
            relative = candidate.relative_to(self.root).as_posix()
            if relative in (self.OWNER_FILE, self.MANIFEST_FILE):
                continue
            actual_files.add(relative)
        if actual_files != set(registered):
            extras = sorted(actual_files - set(registered))
            missing = sorted(set(registered) - actual_files)
            raise IsolationError(
                f"run artifact inventory mismatch; unregistered={extras}, missing={missing}; "
                "run directory preserved"
            )
        return [self.root / Path(relative) for relative in sorted(registered)]

    def _stage_all_artifacts(self, artifacts: list[Path]) -> list[tuple[Path, Path]]:
        """Prove every file can move before deleting any run artifact."""
        staged_names = [artifact.with_name(
            f".cleanup-{self.run_id}-{index:04d}-{artifact.name}"
        ) for index, artifact in enumerate(artifacts)]
        if any(path.exists() or _is_link_or_reparse(path) for path in staged_names):
            raise IsolationError("cleanup staging path already exists")

        moved: list[tuple[Path, Path]] = []
        try:
            for original, staged_path in zip(artifacts, staged_names):
                os.replace(original, staged_path)
                moved.append((original, staged_path))
        except OSError as exc:
            rollback_errors = []
            for original, staged_path in reversed(moved):
                try:
                    os.replace(staged_path, original)
                except OSError as rollback_error:
                    rollback_errors.append(f"{staged_path.name}: {rollback_error}")
            if rollback_errors:
                raise IsolationError(
                    "cleanup preflight failed and artifact rollback was incomplete; "
                    f"evidence preserved under {self.root}: {rollback_errors}"
                ) from exc
            raise IsolationError(
                "cleanup preflight could not move every artifact; no files were deleted "
                f"and the run directory is preserved under {self.root}"
            ) from exc

        for original, staged_path in moved:
            relative = original.relative_to(self.root).as_posix()
            record = next(item for item in self._manifest["artifacts"]
                          if item["path"] == relative)
            content = staged_path.read_bytes()
            if (not staged_path.is_file()
                    or _is_link_or_reparse(staged_path)
                    or staged_path.stat().st_nlink != 1
                    or len(content) != record["size_bytes"]
                    or _sha256(content) != record["sha256"]):
                rollback_errors = []
                for previous_original, previous_staged in reversed(moved):
                    try:
                        if previous_staged.exists() or _is_link_or_reparse(previous_staged):
                            os.replace(previous_staged, previous_original)
                    except OSError as rollback_error:
                        rollback_errors.append(
                            f"{previous_staged.name}: {rollback_error}"
                        )
                if rollback_errors:
                    raise IsolationError(
                        "staged artifact verification failed and rollback was incomplete; "
                        f"evidence preserved under {self.root}: {rollback_errors}"
                    )
                raise IsolationError(
                    "staged artifact changed during cleanup preflight; no files were deleted"
                )
        return moved

    def cleanup(self) -> None:
        """Stop owned children, verify zero external drift, then unlink exact files."""
        if self._cleaned:
            return
        self._stop_owned_processes()
        artifacts = self._verify_inventory()
        # Stage all files first; an open SQLite/download handle fails here on
        # Windows before any log or result file is removed. On failure, restore
        # every prior path and leave the full run root available for diagnosis.
        staged = self._stage_all_artifacts(artifacts)
        try:
            # Observe protected state after the run files have been staged but
            # before deleting them. If state drifted, put every artifact back
            # so the complete run remains available for diagnosis.
            self._verify_external_state()
        except Exception as exc:
            rollback_errors = []
            for original, staged_path in reversed(staged):
                try:
                    os.replace(staged_path, original)
                except OSError as rollback_error:
                    rollback_errors.append(f"{staged_path.name}: {rollback_error}")
            if rollback_errors:
                raise IsolationError(
                    "protected external state check failed and artifact rollback was "
                    f"incomplete; evidence preserved under {self.root}: {rollback_errors}"
                ) from exc
            raise
        for _original, staged_path in staged:
            staged_path.unlink()
        for current, dirnames, _filenames in os.walk(self.root, topdown=False,
                                                       followlinks=False):
            current_path = Path(current)
            for directory in dirnames:
                (current_path / directory).rmdir()
        self._manifest_path.unlink()
        self._owner_path.unlink()
        self.root.rmdir()
        self._cleaned = True

    def __enter__(self) -> "LiveE2ESandbox":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        try:
            self.cleanup()
        except Exception as cleanup_error:
            if exc_value is None:
                raise
            raise IsolationError(
                f"live test failed with {type(exc_value).__name__}; "
                f"cleanup also failed: {cleanup_error}; evidence kept at {self.root}"
            ) from cleanup_error
        return False
