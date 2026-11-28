"""Coverage and selection contracts for split testing; no product runtime."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
from scripts import run_tests as runner


def fixture_manifest(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    suites = {group: ["test_" + group + ".py"] for group in runner.GROUPS}
    for file in sum(suites.values(), []):
        (tests / file).write_text("def test_fixture(): pass\n", encoding="utf8")
    path = tests / "suites.json"
    path.write_text(json.dumps(dict(version=1, suites=suites)), encoding="utf8")
    return path, suites


def test_current_manifest_partitions_every_test_file_exactly_once():
    suites = runner.load_suites(ROOT, ROOT / "tests/suites.json")
    assert set(runner.selection("offline", suites)) == {"fast", "integration", "e2e"}
    assert runner.selection("all", suites) == suites
    assert list(runner.selection("fast", suites)) == ["fast"]
    assert all((ROOT / "tests" / filename).is_file() for filename in suites["fast"])
    assert "test_producer_pipeline_e2e.py" in suites["e2e"]
    assert all("native_e2e" in name for name in suites["native"])


def test_developer_fast_partitions_use_standalone_scope(tmp_path):
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    live: provider I/O\n    owner_assets: external owner\n", encoding="utf-8"
    )
    (test_dir / "test_scope.py").write_text(
        "import pytest\n"
        "def test_home_repo(): assert True\n"
        "@pytest.mark.owner_assets\n"
        "def test_owner(): raise AssertionError('owner test in fast profile')\n"
        "@pytest.mark.live\n"
        "def test_live(): raise AssertionError('live test in fast profile')\n",
        encoding="utf-8",
    )
    result = runner.run_group(tmp_path, "fast", ["test_scope.py"], tmp_path, temp_root=tmp_path)
    assert result["exit_code"] == 0, (tmp_path / "fast.log").read_text(encoding="utf-8")
    assert result["junit"] == {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}


def test_test_child_permits_owned_literal_loopback_but_rejects_external_network(tmp_path):
    root = tmp_path / "fixture-root"
    tests = root / "tests"
    tests.mkdir(parents=True)
    fixture = tests / "test_network_fixture.py"
    fixture.write_text('''import socket, threading
def test_loopback():
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    with ThreadingHTTPServer(('127.0.0.1', 0), BaseHTTPRequestHandler) as server:
        assert server.server_name == '127.0.0.1'
    with socket.socket() as server:
        server.bind(('127.0.0.1',0));server.listen(1)
        def accept():
            conn,_=server.accept()
            with conn:conn.sendall(b'ok')
        thread=threading.Thread(target=accept,daemon=True);thread.start()
        with socket.create_connection(server.getsockname(),timeout=3) as client:
            assert client.recv(2)==b'ok'
        thread.join(timeout=3);assert not thread.is_alive()
def test_external():
    import pytest
    with pytest.raises(RuntimeError,match='offline_test_network_forbidden'):
        socket.create_connection(('203.0.113.1',443),timeout=.1)
    with pytest.raises(RuntimeError,match='offline_test_network_forbidden'):
        socket.getaddrinfo('external.invalid',443)
    with socket.socket() as outbound:
        with pytest.raises(RuntimeError,match='offline_test_network_forbidden'):
            outbound.connect(('203.0.113.1',443))
def test_udp():
    import pytest
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as udp:
        with pytest.raises(RuntimeError,match='offline_test_network_forbidden'):
            udp.connect(('127.0.0.1',9))
        with pytest.raises(RuntimeError,match='offline_test_network_forbidden'):
            udp.sendto(b'owned-fixture',('127.0.0.1',9))
    with pytest.raises(RuntimeError,match='offline_test_network_forbidden'):
        socket.getaddrinfo('127.0.0.1',9,type=socket.SOCK_DGRAM)
def test_dns_entrypoints():
    import pytest
    for resolve in (
        lambda: socket.gethostbyname('external.invalid'),
        lambda: socket.gethostbyname_ex('external.invalid'),
        lambda: socket.gethostbyaddr('203.0.113.1'),
        lambda: socket.getnameinfo(('203.0.113.1',443),0),
    ):
        with pytest.raises(RuntimeError,match='offline_test_network_forbidden'):
            resolve()
''',encoding='utf-8')
    output = tmp_path / "runner-output"
    output.mkdir()
    temp_root = tmp_path / "runner-temp"
    temp_root.mkdir()
    result = runner.run_group(
        root, "fast", ["test_network_fixture.py"], output, temp_root=temp_root
    )
    assert result["exit_code"] == 0, (output / "fast.log").read_text(encoding="utf-8")
    assert result["temporary_root_removed"] is True


@pytest.mark.parametrize("mutation", ["unassigned", "missing", "duplicate", "traversal"])
def test_new_missing_duplicate_or_redirected_tests_cannot_silently_disappear(tmp_path, mutation):
    path, suites = fixture_manifest(tmp_path)
    if mutation == "unassigned":
        (tmp_path / "tests/test_new.py").write_text("", encoding="utf8")
    elif mutation == "missing":
        (tmp_path / "tests/test_fast.py").unlink()
    elif mutation == "duplicate":
        suites["integration"].append("test_fast.py")
    else:
        suites["fast"] = ["../test_escaped.py"]
    path.write_text(json.dumps(dict(version=1, suites=suites)), encoding="utf8")
    with pytest.raises(ValueError):
        runner.load_suites(tmp_path, path)


def test_duplicate_manifest_keys_are_rejected(tmp_path):
    path, _ = fixture_manifest(tmp_path)
    path.write_text('{"version":1,"version":1,"suites":{}}', encoding="utf8")
    with pytest.raises(ValueError, match="duplicate_suite_manifest_key"):
        runner.load_suites(tmp_path, path)


def test_paid_flags_keys_and_parent_pytest_options_are_not_inherited(tmp_path, monkeypatch):
    for name in ("MIMO_API_KEY", "DEEPSEEK_API_KEY", "ZAI_API_KEY", "TOKEN", "STOCKQA_RUN_LIVE_E2E",
                 "PYTEST_ADDOPTS", "PYTEST_PLUGINS", "IQS_C06_RUN_INTEGRATION"):
        monkeypatch.setenv(name, "not-a-secret-test-value")
    env = runner.clean_environment(tmp_path)
    assert env["TEMP"] == env["TMP"] == str(tmp_path)
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert not any(key in env for key in ("MIMO_API_KEY", "DEEPSEEK_API_KEY", "ZAI_API_KEY", "TOKEN",
        "STOCKQA_RUN_LIVE_E2E", "PYTEST_ADDOPTS", "PYTEST_PLUGINS", "IQS_C06_RUN_INTEGRATION"))


def test_all_refuses_missing_native_runtime_before_running_any_tests(tmp_path, monkeypatch):
    fixture_manifest(tmp_path)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.delenv("IQS_C06_RUN_INTEGRATION", raising=False)
    calls = []
    monkeypatch.setattr(runner, "run_group", lambda *a, **k: calls.append(a))
    assert runner.main(["all"]) == 2
    assert not calls and not (tmp_path / "runs").exists()


def test_success_exit_without_junit_cannot_be_reported_green(tmp_path, monkeypatch):
    output = tmp_path / "reports"
    output.mkdir()
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0))
    result = runner.run_group(tmp_path, "fast", ["test_missing.py"], output, temp_root=tmp_path)
    assert result["exit_code"] == 2 and result["status"] == "junit_missing"
    assert result["temporary_root_removed"] and "junit" not in result


@pytest.mark.parametrize("xml", [
    '<testsuites/>', '<wrong-root/>',
    '<testsuites><testsuite tests="1" failures="1"/></testsuites>',
    '<testsuites><testsuite tests="-1"/></testsuites>',
])
def test_empty_invalid_or_conflicting_junit_cannot_be_reported_green(tmp_path, monkeypatch, xml):
    output = tmp_path / "reports"
    output.mkdir()
    def bad_report(*args, **kwargs):
        (output / "fast.xml").write_text(xml, encoding="utf8")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(runner.subprocess, "run", bad_report)
    result = runner.run_group(tmp_path, "fast", ["test_fixture.py"], output, temp_root=tmp_path)
    assert result["exit_code"] == 2 and result["temporary_root_removed"]


def test_test_partitions_are_windowless_on_windows(tmp_path, monkeypatch):
    from types import SimpleNamespace

    calls = []
    monkeypatch.setattr(runner.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    def run(command, **options):
        calls.append((command, options))
        return SimpleNamespace(returncode=3)

    monkeypatch.setattr(runner.subprocess, "run", run)
    result = runner.run_group(tmp_path, "fast", ["test_fixture.py"], tmp_path, temp_root=tmp_path)
    assert result["exit_code"] == 3
    assert result["temporary_root_removed"]
    _, options = calls[0]
    assert options["creationflags"] == 0x08000000
    assert options["stdin"] == runner.subprocess.DEVNULL


def test_partition_preserves_std_handles_for_nested_python(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_child.py").write_text(
        "import subprocess, sys\n"
        "def test_child():\n"
        "    proc = subprocess.run([sys.executable, '-c', 'print(41)'], "
        "capture_output=True, timeout=10, check=True)\n"
        "    assert proc.stdout.strip() == b'41'\n",
        encoding="utf-8",
    )
    result = runner.run_group(tmp_path, "fast", ["test_child.py"], tmp_path, temp_root=tmp_path)
    assert result["exit_code"] == 0, (tmp_path / "fast.log").read_text(encoding="utf-8")
