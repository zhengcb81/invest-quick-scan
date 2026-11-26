"""Native launch boundary for workbench-owned background processes."""

from pathlib import Path
import subprocess


_WINDOWS_NO_CONSOLE = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _invocation(command, options):
    if not _WINDOWS_NO_CONSOLE:
        return command, options

    executable = Path(command[0])
    if executable.is_absolute() and executable.name.casefold() == "python.exe":
        windowless = executable.with_name("pythonw.exe")
        if windowless.is_file():
            command = [str(windowless), *command[1:]]
    options["creationflags"] = options.get("creationflags", 0) | _WINDOWS_NO_CONSOLE
    # GUI Python can have no valid standard input handle. Keep explicit
    # input pipes, and close stdin for background commands that never read it.
    if "stdin" not in options and options.get("input") is None:
        options["stdin"] = subprocess.DEVNULL
    return command, options


def run_background(command, *, runner=None, **options):
    command, options = _invocation(command, options)
    return (runner or subprocess.run)(command, **options)


def start_background(command, **options):
    command, options = _invocation(command, options)
    return subprocess.Popen(command, **options)
