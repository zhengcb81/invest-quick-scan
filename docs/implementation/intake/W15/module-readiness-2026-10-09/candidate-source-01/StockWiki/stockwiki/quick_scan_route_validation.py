"""Typed IQS public-CLI boundary; no cross-repository Python imports or LLMs."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Protocol

from stockwiki.quick_scan_import import parse_package

PROTOCOL = "iqs.route_store_validation/1.0.0"
MAX_BYTES = 8 * 1024 * 1024


class RouteStoreError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def read_json(raw: bytes) -> dict[str, Any]:
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise RouteStoreError("route_input_invalid")
    try:
        return parse_package(raw.decode("utf-8-sig"))
    except (ValueError, UnicodeError) as exc:
        raise RouteStoreError("route_json_invalid") from exc


class RouteValidator(Protocol):
    def validate(
        self,
        route_raw: bytes,
        manifest_raw: bytes,
        *,
        expected_decision_id: str,
        validation_mode: str = "history",
        now_utc: str | None = None,
    ) -> dict[str, Any]: ...


class IqsRouteValidator:
    """Configured first-party command is the trust boundary, not an incoming DTO.

    code_root/release_root are owner configuration, never model output. Input
    JSON contains data only. Temporary bytes are removed on success/refusal.
    This offline check does not authenticate company evidence or approve fees.
    """

    def __init__(
        self,
        code_root: Path,
        *,
        runs_dir: Path,
        release_root: Path | None = None,
        timeout: float = 60,
        process_env: dict[str, str] | None = None,
    ) -> None:
        self.code_root = Path(code_root).resolve()
        self.release_root = Path(release_root or code_root).resolve()
        self.runs_dir = Path(runs_dir).resolve()
        self.timeout = timeout
        self.process_env = process_env

    def validate(
        self,
        route_raw: bytes,
        manifest_raw: bytes,
        *,
        expected_decision_id: str,
        validation_mode: str = "history",
        now_utc: str | None = None,
    ) -> dict[str, Any]:
        read_json(route_raw)
        read_json(manifest_raw)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        script = self.code_root / "scripts/route_store_handoff.py"
        if not script.is_file():
            raise RouteStoreError("route_validator_unavailable")
        env = (
            self.process_env
            if self.process_env is not None
            else {
                k: v
                for k, v in os.environ.items()
                if k.upper()
                in {
                    "SYSTEMROOT",
                    "WINDIR",
                    "PATH",
                    "PATHEXT",
                    "COMSPEC",
                    "USERPROFILE",
                    "APPDATA",
                    "LOCALAPPDATA",
                    "SYSTEMDRIVE",
                }
            }
        )
        env = dict(env, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        try:
            with tempfile.TemporaryDirectory(prefix="iqs-route-", dir=self.runs_dir) as directory:
                base = Path(directory)
                route_path, manifest_path = base / "route.json", base / "manifest.json"
                route_path.write_bytes(route_raw)
                manifest_path.write_bytes(manifest_raw)
                command = [
                    sys.executable,
                    "-B",
                    "-X",
                    "utf8",
                    str(script),
                    "--root",
                    str(self.release_root),
                    "--route",
                    str(route_path),
                    "--manifest",
                    str(manifest_path),
                    "--expected-decision-id",
                    expected_decision_id,
                    "--validation-mode",
                    validation_mode,
                ]
                if now_utc is not None:
                    command.extend(["--now-utc", now_utc])
                result = subprocess.run(
                    command,
                    cwd=self.code_root,
                    env=env,
                    capture_output=True,
                    timeout=self.timeout,
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
        except subprocess.TimeoutExpired as exc:
            raise RouteStoreError("route_validator_timeout") from exc
        except OSError as exc:
            raise RouteStoreError("route_validator_unavailable") from exc
        try:
            dto = read_json(result.stdout)
        except RouteStoreError as exc:
            raise RouteStoreError("route_validator_output_invalid") from exc
        if dto.get("protocol") != PROTOCOL:
            raise RouteStoreError("route_validator_protocol_invalid")
        if result.returncode == 2 and dto.get("status") == "rejected":
            raise RouteStoreError(str(dto.get("error_code", "route_validator_rejected")))
        if (
            result.returncode != 0
            or dto.get("status") != "validated"
            or dto.get("schema_version") != "1.0.0"
            or dto.get("expected_decision_id") != expected_decision_id
            or dto.get("decision_id") != expected_decision_id
            or dto.get("validation_mode") != validation_mode
            or dto.get("execution_checked_at") != now_utc
            or dto.get("new_execution_authorized") is not (validation_mode == "execution")
            or dto.get("model_API_requests") != 0
            or dto.get("database_writes") != 0
            or dto.get("route_raw_sha256") != hashlib.sha256(route_raw).hexdigest()
            or dto.get("manifest_raw_sha256") != hashlib.sha256(manifest_raw).hexdigest()
        ):
            raise RouteStoreError("route_validator_output_invalid")
        return dto
