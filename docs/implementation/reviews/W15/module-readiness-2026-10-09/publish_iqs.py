"""Once-only exact W15 IQS code/PWF/evidence commit and normal push."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "docs/implementation/intake/W15/module-readiness-2026-10-09"
REVIEW = Path(__file__).resolve().parent
BASE = "469d11b127dc908fd0713f1e944459b60bff0a1d"
PUBLIC = ["scripts/route_store_handoff.py", "tests/test_route_store_handoff.py",
          "schemas/quick_scan/route-store-validation.schema.json", "schemas/quick_scan/module-refresh.schema.json",
          "schemas/quick_scan/route-store-cli.schema.json"]
PWF = [".gitattributes", "task_plan.md", "progress.md", "findings.md", "docs/implementation/handoff-for-new-agent.md"]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    assert not (ROOT / "runs/w15a").exists(), "Owned runtime must be cleaned first"
    e = {k: v for k, v in os.environ.items() if k.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMDRIVE"}}
    e.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, env=e)
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    assert not git("diff", "--cached", "--name-only")
    cleaned = json.loads((OUT / "cleanup-receipt.json").read_text("utf-8-sig"))
    assert cleaned["applied"] and cleaned["process_matches"] == 0
    publication = json.loads((OUT / "source-publication/result.json").read_bytes())
    assert publication["source_published"]
    assert json.loads((REVIEW / "review/concentrated-recheck-02.json").read_bytes())["software_open_findings"] == 0
    for entry in filter(None, git("status", "--porcelain=v1", "-uall", "-z").decode().split("\0")):
        name = entry[3:]
        assert name in PUBLIC + PWF + ["opencode.json"] or name.startswith((OUT.relative_to(ROOT).as_posix()+"/", REVIEW.relative_to(ROOT).as_posix()+"/")), entry
    paths = sorted(set(PUBLIC + PWF + [p.relative_to(ROOT).as_posix()
                 for folder in (OUT, REVIEW) for p in folder.rglob("*") if p.is_file()]))
    assert "opencode.json" not in paths
    expected = {n: sha((ROOT/n).read_bytes()) for n in paths}
    target = OUT / "iqs-publication"
    assert not target.exists()
    target.mkdir()
    selection = target / "selected-before.json"
    selection.write_text(json.dumps(dict(base=BASE, selected=expected, preserved_unknown="opencode.json not read or staged"), indent=2)+"\n", encoding="utf-8")
    paths.append(selection.relative_to(ROOT).as_posix())
    expected[paths[-1]] = sha(selection.read_bytes())
    git("add", "--", *PUBLIC, *PWF)
    # Only verified exact evidence paths need -f because the project ignores logs.
    artifacts = [p for p in paths if p not in PUBLIC + PWF]
    for offset in range(0, len(artifacts), 75):
        git("add", "-f", "--", *artifacts[offset:offset+75])
    staged = set(filter(None, git("diff", "--cached", "--name-only", "-z").decode().split("\0")))
    assert staged == set(paths)
    oids = {}
    for entry in filter(None, git("ls-files", "--stage", "-z").decode().split("\0")):
        meta, name = entry.split("\t", 1)
        if name in expected:
            _, oid, stage = meta.split()
            assert stage == "0"
            oids[name] = oid
    proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT, env=e,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data, error = proc.communicate(("\n".join(oids[n] for n in paths)+"\n").encode(), timeout=120)
    assert proc.returncode == 0, error
    cursor = 0
    for n in paths:
        end = data.index(b"\n", cursor)
        oid, kind, size = data[cursor:end].decode().split()
        cursor = end + 1
        raw = data[cursor:cursor+int(size)]
        assert oid == oids[n] and kind == "blob"
        current = (ROOT/n).read_bytes()
        assert sha(current) == expected[n]
        assert raw == current or (n in PWF + PUBLIC and raw == current.replace(b"\r\n", b"\n")), n
        cursor += int(size) + 1
    assert cursor == len(data)
    def recorded(label, args):
        started = time.monotonic()
        p = subprocess.Popen(["git", *args], cwd=ROOT, env=e, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(json.dumps(dict(label=label, pid=p.pid)), flush=True)
        stdout, stderr = p.communicate(timeout=600)
        (target/(label+".stdout.log")).write_bytes(stdout)
        (target/(label+".stderr.log")).write_bytes(stderr)
        (target/(label+".process.json")).write_text(json.dumps(dict(returncode=p.returncode, pid=p.pid,
            terminal_confirmed=True, wall_s=round(time.monotonic()-started,3), normal_hooks=True,
            stdout_sha256=sha(stdout), stderr_sha256=sha(stderr)), indent=2)+"\n", encoding="utf-8")
        print((stdout+stderr).decode("utf-8",errors="replace")[-1800:])
        assert p.returncode == 0
    recorded("diff-check", ["diff", "--cached", "--check"])
    recorded("commit", ["commit", "-m", "Deliver modular quick scan refresh foundation and reviewed cross-repo handoff"])
    commit = git("rev-parse", "HEAD").decode().strip()
    assert set(filter(None, git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit).decode().split("\0"))) == set(paths)
    recorded("push", ["push", "origin", "master"])
    remote = git("ls-remote", "origin", "refs/heads/master").decode().split()[0]
    assert commit == remote
    (target/"result.json").write_text(json.dumps(dict(commit=commit, remote_head=remote,
        selected_paths=len(paths), normal_hooks=True, force_push=False, preserved_unknown="opencode.json",
        artifact_staged_bytes_identical=True, source_publication=publication["sources"],
        whole_W15_complete=False), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(commit=commit, remote_head=remote, selected_paths=len(paths))))


if __name__ == "__main__":
    main()
