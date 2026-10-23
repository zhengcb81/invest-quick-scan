"""Reference-integrity checks for a handoff: do the things it cites actually exist?

Why this exists (2026-10-23): two delivered handoffs passed the shape check while
citing references that do not exist — a `result_commit` whose 40-hex string was a
transcription corruption of a real commit, twelve `changed_paths` that were never
written, and a `content_hash` that matched no file. The schema only enforces
`minLength: 7` on commit ids, so shape validation cannot catch this class.

Everything here is read-only and offline. Each check returns a list of problems;
an empty list means the reference resolved.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

# Reference kinds that name a git object rather than a file.
GIT_REF_FIELDS = ("base_commit", "result_commit", "snapshot_commit")


def _git(repo: Path, *args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return 1, str(error)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def repo_of(handoff: dict, handoff_path: Path) -> Path | None:
    """Locate the repository a handoff describes.

    snapshot.repository is an absolute path to the writer's repo; when it is
    absent or unreadable, fall back to walking up from the handoff file itself.
    """
    declared = ((handoff.get("snapshot") or {}).get("repository") or "").strip()
    if declared:
        candidate = Path(declared)
        if candidate.is_dir():
            return candidate
    for parent in handoff_path.resolve().parents:
        if (parent / ".git").exists():
            return parent
    return None


def check_git_refs(handoff: dict, repo: Path) -> list[dict]:
    """Every declared commit must be a real object in the repo."""
    problems = []
    snapshot = handoff.get("snapshot") or {}
    for field in GIT_REF_FIELDS:
        value = snapshot.get(field)
        if not isinstance(value, str) or not value:
            continue
        code, out = _git(repo, "cat-file", "-t", value)
        if code != 0:
            problems.append({
                "kind": "git_ref_missing",
                "field": "snapshot." + field,
                "value": value,
                "detail": out.strip()[:200] or "not a git object",
            })
        elif out.strip() not in ("commit",):
            problems.append({
                "kind": "git_ref_wrong_type",
                "field": "snapshot." + field,
                "value": value,
                "detail": "object type is " + out.strip(),
            })
    return problems


def check_paths_exist(handoff: dict, repo: Path) -> list[dict]:
    """Every changed_path must exist on disk or in the repo's history."""
    problems = []
    changed = (handoff.get("scope") or {}).get("changed_paths") or []
    if not changed:
        return problems
    # One pass over history instead of one `git log` per path.
    code, tracked = _git(repo, "log", "--all", "--name-only", "--pretty=format:")
    known = set()
    if code == 0:
        for line in tracked.splitlines():
            line = line.strip().replace("\\", "/")
            if line:
                known.add(line.casefold())
    for value in changed:
        rel = str(value).replace("\\", "/").lstrip("./")
        if (repo / rel).exists():
            continue
        if rel.casefold() in known:
            continue
        problems.append({"kind": "changed_path_missing", "path": rel,
                         "detail": "absent on disk and in git history"})
    return problems


def check_interface_hashes(handoff: dict, repo: Path) -> list[dict]:
    """Every interface content_hash must match a local file, unless it is a
    declared external input.

    Interfaces split into two kinds. A `consumed` interface names an artifact the
    package read from elsewhere (the data root, another repo) — its hash will never
    match a file here, and demanding that would be a false positive. A `produced`
    or `both` interface names something this package ships, so its hash must
    resolve locally. Only the latter are checked.
    """
    problems = []
    interfaces = handoff.get("interfaces") or []
    if not interfaces:
        return problems
    local = {}
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            if path.stat().st_size > 8_000_000:
                continue
            local[hashlib.sha256(path.read_bytes()).hexdigest()] = str(
                path.relative_to(repo).as_posix())
        except OSError:
            continue
    for interface in interfaces:
        direction = interface.get("direction")
        if direction == "consumed":
            # Declared input from outside this delivery; nothing local to match.
            continue
        value = interface.get("content_hash")
        if not isinstance(value, str) or len(value) != 64:
            continue
        try:
            int(value, 16)
        except ValueError:
            problems.append({"kind": "interface_hash_not_hex",
                             "name": interface.get("name"), "value": value})
            continue
        if value in local:
            continue
        problems.append({
            "kind": "interface_hash_unmatched",
            "name": interface.get("name"),
            "direction": direction,
            "value": value,
            "detail": "matches no file in the delivery repo",
        })
    return problems


def check_artifacts_self_hashes(handoff_path: Path, repo: Path) -> list[dict]:
    """artifacts.json entries must hash to what they claim.

    Skips the handoff metadata set itself (artifacts.json, handoff.json,
    tests.json, cleanup.json, summary.md, report.md). Those files are written
    before or while the manifest is finalised, so a manifest that hashed them
    could never be self-consistent; demanding it would only force churn. Every
    other entry — source, data, logs, demo artifacts — must match.
    """
    problems = []
    artifacts_path = handoff_path.parent / "artifacts.json"
    if not artifacts_path.is_file():
        return problems
    metadata = {name.casefold() for name in (
        "artifacts.json", "handoff.json", "tests.json", "cleanup.json",
        "summary.md", "report.md")}
    try:
        document = json.loads(artifacts_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [{"kind": "artifacts_unreadable", "path": str(artifacts_path)}]
    entries = document.get("artifacts") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        return problems
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        rel = entry.get("path")
        declared = entry.get("sha256")
        if not isinstance(rel, str) or not isinstance(declared, str) or len(declared) != 64:
            continue
        if PurePosixPath(rel.replace("\\", "/")).name.casefold() in metadata:
            continue
        target = repo / rel
        if not target.is_file():
            continue
        try:
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError:
            continue
        if actual != declared:
            problems.append({
                "kind": "artifact_hash_mismatch",
                "path": rel,
                "declared": declared,
                "actual": actual,
            })
    return problems


def verify_all(handoff: dict, handoff_path: Path) -> list[dict]:
    repo = repo_of(handoff, handoff_path)
    if repo is None:
        return [{"kind": "repo_not_found",
                 "detail": "no snapshot.repository and no enclosing git worktree"}]
    problems = []
    problems += check_git_refs(handoff, repo)
    problems += check_paths_exist(handoff, repo)
    problems += check_interface_hashes(handoff, repo)
    problems += check_artifacts_self_hashes(handoff_path, repo)
    return problems
