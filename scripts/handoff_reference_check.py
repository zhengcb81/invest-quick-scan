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
import re
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


def _rel_of(value: str) -> str:
    """Normalize a declared path for existence checks.

    Strip only a leading './' — lstrip('./') would also eat a leading dot, so
    '.gitignore' would wrongly become 'gitignore' and be reported missing.
    """
    text = str(value).replace("\\", "/")
    if text.startswith("./"):
        text = text[2:]
    return text


def external_roots(handoff: dict) -> list[Path]:
    """Directory paths the handoff itself points at, for cross-repo references.

    An interface may legitimately name a file in another repo (a UI resolver
    contract, for instance). Those commands are handoff claims too, so a path
    declared inside a check command is itself a reference worth resolving:
    only an existing directory is added, and only as a search root.
    """
    roots: list[Path] = []
    for check in (handoff.get("verification") or {}).get("checks") or []:
        command = check.get("command")
        if not isinstance(command, str):
            continue
        for match in re.finditer(r'[A-Za-z]:[\\/][^\s"\'|;]+', command):
            candidate = Path(match.group(0).replace("\\", "/"))
            if candidate.is_dir() and candidate not in roots:
                roots.append(candidate)
    return roots


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
        rel = _rel_of(value)
        if (repo / rel).exists():
            continue
        if rel.casefold() in known:
            continue
        problems.append({"kind": "changed_path_missing", "path": rel,
                         "detail": "absent on disk and in git history"})
    return problems


def _index_dir(root: Path) -> dict[str, str]:
    """sha256 -> relative path for files under root (read-only).

    In a git worktree only tracked files are hashed: a delivered interface is
    committed by definition, while untracked run artifacts here run to gigabytes.
    Non-git roots fall back to a walk (external roots declared by a command are
    often plain directories).
    """
    index: dict[str, str] = {}
    if (root / ".git").exists():
        code, out = _git(root, "ls-files", "-z")
        if code == 0:
            for rel in (entry for entry in out.split("\0") if entry):
                path = root / rel
                try:
                    if not path.is_file() or path.stat().st_size > 33_554_432:
                        continue
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    index.setdefault(digest, rel.replace("\\", "/"))
                except OSError:
                    continue
            return index
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            # 32 MiB covers the delivered UI export (8.4 MB); hashing must not
            # silently skip a file an interface claims to hash.
            if path.stat().st_size > 33_554_432:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            index.setdefault(digest, str(path.relative_to(root).as_posix()))
        except OSError:
            continue
    return index


