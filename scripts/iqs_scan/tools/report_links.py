"""Paths for links in local reports, including Windows drive boundaries."""

import os
from pathlib import Path
from urllib.parse import quote


def local_report_link(target: Path, containing_directory: Path) -> str:
    """Prefer relocatable links and use a file URI when relative addressing is impossible."""
    try:
        relative = os.path.relpath(target, containing_directory)
    except ValueError:
        return target.absolute().as_uri()
    return quote(Path(relative).as_posix())
