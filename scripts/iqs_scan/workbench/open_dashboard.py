"""Start the IQS-owned local workbench with the existing UI as static files."""
from __future__ import annotations

from iqs_scan import REPO_ROOT

import argparse
import json
import mimetypes
from pathlib import Path, PurePosixPath
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

ROOT = REPO_ROOT
GENERATED = {"bank", "versions", "roster", "answers", "manifest"}
STATIC_SUFFIXES = {".html", ".js", ".mjs", ".css", ".json", ".svg", ".png", ".ico",
                   ".woff2", ".txt", ".map"}
WINDOWS_DEVICE_NAMES = {"CON", "NUL", "AUX", "PRN", *(f"COM{i}" for i in range(1, 10)),
                        *(f"LPT{i}" for i in range(1, 10))}


def _load_config(path: Path | None, data_root: Path, validate_config):
    if path is None:
        path = data_root / "config" / "dashboard.local.json"
    if not path.is_file():
        return validate_config({}, data_root)
    if path.stat().st_size > 1_048_576:
        raise ValueError("dashboard configuration exceeds the read limit")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate configuration key")
            result[key] = value
        return result

    raw = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=pairs,
                     parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite configuration")))
    return validate_config(raw, data_root)


def _load_runtime():
    from .dashboard_http import product_handler
    from .dashboard_service import DashboardService, validate_config
    from .workbench_snapshot import build_workbench_snapshot, load_workbench_snapshot, write_workbench_snapshot
    return product_handler, DashboardService, validate_config, build_workbench_snapshot, load_workbench_snapshot, write_workbench_snapshot


