"""Publish and read immutable scored-question module packages.

The editable catalog is the authoring source. Runs read the content-addressed
archives, while ``current.json`` only chooses which verified package is active.
No network access or company data is involved.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import module_contract as contract


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PATTERN = re.compile(r"^pkg_[a-f0-9]{64}$")
RELEASE_PATTERN = re.compile(r"^modrel_[a-f0-9]{64}$")
LEGACY_BASELINE_RELEASE_ID = "modrel_18c097b26b82746d3b48d9f2da4858a15ce216bce39c2572d10c2dcef23d32b9"
LEGACY_BASELINE_SHA256 = "0a128fa569efae7c1b06948a142fb67dead78812d1ccfce6087de21753f28ab3"
LEGACY_BASELINE_IDS = frozenset(
    "common operating bank insurer capital_markets property_owner property_developer holding "
    "pre_revenue software internet semiconductors hardware industrial auto consumer retail "
    "healthcare medtech resources materials utilities telecom transport energy_transition "
    "agriculture professional_services construction leisure_media other validation "
    "commercialization scaling mature cyclical turnaround declining cross_border controlled "
    "listing_structure concentrated acquisitive subsidized distressed recent_listing "
    "dupont porter recovery".split()
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_bytes().decode("utf-8-sig"),
                      object_pairs_hook=contract._unique_object)


def _reject_symlink_components(path: Path, root: Path, message: str) -> None:
    """Reject a symlink anywhere below the caller-selected storage root."""
    root_abs = Path(os.path.abspath(root))
    path_abs = Path(os.path.abspath(path))
    if not path_abs.is_relative_to(root_abs):
        raise ValueError(message)
    candidate = path_abs
    while candidate != root_abs:
        is_junction = getattr(candidate, "is_junction", None)
        if candidate.is_symlink() or (callable(is_junction) and is_junction()):
            raise ValueError(message)
        candidate = candidate.parent


def _safe_path(root: Path, reference: str) -> Path:
    """Reject paths and symlinks that could escape the local release store."""
    if not isinstance(reference, str) or not reference.startswith("questions/releases/"):
        raise ValueError("invalid release artifact reference")
    root = Path(root)
    path = root / reference
    releases = root / "questions" / "releases"
    _reject_symlink_components(path, root, "release archive symlink is forbidden")
    if not path.resolve().is_relative_to(releases.resolve()):
        raise ValueError("release artifact leaves the archive directory")
    return path


def _atomic_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".publish-", delete=False) as handle:
        handle.write(raw)
        temp_path = Path(handle.name)
    try:
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _write_immutable(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError(f"immutable release artifact changed: {path.name}")
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".publish-", delete=False) as handle:
        handle.write(raw)
        temp_path = Path(handle.name)
    try:
        # The caller checks for an existing artifact before publishing; this
        # replace is only of a newly created content-addressed path.
        if path.exists():
            if path.read_bytes() != raw:
                raise ValueError("immutable release artifact changed concurrently")
        else:
            os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def source_catalog(root: Path = ROOT) -> tuple[dict, dict[str, dict], dict[str, bytes]]:
    """Read the sole editable scored catalog, rejecting duplicate registration."""
    catalog = _read_json(root / "questions" / "catalog.json")
    entries = catalog.get("modules")
    if not isinstance(entries, list) or not entries:
        raise ValueError("catalog modules must be nonempty")
    modules: dict[str, dict] = {}
    raw_modules: dict[str, bytes] = {}
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("invalid catalog entry")
        module_id, reference = item["id"], item.get("path")
        if module_id in modules or not isinstance(reference, str) or not reference.startswith("questions/"):
            raise ValueError("duplicate module ID or invalid catalog path")
        path = root / reference
        _reject_symlink_components(path, root, "catalog module symlink is forbidden")
        if not path.resolve().is_relative_to((root / "questions").resolve()) or path.is_symlink():
            raise ValueError("catalog module path leaves questions/ or is a symlink")
        raw = path.read_bytes()
        module = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=contract._unique_object)
        if (module.get("module_id") != module_id or module.get("kind") != item.get("kind")
                or item.get("question_count") != len(module.get("questions", []))):
            raise ValueError(f"catalog registration differs from {module_id} module")
        modules[module_id], raw_modules[module_id] = module, raw
    return catalog, modules, raw_modules


def _artifact_loader(root: Path):
    def load(reference: str) -> bytes:
        return _safe_path(root, reference).read_bytes()
    return load


def _validate_contexts(contexts: dict, modules: Mapping[str, dict]) -> None:
    if (not isinstance(contexts.get("global"), list) or not contexts["global"]
            or any(not isinstance(item, str) or not item.strip() for item in contexts["global"])):
        raise ValueError("scoring contexts require nonempty global rules")
    if not isinstance(contexts.get("subtypes"), dict) or not isinstance(contexts.get("cycle_sensitive"), str):
        raise ValueError("scoring contexts require subtype and cycle rules")
    for kind in ("types", "industries", "stages"):
        values = contexts.get(kind)
        if not isinstance(values, dict):
            raise ValueError(f"scoring contexts require {kind} map")
        for module_id, module in modules.items():
            if module["kind"] == kind and module_id != "cyclical":
                if not isinstance(values.get(module_id), str) or not values[module_id].strip():
                    raise ValueError(f"{module_id}: missing scoring context")
    for module_id, values in contexts["subtypes"].items():
        if not isinstance(values, dict) or any(not isinstance(text, str) or not text.strip()
                                                for text in values.values()):
            raise ValueError(f"{module_id}: invalid subtype scoring context")


def _legacy_baseline_hashes(root: Path) -> dict[str, str]:
    """Read the pinned trust root for the original metadata-light module set."""
    path = Path(root) / "schemas" / "quick_scan" / "module-legacy-baseline.json"
    _reject_symlink_components(path, root, "legacy module baseline symlink is forbidden")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError("legacy module baseline unavailable") from exc
    if hashlib.sha256(raw).hexdigest() != LEGACY_BASELINE_SHA256:
        raise ValueError("legacy module baseline hash mismatch")
    baseline = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=contract._unique_object)
    if (not isinstance(baseline, dict)
            or set(baseline) != {"schema_version", "release_id", "modules"}
            or baseline["schema_version"] != "1.0.0"
            or baseline["release_id"] != LEGACY_BASELINE_RELEASE_ID
            or not isinstance(baseline["modules"], list)):
        raise ValueError("invalid legacy module baseline")
    result: dict[str, str] = {}
    ordered_ids = []
    for item in baseline["modules"]:
        if (not isinstance(item, dict) or set(item) != {"module_id", "artifact_sha256"}
                or not isinstance(item["module_id"], str)
                or not isinstance(item["artifact_sha256"], str)
                or not re.fullmatch(r"[a-f0-9]{64}", item["artifact_sha256"])
                or item["module_id"] in result):
            raise ValueError("invalid legacy module baseline entry")
        result[item["module_id"]] = item["artifact_sha256"]
        ordered_ids.append(item["module_id"])
    if ordered_ids != sorted(LEGACY_BASELINE_IDS) or set(result) != LEGACY_BASELINE_IDS:
        raise ValueError("legacy module baseline registration mismatch")
    return result


def _verified_legacy_ids(root: Path, modules: Mapping[str, dict],
                         artifact_hashes: Mapping[str, str]) -> frozenset[str]:
    """Allow old lifecycle fields only for byte-exact modules in the pinned release."""
    if set(artifact_hashes) != set(modules):
        raise ValueError("module artifact hash registration mismatch")
    baseline = _legacy_baseline_hashes(root)
    legacy_ids = set()
    for module_id, module in modules.items():
        requires_compatibility = (
            not module.get("activation") or not module.get("introduced_in")
            or "dependencies" not in module or "conflicts" not in module)
        if not requires_compatibility:
            continue
        if baseline.get(module_id) != artifact_hashes.get(module_id):
            raise ValueError(f"{module_id}: untrusted legacy module archive; lifecycle metadata is required")
        legacy_ids.add(module_id)
    return frozenset(legacy_ids)


def validate_source_registry(*, root: Path = ROOT) -> tuple[dict, dict[str, dict]]:
    """Validate current authoring files, deriving legacy status from exact bytes."""
    root = Path(root)
    catalog, modules, raw_modules = source_catalog(root)
    contexts = _read_json(root / "questions" / "scoring-contexts.json")
    hashes = {module_id: hashlib.sha256(raw).hexdigest()
              for module_id, raw in raw_modules.items()}
    legacy_ids = _verified_legacy_ids(root, modules, hashes)
    contract.validate_registry(modules, contexts, legacy_ids=legacy_ids)
    _validate_contexts(contexts, modules)
    return catalog, modules


def _package_path(root: Path, package_id: str) -> Path:
    if not isinstance(package_id, str) or not PACKAGE_PATTERN.fullmatch(package_id):
        raise ValueError("invalid module package ID")
    return _safe_path(root, f"questions/releases/packages/{package_id}.json")


def _lock_path(root: Path, release_id: str) -> Path:
    if not isinstance(release_id, str) or not RELEASE_PATTERN.fullmatch(release_id):
        raise ValueError("invalid module release ID")
    return _safe_path(root, f"questions/releases/locks/{release_id}.json")


def load_package(package_id: str, *, root: Path = ROOT) -> tuple[dict, dict[str, dict], dict, dict]:
    """Resolve a historic package only from its verified archive and lock."""
    root = Path(root)
    try:
        package = _read_json(_package_path(root, package_id))
    except OSError as exc:
        raise ValueError('module package unavailable') from exc
    if not isinstance(package, dict) or package.get("package_id") != package_id:
        raise ValueError("module package identity mismatch")
    body = {key: value for key, value in package.items() if key != "package_id"}
    legacy_fields = {"schema_version", "release_id", "scoring_contexts", "renderer_rules_sha256",
                     "format_resources"}
    if set(body) not in (legacy_fields, legacy_fields | {"semantic_fingerprint_version"}):
        raise ValueError("module package fields are incomplete or unexpected")
    if body.get("semantic_fingerprint_version", "1.0.0") not in ("1.0.0", "2.0.0"):
        raise ValueError("unsupported semantic fingerprint version")
    if (body["schema_version"] != "1.0.0"
            or not isinstance(body["scoring_contexts"], dict)
            or not isinstance(body["format_resources"], dict)
            or not re.fullmatch(r"[a-f0-9]{64}", body["renderer_rules_sha256"])):
        raise ValueError("unsupported module package")
    required_resources = {"schemas/answer-content.schema.json", "questions/metric-registry.json",
                          "schemas/quick_scan/score.schema.json", "schemas/quick_scan/metric.schema.json"}
    resource_keys = set(body["format_resources"])
    if resource_keys not in (required_resources, required_resources | {"schemas/observation.schema.json"}):
        raise ValueError("module package is missing frozen response resources")
    if any(not isinstance(resource, dict) for resource in body["format_resources"].values()):
        raise ValueError("module package response resources must be JSON objects")
    if package_id != "pkg_" + contract.digest(body):
        raise ValueError("module package content hash mismatch")
    try:
        release = _read_json(_lock_path(root, body["release_id"]))
    except OSError as exc:
        raise ValueError('module release lock unavailable') from exc
    modules = contract.validate_release(release, _artifact_loader(root))
    artifact_hashes = {entry["module_id"]: entry["artifact_sha256"]
                       for entry in release["modules"]}
    legacy_ids = _verified_legacy_ids(root, modules, artifact_hashes)
    contract.validate_registry(modules, body["scoring_contexts"],
                               legacy_ids=legacy_ids,
                               historical_retired_ids=frozenset(release["retired_question_ids"]))
    _validate_contexts(body["scoring_contexts"], modules)
    if release["schema_version"] == "2.0.0":
        _load_routing_policy(root, release, modules)
    return package, modules, release, body["scoring_contexts"]


def _load_routing_policy(root: Path, release: dict, modules: dict) -> dict:
    from routing import validate_policy
    raw = _safe_path(root, release["routing_policy_ref"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != release["routing_policy_sha256"]:
        raise ValueError("routing policy archive hash mismatch")
    policy = json.loads(raw.decode("utf-8"), object_pairs_hook=contract._unique_object)
    validate_policy(policy, modules)
    if policy["router_version"] != release["router_version"]:
        raise ValueError("routing policy version differs from release")
    return policy


def load_routing_policy(package_id: str, *, root: Path = ROOT) -> dict:
    _, modules, release, _ = load_package(package_id, root=root)
    if release["schema_version"] != "2.0.0":
        raise ValueError("historical package has no executable v2 routing policy")
    return _load_routing_policy(root, release, modules)


def load_current(*, root: Path = ROOT) -> tuple[dict, dict[str, dict], dict, dict]:
    pointer = _read_json(Path(root) / "questions" / "releases" / "current.json")
    if not isinstance(pointer, dict) or set(pointer) != {"package_id"}:
        raise ValueError("invalid current module package pointer")
    return load_package(pointer["package_id"], root=root)


def observation_ingest_ready(package: dict) -> bool:
    """Old candidate packages are readable but cannot issue new standard runs."""
    schema = package.get("format_resources", {}).get("schemas/observation.schema.json", {})
    version = schema.get("properties", {}).get("schema_version", {})
    return (package.get("semantic_fingerprint_version") == "2.0.0"
            and isinstance(version.get("enum"), list) and "1.1.0" in version["enum"])


def _historical_packages(root: Path) -> list[tuple[dict, dict[str, dict], dict, dict]]:
    package_dir = root / "questions" / "releases" / "packages"
    if not package_dir.exists():
        return []
    packages = []
    for path in package_dir.glob("pkg_*.json"):
        if path.is_symlink():
            raise ValueError("release package symlink is forbidden")
        packages.append(load_package(path.stem, root=root))
    return packages


def publish(*, root: Path = ROOT, renderer_version: str, router_version: str,
            renderer_rules_sha256: str, routing_policy: dict | None = None,
            activate: bool = True) -> dict:
    """Publish an immutable release; optionally advance its atomic pointer."""
    if type(activate) is not bool:
        raise ValueError("activate must be boolean")
    root = Path(root)
    catalog, modules, raw_modules = source_catalog(root)
    contexts = _read_json(root / "questions" / "scoring-contexts.json")
    previous = _historical_packages(root)
    baseline_hashes = _legacy_baseline_hashes(root)
    if not previous and set(modules) != set(baseline_hashes):
        raise ValueError("first release must freeze the known 48-module baseline")
    if not re.fullmatch(r"[a-f0-9]{64}", renderer_rules_sha256):
        raise ValueError("invalid renderer rules digest")
    contract._version(renderer_version)
    contract._version(router_version)
    policy_artifact = None
    if routing_policy is not None:
        from routing import validate_policy
        validate_policy(routing_policy, modules)
        if router_version != routing_policy["router_version"]:
            raise ValueError("routing policy version differs from requested router")
        policy_raw = contract.canonical_bytes(routing_policy) + b"\n"
        policy_sha = hashlib.sha256(policy_raw).hexdigest()
        policy_ref = f"questions/releases/routing/router_{router_version.replace('.', '_')}-{policy_sha}.json"
        policy_artifact = (policy_ref, policy_raw, policy_sha)
    elif contract._version(router_version) >= (2, 0, 0):
        raise ValueError("router v2 requires a frozen routing policy")
    retired = set()
    history_questions: dict[str, tuple[str, str]] = {}
    versions_by_module: dict[str, dict[tuple[int, int, int], dict]] = {}
    for past_package, past_modules, past_release, _ in previous:
        if (policy_artifact and past_release["schema_version"] == "2.0.0"
                and past_release["routing_policy_sha256"] != policy_artifact[2]
                and contract._version(router_version) <= contract._version(past_release["router_version"])):
            raise ValueError("routing policy changed without router version increase")
        if (past_package["renderer_rules_sha256"] != renderer_rules_sha256
                and contract._version(renderer_version) <= contract._version(past_release["renderer_version"])):
            raise ValueError("renderer rules changed without renderer version increase")
        retired.update(past_release["retired_question_ids"])
        if set(past_modules) - set(modules):
            raise ValueError("previously published module removed from active catalog")
        for module_id, old in past_modules.items():
            version = contract._version(old["version"])
            same_version = versions_by_module.setdefault(module_id, {}).get(version)
            if same_version is not None and same_version != old:
                raise ValueError(f"{module_id}: historical version has conflicting content")
            versions_by_module[module_id][version] = old
        for module_id, old in past_modules.items():
            for question in old["questions"]:
                qid = question["id"]
                prior = (module_id, contract.question_definition_sha256(question))
                if qid in history_questions and history_questions[qid] != prior:
                    raise ValueError("historical question ID changed owner or definition")
                history_questions[qid] = prior
    for module_id, versions in versions_by_module.items():
        ordered = [versions[version] for version in sorted(versions)]
        for old, new in zip(ordered, ordered[1:]):
            contract.validate_upgrade(old, new)
        latest = ordered[-1]
        current = modules[module_id]
        if current != latest:
            if contract._version(current["version"]) <= contract._version(latest["version"]):
                raise ValueError(f"{module_id}: changed or rolled-back published module version")
            contract.validate_upgrade(latest, current)
    artifact_hashes = {module_id: hashlib.sha256(raw).hexdigest()
                       for module_id, raw in raw_modules.items()}
    legacy_ids = _verified_legacy_ids(root, modules, artifact_hashes)
    contract.validate_registry(modules, contexts, legacy_ids=legacy_ids,
                               historical_retired_ids=frozenset(retired))
    _validate_contexts(contexts, modules)
    active = {q["id"]: (module_id, contract.question_definition_sha256(q))
              for module_id, module in modules.items() for q in module["questions"]}
    for qid, prior in history_questions.items():
        if qid in active and active[qid] != prior:
            raise ValueError("published question ID changed owner or definition")
        if qid not in active and qid not in retired and not any(
                qid in module.get("retired_question_ids", []) for module in modules.values()):
            raise ValueError("removed historical question lacks retirement tombstone")
    retired.update(qid for module in modules.values() for qid in module.get("retired_question_ids", []))
    artifacts: dict[str, bytes] = {}
    entries = []
    for module_id in sorted(modules):
        module, raw = modules[module_id], raw_modules[module_id]
        sha = hashlib.sha256(raw).hexdigest()
        version_slug = module['version'].replace('.', '_')
        reference = f"questions/releases/artifacts/{module_id}/{version_slug}-{sha}.json"
        artifacts[reference] = raw
        entries.append({"module_id": module_id, "kind": module["kind"], "version": module["version"],
                        "artifact_ref": reference, "artifact_sha256": sha,
                        "question_semantics": sorted([
                            {"question_id": q["id"], "rubric_version": q["rubric_version"],
                             "definition_sha256": contract.question_definition_sha256(q)}
                            for q in module["questions"]], key=lambda item: item["question_id"])})
    release_body = {"schema_version": "2.0.0" if policy_artifact else "1.0.0", "catalog_version": catalog["version"],
                                     "renderer_version": renderer_version, "router_version": router_version,
                                     "retired_question_ids": sorted(retired), "modules": entries}
    if policy_artifact:
        policy_ref, policy_raw, policy_sha = policy_artifact
        release_body.update(routing_policy_ref=policy_ref, routing_policy_sha256=policy_sha)
        artifacts[policy_ref] = policy_raw
    release = contract.seal_release(release_body)
    contract.validate_release(release, artifacts.__getitem__)
    resources = {reference: _read_json(root / reference) for reference in (
        "schemas/answer-content.schema.json", "questions/metric-registry.json",
        "schemas/quick_scan/score.schema.json", "schemas/quick_scan/metric.schema.json",
        "schemas/observation.schema.json")}
    body = {"schema_version": "1.0.0", "release_id": release["release_id"],
            "scoring_contexts": contexts, "renderer_rules_sha256": renderer_rules_sha256,
            "format_resources": resources, "semantic_fingerprint_version": "2.0.0"}
    package = {**body, "package_id": "pkg_" + contract.digest(body)}
    for reference, raw in artifacts.items():
        _write_immutable(_safe_path(root, reference), raw)
    _write_immutable(_lock_path(root, release["release_id"]),
                     json.dumps(release, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    _write_immutable(_package_path(root, package["package_id"]),
                     json.dumps(package, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    # Validate all on-disk bytes before the only mutable pointer is advanced.
    load_package(package["package_id"], root=root)
    if activate:
        _atomic_json(root / "questions" / "releases" / "current.json", {"package_id": package["package_id"]})
    return {"package_id": package["package_id"], "release_id": release["release_id"],
            "modules": len(modules), "questions": len(active)}

