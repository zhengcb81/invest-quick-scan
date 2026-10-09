"""Reconcile this batch's reviewed EOL-only hook changes into its private copy.

The external checkout and its Git index are read-only here. Immutable intent is
written before any private copy changes, so interrupted copies can resume only
under the same helper and the same complete set of inputs.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/model-resolution-2026-10-09-01"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-model-resolution"
SOURCE = Path("C:/Users/郑曾波/Projects/StockQAbyLLM")
ORIGINAL_LABEL = "model-release-01"
ARCHIVE = OUT / "eol-reconciliation"
PROOF = OUT / "eol-source-proof.json"
EXPECTED_NEW = {
    "src/providers/model_resolution.py",
    "src/config/quick_scan_model_resolution.schema.json",
    "tests/unit/test_model_resolution.py",
    "tests/unit/test_async_llm_provider.py",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized(raw):
    # This is exactly the normalization recorded by the original collector.
    return raw.replace(b"\r\n", b"\n")


def safe_path(root, relative):
    require(isinstance(relative, str) and relative and "\\" not in relative,
            "Invalid relative evidence/source path")
    parts = relative.split("/")
    require(all(part not in {"", ".", ".."} and ":" not in part for part in parts),
            "Invalid relative evidence/source path")
    root = Path(root)
    path = root.joinpath(*parts)
    require(root.is_absolute() and root.resolve() == root and path.resolve() == path
            and path.is_relative_to(root), "Path leaves its exact root: " + relative)
    for current in (root, *list(path.parents)[:len(parts) - 1], path):
        if current.exists() or current.is_symlink():
            info = current.lstat()
            require(not stat.S_ISLNK(info.st_mode)
                    and not getattr(info, "st_file_attributes", 0) & 0x400,
                    "Reparse point/symlink forbidden: " + str(current))
            if stat.S_ISREG(info.st_mode):
                require(info.st_nlink == 1, "Hardlink forbidden: " + str(current))
    return path


def read(root, relative):
    path = safe_path(root, relative)
    require(path.is_file(), "Required file missing: " + str(path))
    return path.read_bytes()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON evidence key")
        result[key] = value
    return result


def decode(raw):
    def invalid_constant(value):
        raise RuntimeError("Nonfinite JSON evidence constant: " + value)
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


def json_bytes(body):
    return (json.dumps(body, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def write_once(root, relative, raw):
    path = safe_path(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def preserve_once(root, relative, raw):
    path = safe_path(root, relative)
    if path.exists():
        require(read(root, relative) == raw, "Existing immutable evidence differs: " + relative)
    else:
        write_once(root, relative, raw)


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(SOURCE), *args])


def load_original(archived=False):
    baseline_raw = read(OUT, "source-baseline.json")
    inventory_raw = read(OUT, "source-snapshot.json")
    extra_raw = read(OUT, "extra-baseline.json")
    scope_raw = read(Path(__file__).parent, "scope.json")
    baseline, inventory, extras, scope = map(decode, (baseline_raw, inventory_raw, extra_raw, scope_raw))
    require(Path(baseline["source"]) == SOURCE and scope["source"] == baseline["source"]
            and scope["baseline"] == baseline["head"], "Source baseline identity differs")
    require(scope["isolated_root"] == "runs/model-resolution-2026-10-09-01/qa",
            "Isolated root differs")
    require(len(extras) == 1 and extras[0]["path"] == ".gitignore", "Unexpected extra baseline")
    before = {row["path"]: row for row in inventory}
    require(len(before) == len(inventory) == 136 and ".gitignore" not in before,
            "Original 136-path inventory differs")
    before[".gitignore"] = extras[0]
    relative = "snapshots/" + ORIGINAL_LABEL + "/source.json"
    originals = {
        "original-approval-for-publish.json": read(OUT, "approval-for-publish.json"),
        "original-publish-receipt.json": read(OUT, "publish-receipt.json"),
        "original-source.json": read(OUT, relative),
    }
    if archived:
        for name, raw in originals.items():
            require(read(ARCHIVE, name) == raw, "Original evidence changed: " + name)
    approval, publication, manifest = map(decode, originals.values())
    manifest_sha = sha(originals["original-source.json"])
    require(approval["schema"] == "model_resolution_publish_approval/1"
            and approval["approved_for_model_resolution_publish"] is True
            and approval["snapshot_label"] == ORIGINAL_LABEL
            and approval["reviewed_source_sha256"] == manifest_sha,
            "Original approval is not bound to snapshot01")
    require(publication["schema"] == "model_resolution_publish/1"
            and publication["applied"] is True
            and publication["expected_files"] == publication["published_files"] == 24
            and publication["baseline_head"] == baseline["head"]
            and publication["exact_reviewed_sha256"] == manifest_sha
            and publication["other_repositories_written"] is False
            and publication["paid_calls"] == 0, "Original publish receipt differs")
    require(manifest["schema"] == "model_resolution_reviewed_source/1"
            and manifest["source_baseline"] == baseline,
            "Original snapshot baseline differs")
    rows = manifest["changed_files"]
    names = [row["path"] for row in rows]
    require(len(names) == len(set(names)) == 24
            and names == approval["approved_paths"]
            and set(names) == set(scope["files"]), "Reviewed 24-path scope differs")
    require({row["path"] for row in rows if row["before_sha256"] is None} == EXPECTED_NEW
            and set(names) - set(before) == EXPECTED_NEW, "Original new-file provenance differs")
    for row in rows:
        previous = before.get(row["path"])
        require(row["before_sha256"] == (previous["sha256"] if previous else None),
                "Original before SHA differs: " + row["path"])
        raw = read(OUT, "snapshots/" + ORIGINAL_LABEL + "/source/" + row["path"])
        require(len(raw) == row["bytes"] and sha(raw) == row["sha256"]
                and sha(normalized(raw)) == row["normalized_lf_sha256"],
                "Original snapshot bytes differ: " + row["path"])
    require(len(set(before) - set(names)) == 117, "Protected 117-path inventory differs")
    hashes = dict(original_manifest_sha256=manifest_sha,
                  original_approval_sha256=sha(originals["original-approval-for-publish.json"]),
                  original_publish_receipt_sha256=sha(originals["original-publish-receipt.json"]),
                  source_baseline_sha256=sha(baseline_raw), source_inventory_sha256=sha(inventory_raw),
                  extra_baseline_sha256=sha(extra_raw), scope_sha256=sha(scope_raw))
    return dict(baseline=baseline, before=before, rows=rows, manifest=manifest,
                approval=approval, publication=publication, originals=originals, hashes=hashes)


def verify_checkout(context):
    baseline, rows = context["baseline"], context["rows"]
    names = {row["path"] for row in rows}
    head = git("rev-parse", "HEAD").decode("utf-8").strip()
    branch = git("branch", "--show-current").decode("utf-8").strip()
    require(head == baseline["head"] and branch == "master", "External HEAD/branch changed")
    staged_raw = git("diff", "--cached", "--name-only", "--no-renames", "-z")
    staged = staged_raw.decode("utf-8").split("\0")
    require(staged[-1] == "" and len(staged[:-1]) == len(set(staged[:-1])) == 24
            and set(staged[:-1]) == names, "External index is not precisely the reviewed 24 paths")
    status = git("status", "--porcelain=v1").decode("utf-8")
    lines = status.splitlines()
    require([line for line in lines if line[3:] not in names] == baseline["status"].splitlines(),
            "External status outside reviewed paths changed")
    scoped = [line for line in lines if line[3:] in names]
    require(len(scoped) == 24 and {line[3:] for line in scoped} == names,
            "External scoped status differs")
    for line in scoped:
        expected = "A" if line[3:] in EXPECTED_NEW else "M"
        require(line[0] == expected and line[1] in {" ", "M"},
                "Unexpected staged/worktree state: " + line[3:])
    source_raw, staged_rows = {}, []
    changed_eol = set()
    expected_eol = {row["path"] for row in rows if row["sha256"] != row["normalized_lf_sha256"]}
    require(len(expected_eol) == 11, "Original 11 EOL-sensitive rows differ")
    for row in rows:
        name = row["path"]
        raw = read(SOURCE, name)
        require(sha(normalized(raw)) == row["normalized_lf_sha256"],
                "External functional drift: " + name)
        if sha(raw) != row["sha256"]:
            changed_eol.add(name)
            require(name in expected_eol and sha(raw) == row["normalized_lf_sha256"],
                    "External change is not the expected LF hook result: " + name)
        index_raw = git("show", ":" + name)
        require(sha(normalized(index_raw)) == row["normalized_lf_sha256"],
                "Unreviewed staged bytes: " + name)
        staged_rows.append(dict(path=name, bytes=len(index_raw), sha256=sha(index_raw),
                                normalized_lf_sha256=sha(normalized(index_raw))))
        source_raw[name] = raw
    require(changed_eol == expected_eol, "Expected 11 hook-only EOL changes differ")
    protected = []
    for name in sorted(set(context["before"]) - names):
        row = context["before"][name]
        external, owned = read(SOURCE, name), read(OWN / "qa", name)
        require(sha(external) == sha(owned) == row["sha256"]
                and len(external) == len(owned) == row["bytes"],
                "Protected raw source changed: " + name)
        protected.append(dict(path=name, bytes=row["bytes"], before_sha256=row["sha256"],
                              source_sha256=sha(external), owned_sha256=sha(owned)))
    return dict(head=head, branch=branch, status=status, staged_paths=sorted(names),
                staged_files=staged_rows, protected_files=protected), source_raw


def owned_inventory(context):
    root = OWN / "qa"
    safe_path(OWN, "qa")
    paths = set()
    for current, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            relative = (Path(current) / name).relative_to(root).as_posix()
            path = safe_path(root, relative)
            info = path.lstat()
            require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),
                    "Unexpected owned filesystem entry: " + relative)
            if stat.S_ISREG(info.st_mode):
                paths.add(relative)
    source_paths = set(context["before"]) | {row["path"] for row in context["rows"]}
    require(source_paths <= paths, "Protected owned source missing")
    generated = paths - source_paths
    require(generated <= {"logs/stock_qa_20261009.log"}, "Unclassified owned source/output")
    return [dict(path=name, bytes=len(read(root, name)), sha256=sha(read(root, name)),
                 classification="Owner logger output from isolated tests; only deleted with exact OWN cleanup")
            for name in sorted(generated)]


def load_completed_proof(context):
    proof_raw = read(OUT, "eol-source-proof.json")
    proof = decode(proof_raw)
    intent_raw = read(ARCHIVE, "copy-intent.json")
    intent = decode(intent_raw)
    helper_sha = sha(Path(__file__).read_bytes())
    require(proof["schema"] == "model_resolution_eol_source_proof/1"
            and proof["owned_copy_complete"] is True
            and proof["copy_intent_sha256"] == sha(intent_raw)
            and proof["helper_sha256"] == intent["helper_sha256"] == helper_sha
            and intent["schema"] == "model_resolution_eol_copy_intent/1"
            and intent["original_evidence"] == proof["original_evidence"] == context["hashes"]
            and intent["source_baseline"] == proof["source_baseline"] == context["baseline"]
            and intent["original_snapshot_label"] == proof["original_snapshot_label"] == ORIGINAL_LABEL
            and intent["source_read_only"] is True and intent["copy_target"] == str(OWN / "qa"),
            "Completed EOL proof/intent binding differs")
    require(proof["external_source_written"] is False and proof["git_written"] is False
            and proof["tests_executed"] is False, "EOL proof claims unexpected actions")
    return proof, intent, sha(proof_raw)


def verify_published_eol():
    context = load_original(archived=True)
    proof, intent, proof_sha = load_completed_proof(context)
    checkout, source_raw = verify_checkout(context)
    require(checkout == intent["checkout"] == proof["checkout"], "External EOL proof drift")
    original = {row["path"]: row for row in context["rows"]}
    require(len(intent["files"]) == 24 and {row["path"] for row in intent["files"]} == set(original)
            and proof["files"] == intent["files"], "EOL proof row set differs")
    for row in intent["files"]:
        name = row["path"]
        old = original[name]
        owned = read(OWN / "qa", name)
        require(owned == source_raw[name] and len(owned) == row["current_bytes"]
                and sha(owned) == row["source_current_sha256"] == row["owned_target_sha256"]
                and row["owned_original_sha256"] == row["owned_before_sha256"] == old["sha256"]
                and row["before_sha256"] == old["before_sha256"]
                and row["original_bytes"] == old["bytes"]
                and row["eol_changed"] is (sha(owned) != old["sha256"])
                and sha(normalized(owned)) == row["normalized_lf_sha256"] == old["normalized_lf_sha256"],
                "Owned/source EOL proof drift: " + name)
    context.update(checkout=checkout, source_raw=source_raw, proof=proof, proof_sha256=proof_sha,
                   copy_intent_sha256=proof["copy_intent_sha256"], generated=owned_inventory(context))
    return context


def main():
    context = load_original()
    checkout, source_raw = verify_checkout(context)
    owned_inventory(context)
    helper_sha = sha(Path(__file__).read_bytes())
    intent_path = safe_path(ARCHIVE, "copy-intent.json")
    if intent_path.exists():
        # Existing target bytes are allowed only with this exact helper's intent.
        intent_raw = read(ARCHIVE, "copy-intent.json")
        intent = decode(intent_raw)
        require(intent["schema"] == "model_resolution_eol_copy_intent/1"
                and intent["helper_sha256"] == helper_sha
                and intent["original_evidence"] == context["hashes"]
                and intent["source_baseline"] == context["baseline"]
                and intent["original_snapshot_label"] == ORIGINAL_LABEL
                and intent["source_read_only"] is True and intent["copy_target"] == str(OWN / "qa")
                and intent["checkout"] == checkout, "Existing copy intent differs")
        for name, raw in context["originals"].items():
            require(read(ARCHIVE, name) == raw, "Archived original differs: " + name)
    else:
        rows = []
        for old in context["rows"]:
            name = old["path"]
            owned = read(OWN / "qa", name)
            require(len(owned) == old["bytes"] and sha(owned) == old["sha256"],
                    "OWN is not the reviewed original before intent: " + name)
            rows.append(dict(path=name, before_sha256=old["before_sha256"],
                             original_bytes=old["bytes"], owned_original_sha256=old["sha256"],
                             owned_before_sha256=sha(owned), current_bytes=len(source_raw[name]),
                             source_current_sha256=sha(source_raw[name]), owned_target_sha256=sha(source_raw[name]),
                             normalized_lf_sha256=old["normalized_lf_sha256"],
                             eol_changed=sha(source_raw[name]) != old["sha256"]))
        intent = dict(schema="model_resolution_eol_copy_intent/1", helper_sha256=helper_sha,
                      original_snapshot_label=ORIGINAL_LABEL, original_evidence=context["hashes"],
                      source_baseline=context["baseline"], checkout=checkout, files=rows,
                      source_read_only=True, copy_target=str(OWN / "qa"))
        intent_raw = json_bytes(intent)
        for name, raw in context["originals"].items():
            preserve_once(ARCHIVE, name, raw)
        write_once(ARCHIVE, "copy-intent.json", intent_raw)
    originals = {row["path"]: row for row in context["rows"]}
    require(len(intent["files"]) == 24 and {row["path"] for row in intent["files"]} == set(originals),
            "Intent row set differs")
    prepared = []
    for row in intent["files"]:
        name, old = row["path"], originals[row["path"]]
        raw, owned = source_raw[name], read(OWN / "qa", name)
        require(row["owned_original_sha256"] == row["owned_before_sha256"] == old["sha256"]
                and row["before_sha256"] == old["before_sha256"]
                and row["source_current_sha256"] == row["owned_target_sha256"] == sha(raw)
                and row["current_bytes"] == len(raw)
                and row["normalized_lf_sha256"] == old["normalized_lf_sha256"]
                and row["original_bytes"] == old["bytes"]
                and row["eol_changed"] is (sha(raw) != old["sha256"]), "Intent file binding differs: " + name)
        require(sha(owned) in {old["sha256"], sha(raw)}, "OWN drift outside this intent: " + name)
        prepared.append((name, raw, owned))
    # Freeze every input and destination before the first private write.
    second_checkout, second_raw = verify_checkout(context)
    require(second_checkout == checkout and second_raw == source_raw, "Source changed during preflight")
    require(all(read(OWN / "qa", name) == owned for name, _, owned in prepared),
            "OWN changed during preflight")
    copied = []
    for name, raw, owned in prepared:
        if raw != owned:
            path = safe_path(OWN / "qa", name)
            require(path.read_bytes() == owned, "OWN changed before copy: " + name)
            path.write_bytes(raw)
            require(path.read_bytes() == raw, "Private raw copy failed: " + name)
            copied.append(name)
    final_checkout, final_raw = verify_checkout(context)
    require(final_checkout == checkout and final_raw == source_raw
            and all(read(OWN / "qa", name) == raw for name, raw in source_raw.items()),
            "Post-copy source/OWN drift")
    proof = dict(schema="model_resolution_eol_source_proof/1", helper_sha256=helper_sha,
                 original_snapshot_label=ORIGINAL_LABEL, original_evidence=context["hashes"],
                 source_baseline=context["baseline"], copy_intent_sha256=sha(intent_raw),
                 checkout=checkout, files=intent["files"], eol_changed_files=11,
                 protected_raw_unchanged_files=117, owned_copy_complete=True,
                 external_source_written=False, git_written=False, tests_executed=False,
                 proof_limit="Known 137 source paths and exact Git status; original seven unknown paths are not opened")
    preserve_once(OUT, "eol-source-proof.json", json_bytes(proof))
    verify_published_eol()
    print(json.dumps(dict(owned_files_copied=len(copied), eol_changed_files=11,
                          protected_raw_files=117, proof_sha256=sha(read(OUT, "eol-source-proof.json")),
                          external_source_written=False, git_written=False, tests_executed=False)))


if __name__ == "__main__":
    main()