def _handler(static_root: Path, snapshot_path: Path, load_snapshot):
    root = static_root.resolve()
    index = root / "index.html"

    class StaticUIHandler(BaseHTTPRequestHandler):
        server_version = "IQSLocal/1.0"

        def log_message(self, _format, *_args):
            return

        def _send_static(self, status: int, raw: bytes, content_type: str, *, no_store=False, head=False):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store" if no_store else "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if not head:
                self.wfile.write(raw)

        def _reply_json(self, payload, *, head=False):
            raw = (json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
            self._send_static(200, raw, "application/json; charset=utf-8", no_store=True, head=head)

        def _generated(self, url_path: str, *, head=False):
            if url_path == "/generated/snapshot.json":
                self._reply_json(load_snapshot(snapshot_path), head=head)
                return True
            prefix = "/generated/"
            name = url_path[len(prefix):-5] if url_path.startswith(prefix) and url_path.endswith(".json") else ""
            if name in GENERATED:
                snapshot = load_snapshot(snapshot_path)
                payload = snapshot.get(name)
                if payload is None:
                    payload = {"section": name, "availability": snapshot["availability"].get(name, "unavailable"),
                               "data": None, "warnings": [warning for warning in snapshot["warnings"]
                                                            if warning.get("section") in {name, "snapshot"}]}
                self._reply_json(payload, head=head)
                return True
            if url_path.startswith(prefix):
                self._send_static(404, b"Not found\n", "text/plain; charset=utf-8", no_store=True, head=head)
                return True
            return False

        def _static_file(self, url_path: str, *, head=False):
            if url_path == "/":
                candidate = index
            else:
                if "\\" in url_path or ":" in url_path or "\0" in url_path:
                    self._send_static(404, b"Not found\n", "text/plain; charset=utf-8", head=head)
                    return
                decoded = url_path
                parts = PurePosixPath(decoded.lstrip("/")).parts
                if (not parts or any(part in {"", ".", ".."} or part.startswith(".") for part in parts)
                        or any(part.split(".", 1)[0].upper() in WINDOWS_DEVICE_NAMES for part in parts)):
                    self._send_static(404, b"Not found\n", "text/plain; charset=utf-8", head=head)
                    return
                candidate = root.joinpath(*parts)
            try:
                resolved = candidate.resolve(strict=True)
                if (not resolved.is_relative_to(root) or not resolved.is_file()
                        or resolved.suffix.lower() not in STATIC_SUFFIXES
                        or candidate.is_symlink()
                        or bool(getattr(candidate.stat(), "st_file_attributes", 0) & 0x400)):
                    raise OSError("outside static root or not a file")
                raw = resolved.read_bytes()
            except (OSError, RuntimeError, ValueError, UnicodeError):
                self._send_static(404, b"Not found\n", "text/plain; charset=utf-8", head=head)
                return
            content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type in {"application/javascript", "application/json", "image/svg+xml"}:
                content_type += "; charset=utf-8"
            self._send_static(200, raw, content_type, head=head)

        def _serve(self, *, head=False):
            try:
                url_path = unquote(urlsplit(self.path).path, errors="strict")
                if self._generated(url_path, head=head):
                    return
                self._static_file(url_path, head=head)
            except (ValueError, UnicodeError):
                self._send_static(400, b"Invalid path\n", "text/plain; charset=utf-8", no_store=True, head=head)

        def do_GET(self):
            self._serve()

        def do_HEAD(self):
            self._serve(head=True)

    return StaticUIHandler


def main(argv=None):
    parser = argparse.ArgumentParser(description="本机公司快扫工作台；浏览不调用模型，启动不运行测试。")
    parser.add_argument("--ui-root", type=Path, default=ROOT.parent / "iqs-question-bank-ui-lab",
                        help="UI源码仓，只读取 src/app 静态文件")
    parser.add_argument("--data-root", type=Path, default=ROOT, help="IQS代码与题库根目录")
    parser.add_argument("--port", type=int, default=8765, help="本机端口；0 表示由系统分配")
    parser.add_argument("--no-refresh", action="store_true", help="仅读取已有展示快照，不重新读取owner或写快照")
    parser.add_argument("--dashboard-config", type=Path, help="本机owner与执行配置；默认config/dashboard.local.json")
    parser.add_argument("--plan", action="store_true", help="显示启动范围，不读取owner、不写快照、不启动服务")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")

    ui_root, data_root = args.ui_root.resolve(), args.data_root.resolve()
    static_root = ui_root / "src" / "app"
    if not (static_root / "index.html").is_file():
        parser.exit(2, "UI static app is missing; provide --ui-root with src/app/index.html.\n")
    if not data_root.is_dir():
        parser.exit(2, "Data root is missing; provide --data-root.\n")

    product_handler, DashboardService, validate_config, build_snapshot, load_snapshot, write_snapshot = _load_runtime()
    config_path = args.dashboard_config.resolve() if args.dashboard_config else data_root / "config" / "dashboard.local.json"
    try:
        config = _load_config(args.dashboard_config.resolve() if args.dashboard_config else None,
                              data_root, validate_config)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(2, f"Dashboard configuration is invalid: {error}\n")
    state_root = Path(config["state_root"]).resolve()
    snapshot_path = state_root / "workbench" / "snapshot.json"
    if args.plan:
        print(json.dumps({"ui_static_root": str(static_root), "data_root": str(data_root),
                          "snapshot_path": str(snapshot_path), "refresh": False,
                          "no_refresh_requested": args.no_refresh, "tests": False,
                          "model_calls": False, "owner_reads": False, "writes": False,
                          "listener": False}, ensure_ascii=False))
        return 0

    try:
        service = DashboardService(root=data_root, config_path=config_path)
        if not args.no_refresh:
            snapshot = build_snapshot(data_root, service.config)
            write_snapshot(snapshot_path, snapshot)
    except Exception as error:
        sys.stderr.write(f"Cannot build the read-only dashboard snapshot: {getattr(error, 'code', 'snapshot_export_failed')}\n")
        return 2
    handler = product_handler(_handler(static_root, snapshot_path, load_snapshot), service)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as error:
        sys.stderr.write(f"Cannot bind local dashboard: {error}\n")
        return 2
    server.daemon_threads = True
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(json.dumps({"status": "ready", "url": url, "port": server.server_address[1],
                      "snapshot": str(snapshot_path), "model_calls": 0, "network_calls": 0,
                      "refreshed": not args.no_refresh}, ensure_ascii=False), flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        return 130
    finally:
        server.server_close()
    return 0