def _blob_sha256s(repo: Path, commit: str, rel: str) -> tuple[str, ...]:
    """Every byte form ``rel`` has had at ``commit``: filtered, raw, and unfiltered.

    Handoffs describe the tree at ``result_commit``, not today's worktree. A later
    package may legitimately rewrite a shared file, so a declared hash has to be
    judged against the commit first and the worktree second — otherwise every
    follow-up refactor turns an already accepted handoff red.

    Three forms are returned because generators differ on this machine: some hash
    worktree bytes (CRLF after core.autocrlf), some hash the raw blob (LF), and
    ``cat-file --filters`` reproduces the worktree form. Accepting all three keeps
    the check about *which content* was delivered rather than *which newline form*
    the writer happened to read.
    """
    if not commit:
        return ()
    forms: list[str] = []
    for args in (("cat-file", "--filters", f"{commit}:{rel}"),
                 ("show", f"{commit}:{rel}")):
        try:
            proc = subprocess.run(["git", *args], cwd=repo,
                                  capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            break
        if proc.returncode == 0:
            digest = hashlib.sha256(proc.stdout).hexdigest()
            if digest not in forms:
                forms.append(digest)
    return tuple(forms)


def _blob_sha256(repo: Path, commit: str, rel: str) -> str | None:
    """First available byte form of ``rel`` at ``commit`` (see ``_blob_sha256s``)."""
    forms = _blob_sha256s(repo, commit, rel)
    return forms[0] if forms else None


_VERSION_REF_RE = re.compile(r"^(?P<path>[\w./-]+\.\w+)\s*@\s*(?P<ref>[0-9a-f]{7,40})\b")


def _declared_pin(interface: dict) -> tuple[str, str] | None:
    """Parse ``"<path> @ <commit>"`` out of an interface's version field.

    A handoff may pin an interface to a commit rather than to the delivery HEAD —
    APPLIC-RESOLVE-14 names ``adapters/contracts.py @ 9ab7a339``, a UI commit that
    predates the package. The hash describes that tree, so it must be resolved
    against that commit or the check reports a false failure.
    """
    version = interface.get("version")
    if not isinstance(version, str):
        return None
    match = _VERSION_REF_RE.match(version.strip())
    if not match:
        return None
    return match.group("path"), match.group("ref")


def _candidate_paths(handoff: dict, handoff_path: Path) -> list[str]:
    """Paths the handoff itself names: artifacts entries plus changed_paths."""
    seen: list[str] = []
    artifacts_path = handoff_path.parent / "artifacts.json"
    try:
        document = json.loads(artifacts_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        document = None
    entries = document.get("artifacts") if isinstance(document, dict) else None
    for entry in entries or []:
        rel = entry.get("path") if isinstance(entry, dict) else None
        if isinstance(rel, str) and rel not in seen:
            seen.append(rel)
    for rel in (handoff.get("scope") or {}).get("changed_paths") or []:
        if isinstance(rel, str) and rel not in seen:
            seen.append(rel)
    return seen


def check_interface_hashes(handoff: dict, repo: Path, commit: str = "",
                           handoff_path: Path | None = None) -> list[dict]:
    """Every interface content_hash must match a local file, unless it is a
    declared external input.

    Interfaces split into two kinds. A `consumed` interface names an artifact the
    package read from elsewhere (the data root, another repo) — its hash will never
    match a file here, and demanding that would be a false positive. A `produced`
    or `both` interface names something this package ships, so its hash must
    resolve locally or in a repo the handoff itself names in a check command.

    Lookups are lazy on purpose: hash the delivery repo once, then walk external
    roots one at a time only for hashes the repo cannot satisfy, stopping at the
    first hit. Eagerly hashing a data-root the size of this workspace took
    forty minutes; the lazy order takes seconds.
    """
    problems = []
    interfaces = handoff.get("interfaces") or []
    if not interfaces:
        return problems
    pending: list[dict] = []
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
        pending.append({**interface, "content_hash": value})
    if not pending:
        return problems

    local = _index_dir(repo)
    externals = [r for r in external_roots(handoff) if r != repo]
    extern_index: dict[Path, dict[str, str]] = {}
    commit_index: dict[str, str] | None = None
    for interface in pending:
        value = interface["content_hash"]
        if value in local:
            continue
        for root in externals:
            if root not in extern_index:
                extern_index[root] = _index_dir(root)
            if value in extern_index[root]:
                break
        else:
            # 接口可能把版本钉在某个 commit 上（"path @ <sha>"），
            # 此时哈希描述的是那个 tree，而不是交付 HEAD。
            pin = _declared_pin(interface)
            if pin is not None:
                pin_path, pin_ref = pin
                matched = False
                for root_dir in [repo, *externals]:
                    if value in _blob_sha256s(root_dir, pin_ref, pin_path):
                        matched = True
                        break
                if matched:
                    continue
                problems.append({
                    "kind": "interface_hash_unmatched",
                    "name": interface.get("name"),
                    "direction": interface.get("direction"),
                    "value": value,
                    "detail": (f"pinned to {pin_ref[:9]}:{pin_path} "
                               "but that blob does not hash to it"),
                })
                continue
            if commit_index is None:
                commit_index = {}
                candidates = (_candidate_paths(handoff, handoff_path)
                              if handoff_path is not None
                              else list((handoff.get("scope") or {}).get("changed_paths") or []))
                for rel in candidates:
                    for digest in _blob_sha256s(repo, commit, rel):
                        commit_index.setdefault(digest, rel)
            if value in commit_index:
                continue
            problems.append({
                "kind": "interface_hash_unmatched",
                "name": interface.get("name"),
                "direction": interface.get("direction"),
                "value": value,
                "detail": "matches no file in the delivery repo, its result commit, or declared repos",
            })
    return problems


def check_artifacts_self_hashes(handoff_path: Path, repo: Path,
                                commit: str = "") -> list[dict]:
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
            # A later package may have rewritten this file; the handoff still
            # describes the tree at result_commit, so accept that match.
            if declared in _blob_sha256s(repo, commit, rel.replace("\\", "/")):
                continue
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
    problems += check_interface_hashes(
        handoff, repo, commit=((handoff.get("snapshot") or {}).get("result_commit") or ""),
        handoff_path=handoff_path,
    )
    problems += check_artifacts_self_hashes(
        handoff_path, repo,
        commit=((handoff.get("snapshot") or {}).get("result_commit") or ""),
    )
    return problems
