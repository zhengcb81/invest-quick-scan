"""Tiny real subprocess checks for isolation and failure accounting."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("split_test_subprocess_runner", ROOT / "scripts/run_tests.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_real_pytest_process_denies_network_removes_key_and_cleans_own_temp(tmp_path, monkeypatch):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_tiny.py").write_text('''import os, socket
from pathlib import Path
import pytest
def test_isolated():
    assert "MIMO_API_KEY" not in os.environ
    assert "STOCKQA_RUN_LIVE_E2E" not in os.environ
    root = Path(os.environ["TEMP"])
    assert root.name.startswith("iqs-tests-")
    (root / "temporary-fixture.txt").write_text("fixture")
    with pytest.raises(RuntimeError, match="offline_test_network_forbidden"):
        socket.getaddrinfo("example.invalid", 443)
''', encoding="utf8")
    output = tmp_path / "reports"
    output.mkdir()
    sentinel = tmp_path / "preexisting.txt"
    sentinel.write_text("keep", encoding="utf8")
    monkeypatch.setenv("MIMO_API_KEY", "SYNTHETIC_TEST_VALUE")
    monkeypatch.setenv("STOCKQA_RUN_LIVE_E2E", "1")
    result = runner.run_group(tmp_path, "fast", ["test_tiny.py"], output, temp_root=tmp_path)
    assert result["exit_code"] == 0
    assert result["junit"] == dict(tests=1, failures=0, errors=0, skipped=0)
    assert result["temporary_root_removed"] and sentinel.read_text(encoding="utf8") == "keep"


def test_real_pytest_failure_is_reported_as_failure_without_becoming_green(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_failure.py").write_text("def test_expected_failure(): assert False\n", encoding="utf8")
    output = tmp_path / "reports"
    output.mkdir()
    result = runner.run_group(tmp_path, "fast", ["test_failure.py"], output, temp_root=tmp_path)
    assert result["exit_code"] == 1
    assert result["junit"]["failures"] == 1 and result["temporary_root_removed"]
