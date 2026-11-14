"""Current UI public modules over the live IQS loopback server, in isolated state."""
from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from dashboard_http import product_handler
from dashboard_service import DashboardService
from open_dashboard import _handler as static_handler
from workbench_snapshot import build_workbench_snapshot, load_workbench_snapshot, write_workbench_snapshot


class Owner:
    def __init__(self, config):
        self.config = config

    def status(self):
        return {"available": True, "network_calls": 0}

    def search(self, *args, **kwargs):
        return {"rows": [{"entity_id": "SYNTHETIC_FORMAL", "canonical_name": "FORMAL_OWNER_RECORD",
                          "resolution_status": "resolved"}],
                "total": 1, "snapshot": {"ordered_ids": ["SYNTHETIC_FORMAL"]}}


class Execution:
    def __init__(self, config):
        self.config = config

    def status(self):
        return {"available": True, "API_requests": 0}


def _env(tmp_path: Path) -> dict[str, str]:
    allowed = {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC"}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env.update(TEMP=str(tmp_path), TMP=str(tmp_path), PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    return env


def test_current_ui_partial_snapshot_and_formal_results_survive_reopen(tmp_path):
    node = shutil.which("node")
    if not node:
        import pytest
        pytest.skip("Node.js is required to execute the current UI's public modules")
    ui_root = Path(os.environ.get("IQS_UI_ROOT", ROOT.parent / "iqs-question-bank-ui-lab")).resolve()
    if not (ui_root / "src" / "app" / "store.js").is_file():
        import pytest
        pytest.skip("Current UI source is unavailable; set IQS_UI_ROOT to its checkout")

    config = {"state_root": str(tmp_path / "state"), "workspace_root": "",
              "workspace_kind": "unconfigured"}
    config_path = tmp_path / "dashboard.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    service = DashboardService(root=ROOT, config_path=config_path,
                               owner_factory=Owner, execution_factory=Execution)
    snapshot = build_workbench_snapshot(ROOT, service.config,
                                        generated_at="2026-11-12T00:00:00Z")
    assert snapshot["availability"]["bank"] == "available"
    assert snapshot["availability"]["roster"] == "unavailable"
    snapshot["availability"]["answers"] = "partial"
    snapshot["answers"] = {
        "runs": [{"run_id": "run-ui-partial-fixture", "entity_id": None,
                  "binding": {"state": "unbound"},
                  "answers": [{"question_id": "Q_SYNTHETIC", "score": 4,
                               "rationale": "test fixture; no investment conclusion"}]}],
        "alias_entries": [], "unmatched": [],
    }
    snapshot["warnings"].append({"section": "answers", "code": "integration_partial",
                                 "message": "integration partial: fixture history is incomplete"})
    snapshot_path = tmp_path / "state" / "workbench" / "snapshot.json"
    write_workbench_snapshot(snapshot_path, snapshot)
    before_snapshot = snapshot_path.read_bytes()

    static = static_handler(ui_root / "src" / "app", snapshot_path, load_workbench_snapshot)
    snapshot_reads = []

    class CountingStatic(static):
        def do_GET(self):
            if self.path == "/generated/snapshot.json":
                snapshot_reads.append(self.path)
            super().do_GET()

    handler = product_handler(CountingStatic, service)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        origin = f"http://127.0.0.1:{server.server_address[1]}/"
        with urlopen(origin + "generated/snapshot.json", timeout=10) as response:
            assert response.status == 200
            live_snapshot = json.loads(response.read())
        with urlopen(origin + "api/product/status", timeout=10) as response:
            assert response.status == 200
            live_status = json.loads(response.read())
        with urlopen(origin + "api/product/results", timeout=10) as response:
            assert response.status == 200
            live_results = json.loads(response.read())
        assert live_snapshot["availability"]["bank"] == "available"
        assert live_snapshot["availability"]["roster"] == "unavailable"
        assert live_snapshot["availability"]["answers"] == "partial"
        assert live_results["data"]["rows"][0]["canonical_name"] == "FORMAL_OWNER_RECORD"
        done = subprocess.run([node, str(ROOT / "tests" / "js" / "workbench_public_http.mjs"),
                               str(ui_root), origin], cwd=ROOT, env=_env(tmp_path),
                              capture_output=True, text=True, encoding="utf-8", timeout=60)
        assert done.returncode == 0, done.stdout + "\n" + done.stderr
        result = json.loads(done.stdout.strip().splitlines()[-1])
        assert result["passed"] is True and result["formal_result_preserved"] is True
        assert result["snapshot_reads"] == 2 and result["product_writes"] == 0
        assert snapshot_path.read_bytes() == before_snapshot, "UI reads must not rewrite or renew the snapshot"

        # Exercise the actual page in a browser. Import-only checks cannot prove
        # that a person sees usable bank content while another snapshot section
        # is partial/unavailable.
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            import pytest
            pytest.skip("Playwright is required for the rendered UI integration")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                reads_before_browser = len(snapshot_reads)
                page.goto(origin + "#/bank", wait_until="networkidle", timeout=30000)
                page.get_by_role("heading", name="题库内容与版本").wait_for(state="visible", timeout=15000)
                page.get_by_test_id("basic-required").wait_for(state="visible", timeout=10000)
                assert page.get_by_test_id("module-card").count() > 0
                source_warning = page.get_by_test_id("snapshot-source-warning")
                source_warning.wait_for(state="visible", timeout=10000)
                assert "roster.json" in source_warning.inner_text()
                partial_warning = page.get_by_test_id("optional-drafts-warning")
                partial_warning.wait_for(state="visible", timeout=10000)
                assert "历史薄草稿源尚未明确选择" in partial_warning.inner_text()
                rendered_warnings = page.get_by_test_id("snapshot-warnings")
                rendered_warnings.wait_for(state="visible", timeout=10000)
                assert "integration partial" in rendered_warnings.inner_text()
                assert page.get_by_role("heading", name="题库内容与版本").is_visible()
                assert len(snapshot_reads) == reads_before_browser + 1, "the rendered UI should fetch one atomic snapshot"
            finally:
                browser.close()
        assert snapshot_path.read_bytes() == before_snapshot, "rendering partial data must remain read-only"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_i6_real_launcher_reopen_reads_partial_snapshot_without_starting_scan(tmp_path):
    """Use the public launcher and rendered UI; opening/reopening is read-only.

    The isolated config intentionally has no registered execution bundle, so
    the real task-start button remains disabled. This proves that a normal
    visit or reload cannot dispatch work; it does not substitute a fake task
    for the separate explicit-start path.
    """
    import pytest

    ui_root = Path(os.environ.get("IQS_UI_ROOT", ROOT.parent / "iqs-question-bank-ui-lab")).resolve()
    if not (ui_root / "src" / "app" / "index.html").is_file():
        pytest.skip("Current UI source is unavailable; set IQS_UI_ROOT to its checkout")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Playwright is required for the rendered UI integration")

    state_root = tmp_path / "state"
    config = {"state_root": str(state_root), "workspace_root": "",
              "workspace_kind": "unconfigured"}
    config_path = tmp_path / "dashboard.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    snapshot = build_workbench_snapshot(ROOT, config, generated_at="2026-11-13T00:00:00Z")
    assert snapshot["availability"]["bank"] == "available"
    assert snapshot["availability"]["roster"] == "unavailable"
    snapshot["availability"]["answers"] = "partial"
    snapshot["answers"] = {
        "runs": [{"run_id": "run-i6-partial-fixture", "entity_id": None,
                  "binding": {"state": "unbound"},
                  "answers": [{"question_id": "Q_I6_SYNTHETIC", "score": 6,
                               "rationale": "隔离UI测试；不是投资结论"}]}],
        "alias_entries": [], "unmatched": [],
    }
    snapshot["warnings"].append({"section": "answers", "code": "i6_partial_fixture",
                                 "message": "隔离测试：历史答案不完整"})
    snapshot_path = state_root / "workbench" / "snapshot.json"
    write_workbench_snapshot(snapshot_path, snapshot)
    before_snapshot = snapshot_path.read_bytes()

    command = [sys.executable, "-B", "-X", "utf8", str(SCRIPTS / "open_dashboard.py"),
               "--ui-root", str(ui_root), "--data-root", str(ROOT), "--port", "0",
               "--no-refresh", "--dashboard-config", str(config_path)]
    process = subprocess.Popen(command, cwd=ROOT, env=_env(tmp_path),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace", bufsize=1)
    ready_lines: queue.Queue[str] = queue.Queue()
    reader = threading.Thread(target=lambda: ready_lines.put(process.stdout.readline()), daemon=True)
    reader.start()
    try:
        try:
            ready_line = ready_lines.get(timeout=30)
        except queue.Empty:
            pytest.fail(f"public launcher did not report ready; exit={process.poll()}")
        assert ready_line, f"public launcher exited before ready; exit={process.poll()}"
        ready = json.loads(ready_line)
        assert ready["status"] == "ready", ready
        assert ready["model_calls"] == ready["network_calls"] == 0
        assert ready["refreshed"] is False
        origin = ready["url"]

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                observed_requests = []
                page.on("request", lambda request: observed_requests.append(
                    (request.method, request.url)))

                page.goto(origin + "#/bank", wait_until="domcontentloaded", timeout=30000)
                page.get_by_role("heading", name="题库内容与版本").wait_for(
                    state="visible", timeout=15000)
                page.get_by_test_id("basic-required").wait_for(state="visible", timeout=10000)
                assert page.get_by_test_id("module-card").count() > 0
                page.get_by_test_id("snapshot-source-warning").wait_for(state="visible", timeout=10000)
                page.get_by_test_id("optional-drafts-warning").wait_for(state="visible", timeout=10000)
                assert "隔离测试：历史答案不完整" in page.get_by_test_id("snapshot-warnings").inner_text()

                page.goto(origin + "#/operations", wait_until="domcontentloaded", timeout=30000)
                page.get_by_role("heading", name="扫描任务").wait_for(state="visible", timeout=15000)
                page.get_by_text("高级恢复与迁移：原单包 / 手工导入").click(timeout=10000)
                start_button = page.get_by_role("button", name="启动所选扫描包")
                assert start_button.is_disabled(timeout=5000), \
                    "unregistered work must not expose an enabled scan start"
                page.reload(wait_until="domcontentloaded", timeout=30000)
                page.get_by_role("heading", name="扫描任务").wait_for(state="visible", timeout=15000)
                page.get_by_text("高级恢复与迁移：原单包 / 手工导入").click(timeout=10000)
                assert page.get_by_role("button", name="启动所选扫描包").is_disabled(timeout=5000)

                writes = [(method, url) for method, url in observed_requests if method != "GET"]
                assert writes == [], f"opening or reopening the UI dispatched a write: {writes}"
                assert any(url.endswith("/api/product/tasks") for _method, url in observed_requests), \
                    "the tasks page should query the original task status over the real HTTP service"
                assert snapshot_path.read_bytes() == before_snapshot, \
                    "the public --no-refresh launcher and UI reads must not renew or rewrite the snapshot"
            finally:
                browser.close()
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        reader.join(timeout=5)
        if process.stdout is not None:
            process.stdout.close()
        assert not reader.is_alive(), "launcher output reader must stop during cleanup"


def test_i6_explicit_ui_start_is_read_once_after_reopen_with_local_runner(tmp_path):
    """A real UI click starts one isolated local stub; reload only reads that task."""
    import pytest

    node = shutil.which("node")
    ui_root = Path(os.environ.get("IQS_UI_ROOT", ROOT.parent / "iqs-question-bank-ui-lab")).resolve()
    if not node or not (ui_root / "src" / "app" / "index.html").is_file():
        pytest.skip("Node.js and current UI source are required for the rendered task integration")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Playwright is required for the rendered task integration")

    # Reuse the real Dashboard execution input shape and real public StockQA
    # permission/inspection CLI fixtures; only the model executable is a local
    # deterministic stub with no network or credential access.
    from test_dashboard_execution import deployment as execution_deployment

    execution_config, runtime, bundle = execution_deployment.__wrapped__(tmp_path)
    source = Path(execution_config["stockqa_root"])
    counter = source / "dispatch-count.txt"
    (source / "main_with_llm.py").write_text(
        "import json, os, pathlib, re, sys\n"
        "assert not any(re.search(r'(?:KEY|TOKEN|SECRET|PASSWORD|LIVE_E2E)', key, re.I) "
        "for key in os.environ), 'test runner received credential-like environment'\n"
        "counter = pathlib.Path(__file__).with_name('dispatch-count.txt')\n"
        "with counter.open('a', encoding='utf-8') as stream: stream.write('started\\n')\n"
        "output = pathlib.Path(sys.argv[sys.argv.index('--output') + 1])\n"
        "output.write_text(json.dumps({'fixture': 'i6-local-runner', 'API_requests': 0}), encoding='utf-8')\n"
        "print('I6 deterministic local runner; no model or search API')\n",
        encoding="utf-8",
    )

    state_root = tmp_path / "dashboard-state"
    state_root.mkdir()
    config = {
        "schema_version": "1.0.0",
        "stockwiki_root": str(tmp_path / "empty-stockwiki"),
        "stockqa_root": str(source),
        "stockqa_python": sys.executable,
        "runtime_dir": str(runtime),
        "model_policy_path": execution_config["model_policy_path"],
        "workspace_root": "",
        "workspace_kind": "unconfigured",
        "workspace_label": "isolated I6 local runner",
        "state_root": str(state_root),
        "execution_bundles": {"test": bundle},
        "import_bundles": {},
    }
    config_path = tmp_path / "dashboard.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    snapshot = build_workbench_snapshot(ROOT, config, generated_at="2026-11-13T00:00:00Z")
    snapshot["availability"]["answers"] = "partial"
    snapshot["answers"] = {"runs": [], "alias_entries": [], "unmatched": []}
    snapshot["warnings"].append({"section": "answers", "code": "i6_partial_fixture",
                                 "message": "隔离测试：历史答案不完整"})
    snapshot_path = state_root / "workbench" / "snapshot.json"
    write_workbench_snapshot(snapshot_path, snapshot)
    before_snapshot = snapshot_path.read_bytes()

    command = [sys.executable, "-B", "-X", "utf8", str(SCRIPTS / "open_dashboard.py"),
               "--ui-root", str(ui_root), "--data-root", str(ROOT), "--port", "0",
               "--no-refresh", "--dashboard-config", str(config_path)]
    process = subprocess.Popen(command, cwd=ROOT, env=_env(tmp_path),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace", bufsize=1)
    ready_lines: queue.Queue[str] = queue.Queue()

    def read_output():
        assert process.stdout is not None
        for line in process.stdout:
            ready_lines.put(line)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    try:
        try:
            ready_line = ready_lines.get(timeout=30)
        except queue.Empty:
            pytest.fail(f"public launcher did not report ready; exit={process.poll()}")
        assert ready_line, f"public launcher exited before ready; exit={process.poll()}"
        ready = json.loads(ready_line)
        assert ready["status"] == "ready", ready
        assert ready["model_calls"] == ready["network_calls"] == 0
        assert ready["refreshed"] is False
        origin = ready["url"]

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                requests = []
                responses = []
                page.on("request", lambda request: requests.append(
                    (request.method, request.url)))
                page.on("response", lambda response: responses.append(response))
                page.goto(origin + "#/operations", wait_until="domcontentloaded", timeout=30000)
                page.get_by_role("heading", name="扫描任务").wait_for(state="visible", timeout=15000)
                page.get_by_text("高级恢复与迁移：原单包 / 手工导入").click(timeout=10000)
                picker = page.get_by_label("已注册扫描包")
                picker.wait_for(state="visible", timeout=10000)
                page.wait_for_function(
                    "() => [...document.querySelectorAll('select[aria-label=\\\"已注册扫描包\\\"] option')] "
                    ".some(option => option.value === 'test')",
                    timeout=15000,
                )
                picker.select_option("test")
                start_button = page.get_by_role("button", name="启动所选扫描包")
                assert start_button.is_enabled(timeout=5000), "registered isolated package should be startable"

                with page.expect_response(
                    lambda response: response.request.method == "POST"
                    and response.url.endswith("/api/product/tasks/start"),
                    timeout=20000,
                ) as started_response:
                    start_button.click(timeout=10000)
                start_reply = started_response.value
                assert start_reply.status == 200
                started = start_reply.json()["data"]
                assert started["status"] == "started" and started["process_started"] is True
                run_id = started["run"]["run_id"]
                assert run_id.startswith("run-")

                page.wait_for_function(
                    "runId => document.body.innerText.includes(runId)", arg=run_id, timeout=15000)
                task_gets_before_reload = [response for response in responses
                    if response.request.method == "GET" and response.url.endswith("/api/product/tasks")]
                assert task_gets_before_reload, "the live UI must read task state through public HTTP after start"
                last_tasks = task_gets_before_reload[-1].json()["data"]["tasks"]
                assert len(last_tasks) == 1 and last_tasks[0]["run_id"] == run_id

                post_count_before_reload = sum(
                    method == "POST" and url.endswith("/api/product/tasks/start")
                    for method, url in requests)
                assert post_count_before_reload == 1
                with page.expect_response(
                    lambda response: response.request.method == "GET"
                    and response.url.endswith("/api/product/tasks"),
                    timeout=20000,
                ) as reopened_tasks:
                    page.reload(wait_until="domcontentloaded", timeout=30000)
                assert reopened_tasks.value.status == 200
                reopened = reopened_tasks.value.json()["data"]["tasks"]
                assert len(reopened) == 1 and reopened[0]["run_id"] == run_id
                page.get_by_text(run_id, exact=True).wait_for(state="visible", timeout=10000)
                assert sum(method == "POST" and url.endswith("/api/product/tasks/start")
                           for method, url in requests) == 1, \
                    "reopening the UI must never submit a second start"
                assert counter.read_text(encoding="utf-8").splitlines() == ["started"], \
                    "the local runner must be launched exactly once"
                assert snapshot_path.read_bytes() == before_snapshot, \
                    "starting/reading tasks must not renew or rewrite the workbench snapshot"
            finally:
                browser.close()
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        reader.join(timeout=5)
        if process.stdout is not None:
            process.stdout.close()
        assert not reader.is_alive(), "launcher output reader must stop during cleanup"
