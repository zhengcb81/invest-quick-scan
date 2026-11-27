"""The workbench transport keeps Windows launches off the desktop."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from iqs_scan.workbench import _background_process


@pytest.mark.parametrize("has_windowless_interpreter", [True, False])
def test_windows_waited_owner_keeps_request_and_uses_same_install(
    tmp_path, monkeypatch, has_windowless_interpreter,
):
    console = tmp_path / "python.exe"
    console.touch()
    windowless = console.with_name("pythonw.exe")
    if has_windowless_interpreter:
        windowless.touch()
    monkeypatch.setattr(_background_process, "_WINDOWS_NO_CONSOLE", 0x08000000)
    calls = []
    response = object()

    def run(command, **options):
        calls.append((command, options))
        return response

    command = [str(console), "-B", "-X", "utf8", "owner_cli.py"]
    options = {"cwd": str(tmp_path), "input": b"query", "capture_output": True, "timeout": 2}
    assert _background_process.run_background(command, runner=run, **options) is response
    expected = windowless if has_windowless_interpreter else console
    assert calls == [([str(expected), *command[1:]], {**options, "creationflags": 0x08000000})]
    assert command[0] == str(console)


def test_windows_running_job_uses_same_port_and_preserves_pipe_options(tmp_path, monkeypatch):
    console = tmp_path / "python.exe"
    console.touch()
    windowless = console.with_name("pythonw.exe")
    windowless.touch()
    monkeypatch.setattr(_background_process, "_WINDOWS_NO_CONSOLE", 0x08000000)
    calls = []
    child = object()

    def popen(command, **options):
        calls.append((command, options))
        return child

    monkeypatch.setattr(_background_process.subprocess, "Popen", popen)
    command = [str(console), "-m", "owner_worker"]
    options = {"env": {"OWNER_WORKER": "1"}, "stdout": _background_process.subprocess.PIPE}
    assert _background_process.start_background(command, **options) is child
    assert calls == [
        ([str(windowless), *command[1:]], {**options, "creationflags": 0x08000000, "stdin": _background_process.subprocess.DEVNULL}),
    ]


def test_non_windows_command_and_options_pass_through(tmp_path, monkeypatch):
    console = tmp_path / "python.exe"
    console.touch()
    console.with_name("pythonw.exe").touch()
    monkeypatch.setattr(_background_process, "_WINDOWS_NO_CONSOLE", 0)

    def run(command, **options):
        return command, options

    command = [str(console), "-B", "owner_cli.py"]
    assert _background_process.run_background(command, runner=run, timeout=2) == (command, {"timeout": 2})


def test_selected_checkout_launcher_passes_windowless_options(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from iqs_scan.workbench import open_dashboard

    ui = tmp_path / "ui"
    static = ui / "src" / "app"
    static.mkdir(parents=True)
    (static / "index.html").touch()
    data = tmp_path / "checkout"
    scripts = data / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "open_dashboard.py").touch()
    (scripts / "dashboard_service.py").touch()
    seen = []
    monkeypatch.setattr(_background_process, "_WINDOWS_NO_CONSOLE", 0x08000000)
    monkeypatch.setattr(
        _background_process.subprocess, "run",
        lambda command, **options: seen.append((command, options)) or SimpleNamespace(returncode=7),
    )

    assert open_dashboard.main(["--data-root", str(data), "--ui-root", str(ui), "--port", "0", "--plan"]) == 7
    command, options = seen[0]
    assert command[-3:] == ["--port", "0", "--plan"]
    assert options["creationflags"] == 0x08000000
    assert options["stdin"] == _background_process.subprocess.DEVNULL
