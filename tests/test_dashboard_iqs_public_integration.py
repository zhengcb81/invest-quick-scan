"""Dashboard m6/m8 adapters over the real IQS public HTTP and CLI faces."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import sys
import subprocess
import threading
import time
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DASHBOARD = ROOT.parent / "investment-dashboard"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "tests"))

from dashboard_http import product_handler
from dashboard_service import DashboardService
from test_dashboard_company_result import Owner as AssessmentOwner, RESULT_SNAPSHOT
from test_dashboard_entity_iqs_link import ENTITY_PAYLOAD
from test_owner_job_cli import COMMAND as IQS_COMMAND
from test_owner_job_cli import Execution as FakeExecution

OVERLAP_COMMAND = {**IQS_COMMAND, "command_id": "run-" + "f" * 32,
                   "idempotency_key": "dash-idem-overlap"}


def _clear_test_credentials(monkeypatch):
    markers = ("API_KEY", "TOKEN", "SECRET", "PASSWORD")
    for name in tuple(os.environ):
        if any(marker in name.upper() for marker in markers):
            monkeypatch.delenv(name, raising=False)
    assert not any(any(marker in name.upper() for marker in markers) for name in os.environ)


def _build_dashboard_web(source: Path, target_root: Path, tmp_path: Path) -> Path:
    """Build current frontend source into test-owned storage, never shared dist."""
    npm = shutil.which("npm")
    if not npm:
        pytest.skip("npm is required to build the current Dashboard frontend")
    web_root = source / "apps" / "web"
    installed = Path(os.environ.get("IQS_DASHBOARD_TEST_WEB_ROOT", web_root)).resolve()
    if not (installed / "node_modules").is_dir():
        pytest.skip("Dashboard frontend dependencies are not installed")
    for manifest in ("package.json", "package-lock.json"):
        assert (installed / manifest).read_bytes() == (web_root / manifest).read_bytes(), manifest
    dist = target_root / "apps" / "web" / "dist"
    build_env = dict(os.environ, TEMP=str(tmp_path), TMP=str(tmp_path))
    result = subprocess.run(
        [npm, "run", "build", "--", "--outDir", str(dist), "--emptyOutDir"],
        cwd=installed, env=build_env, capture_output=True, text=True, encoding="utf-8", timeout=240,
    )
    assert result.returncode == 0, result.stdout[-6000:] + "\n" + result.stderr[-6000:]
    assert (dist / "index.html").is_file(), "build must emit a temporary frontend index"
    return dist


class Static(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"static")

    def log_message(self, *_args):
        return


class Identity:
    async def resolve_subject(self, entity_id, listing_id=None):
        return {"entity_id": entity_id, "listing_id": listing_id,
                "analysis_subject_id": None, "resolution_status": "resolved",
                "display_name": "Isolated Dashboard Test Company"}


class Owner(AssessmentOwner):
    def entity(self, entity_id):
        return {"protocol": "stockwiki_w09_read_primitives",
                "projection_version": "quick_scan_profiles/1.1.0",
                "entity": {**ENTITY_PAYLOAD["entity"], "entity_id": entity_id},
                "groups": []}


def _dashboard_modules():
    if not (DASHBOARD / "backend" / "dashboard" / "adapters" / "iqs" / "quickscan.py").is_file():
        pytest.skip("Dashboard source is unavailable")
    sys.path.insert(0, str(DASHBOARD))
    from backend.dashboard.adapters.iqs.quickscan import IqsQuickScanAdapter
    from backend.dashboard.adapters.m8_owner_jobs.iqs_job import IqsJobAdapter
    from backend.dashboard.adapters.transport import CliResult, JsonHttpTransport
    from backend.dashboard.transport.http import create_app
    return IqsQuickScanAdapter, IqsJobAdapter, CliResult, JsonHttpTransport, create_app


def test_dashboard_m6_m8_use_live_iqs_http_cli_and_read_after_lost_submit(tmp_path, monkeypatch, request):
    _clear_test_credentials(monkeypatch)
    IqsQuickScanAdapter, IqsJobAdapter, CliResult, JsonHttpTransport, create_app = _dashboard_modules()
    config_path = tmp_path / "dashboard.json"
    config_path.write_text(json.dumps({"workspace_root": "", "workspace_kind": "unconfigured",
                                       "state_root": str(tmp_path / "iqs-state")}), encoding="utf-8")
    iq_service = DashboardService(root=ROOT, config_path=config_path,
                                   owner_factory=Owner, execution_factory=FakeExecution)
    assert Path(iq_service.config["state_root"]) == tmp_path / "iqs-state"
    iqs_requests = []
    original_dispatch = iq_service.dispatch

    def trace_iqs_request(method, target, body=None):
        iqs_requests.append((method, target))
        return original_dispatch(method, target, body)

    iq_service.dispatch = trace_iqs_request

    class Static(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"static")

        def log_message(self, *_args):
            return

    cleanup = ExitStack()
    request.addfinalizer(cleanup.close)
    server = ThreadingHTTPServer(("127.0.0.1", 0), product_handler(Static, iq_service))
    cleanup.callback(server.server_close)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def stop_iqs():
        server.shutdown()
        thread.join(timeout=5)
        assert not thread.is_alive()

    cleanup.callback(stop_iqs)
    FakeExecution.started.clear()
    FakeExecution.controls.clear()
    FakeExecution.counter = 0
    FakeExecution.runs.clear()
    try:
        origin = f"http://127.0.0.1:{server.server_address[1]}"
        quick_scan = IqsQuickScanAdapter(JsonHttpTransport(origin, owner="invest-quick-scan"))
        job_adapter = IqsJobAdapter(python=sys.executable, root=ROOT, origin=origin, timeout_seconds=20)
        dashboard = create_app({"identity": Identity(), "quick_scan": quick_scan,
                                "jobs": {"invest-quick-scan": job_adapter}},
                               tmp_path / "dashboard-data", allow_test_origin=True)

        try:
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("FastAPI TestClient dependencies are unavailable")

        with TestClient(dashboard) as client:
            m6 = client.get("/api/v1/companies/ENT_A/quick-scan")
            assert m6.status_code == 200, m6.text
            assert m6.json()["latest_formal"]["observation_id"] == RESULT_SNAPSHOT["result_id"]

            import backend.dashboard.adapters.m8_owner_jobs.iqs_job as iqs_job
            real_run_cli = iqs_job.run_cli
            cli_operations = []
            lost_submit_response = {"pending": True}

            def lose_one_successful_submit_response(owner, argv, **kwargs):
                operation = argv[argv.index("--operation") + 1]
                assert argv[argv.index("--origin") + 1] == origin
                assert argv[argv.index("--origin") + 1] == origin
                cli_operations.append(operation)
                result = real_run_cli(owner, argv, **kwargs)
                if operation == "submit" and lost_submit_response.pop("pending", False):
                    assert result.exit_code == 0, result.stderr.decode("utf-8", "replace")
                    return CliResult(stdout=b"", stderr=b"simulated response lost after owner accepted command", exit_code=1)
                return result

            monkeypatch.setattr(iqs_job, "run_cli", lose_one_successful_submit_response)
            headers = {"Origin": "http://testserver", "X-Dashboard-CSRF": dashboard.state.csrf_token}
            submitted = client.post("/api/v1/commands", json=OVERLAP_COMMAND, headers=headers)
            assert submitted.status_code == 503, submitted.text
            assert submitted.json()["retryable"] is True
            assert len(FakeExecution.started) == 1
            assert len(FakeExecution.runs) == 1

            # Command IDs can match the owner-job grammar. Recovery must use
            # the exact command ledger rather than accepting an "unknown" job.
            recovered = client.get(f"/api/v1/jobs/{OVERLAP_COMMAND['command_id']}")
            assert recovered.status_code == 200, (recovered.text, cli_operations,
                                                  FakeExecution.started, iqs_requests)
            assert recovered.json()["command_id"] == OVERLAP_COMMAND["command_id"]
            assert recovered.json()["owner_job_id"].startswith("run-")
            assert recovered.json()["status"] == "running", recovered.json()

        assert cli_operations == ["submit", "get-command"]
        assert len(FakeExecution.started) == 1
    finally:
        cleanup.close()


def test_dashboard_m6_m8_real_browser_recovers_generated_command_id_without_resubmit(tmp_path, monkeypatch, request):
    """The source-built Dashboard UI reads m6 and recovers m8 through public IQS faces."""
    _clear_test_credentials(monkeypatch)
    pytest.importorskip("playwright.sync_api")
    pytest.importorskip("uvicorn")
    IqsQuickScanAdapter, IqsJobAdapter, CliResult, JsonHttpTransport, create_app = _dashboard_modules()
    from playwright.sync_api import sync_playwright
    import uvicorn
    dashboard_http = __import__("backend.dashboard.transport.http", fromlist=["ROOT"])
    dashboard_web_root = tmp_path / "dashboard-web-root"
    _build_dashboard_web(DASHBOARD, dashboard_web_root, tmp_path)
    monkeypatch.setattr(dashboard_http, "ROOT", dashboard_web_root)

    cleanup = ExitStack()
    request.addfinalizer(cleanup.close)

    listing_id = "LST_1"
    config_path = tmp_path / "dashboard.json"
    config_path.write_text(json.dumps({"workspace_root": "", "workspace_kind": "unconfigured",
                                       "state_root": str(tmp_path / "iqs-state")}), encoding="utf-8")
    iq_service = DashboardService(root=ROOT, config_path=config_path,
                                   owner_factory=Owner, execution_factory=FakeExecution)

    iqs_server = ThreadingHTTPServer(("127.0.0.1", 0), product_handler(Static, iq_service))
    cleanup.callback(iqs_server.server_close)
    iqs_thread = threading.Thread(target=iqs_server.serve_forever, daemon=True)
    iqs_thread.start()

    def stop_iqs():
        iqs_server.shutdown()
        iqs_thread.join(timeout=5)
        assert not iqs_thread.is_alive(), "IQS HTTP thread was not cleaned up"

    cleanup.callback(stop_iqs)
    FakeExecution.started.clear()
    FakeExecution.controls.clear()
    FakeExecution.counter = 0
    FakeExecution.runs.clear()

    dashboard_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cleanup.callback(dashboard_socket.close)
    dashboard_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dashboard_socket.bind(("127.0.0.1", 0))
    dashboard_socket.listen(128)
    dashboard_origin = f"http://127.0.0.1:{dashboard_socket.getsockname()[1]}"
    iqs_origin = f"http://127.0.0.1:{iqs_server.server_address[1]}"
    quick_scan = IqsQuickScanAdapter(JsonHttpTransport(iqs_origin, owner="invest-quick-scan"))
    job_adapter = IqsJobAdapter(python=sys.executable, root=ROOT, origin=iqs_origin, timeout_seconds=20)
    dashboard = create_app({"identity": Identity(), "quick_scan": quick_scan,
                            "jobs": {"invest-quick-scan": job_adapter}},
                           tmp_path / "dashboard-data", allow_test_origin=True)
    uvicorn_server = uvicorn.Server(uvicorn.Config(dashboard, log_level="warning", access_log=False,
                                                   lifespan="off"))
    dashboard_thread = threading.Thread(target=uvicorn_server.run,
                                        kwargs={"sockets": [dashboard_socket]}, daemon=True)
    dashboard_thread.start()

    def stop_dashboard():
        uvicorn_server.should_exit = True
        dashboard_thread.join(timeout=10)
        if dashboard_thread.is_alive():
            uvicorn_server.force_exit = True
            dashboard_thread.join(timeout=5)
        assert not dashboard_thread.is_alive(), "Dashboard HTTP thread was not cleaned up"

    cleanup.callback(stop_dashboard)
    try:
        deadline = time.monotonic() + 15
        while not uvicorn_server.started and dashboard_thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert uvicorn_server.started, "Dashboard HTTP server did not start"

        import backend.dashboard.adapters.m8_owner_jobs.iqs_job as iqs_job
        real_run_cli = iqs_job.run_cli
        cli_operations = []
        submitted_ids = []
        lost_submit_response = {"pending": True}

        def lose_one_successful_submit_response(owner, argv, **kwargs):
            operation = argv[argv.index("--operation") + 1]
            assert argv[argv.index("--origin") + 1] == iqs_origin
            cli_operations.append(operation)
            if operation == "submit":
                payload = json.loads(kwargs["stdin"].decode("utf-8"))
                submitted_ids.append(payload["command_request"]["command_id"])
            result = real_run_cli(owner, argv, **kwargs)
            if operation == "submit" and lost_submit_response.pop("pending", False):
                assert result.exit_code == 0, result.stderr.decode("utf-8", "replace")
                return CliResult(stdout=b"", stderr=b"simulated response lost after owner accepted command", exit_code=1)
            return result

        monkeypatch.setattr(iqs_job, "run_cli", lose_one_successful_submit_response)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(f"{dashboard_origin}/company/ENT_A/quickscan?listing_id={listing_id}",
                          wait_until="networkidle", timeout=30000)
                assert page.get_by_text(RESULT_SNAPSHOT["result_id"], exact=False).first.is_visible(timeout=15000)
                page.get_by_role("button", name="提交正式粗筛").click()
                page.get_by_role("alert").wait_for(state="visible", timeout=30000)
                query_link = page.get_by_role("link", name="查询原命令")
                query_link.wait_for(state="visible")
                command_id = submitted_ids[0]
                assert command_id.startswith("cmd-")
                assert query_link.get_attribute("href") == f"/jobs?job={command_id}"
                assert "命令状态待确认" in page.get_by_role("status").inner_text()
                query_link.click()
                page.wait_for_url(f"**/jobs?job={command_id}", timeout=10000)
                page.get_by_role("heading", name="查询 owner 任务").wait_for(timeout=10000)
                page.get_by_text("running", exact=True).wait_for(timeout=30000)
                assert FakeExecution.started and len(FakeExecution.started) == 1
                assert cli_operations == ["submit", "get-command"]
            finally:
                browser.close()
    finally:
        cleanup.close()
