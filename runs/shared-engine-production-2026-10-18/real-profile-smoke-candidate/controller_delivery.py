"""Pure engineering provenance checks. These never grant native permission."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parents[1]
REVIEW = ROOT / "docs/implementation/reviews/native-continuation-v15-2026-10-18"
SOURCE_CAS = BASE / "native-continuation-v15-candidate/candidate-cas.json"
CONTROLLER_CAS = HERE / "controller-cas-r3.json"
PROOF = BASE / "native-continuation-v15-candidate/deployment-source-pins.json"
RELEASE = ROOT / "runs/c16b/iqs-release"
CORRECTION = BASE / "batch-carrier-recovery-candidate"
CORRECTION_REVIEW = REVIEW / "batch-carrier-recovery-final.json"
CORRECTION_CAS = CORRECTION / "combined-correction-cas.json"
CORRECTION_DELIVERY = REVIEW / "batch-carrier-recovery-delivery.json"
CORRECTION_PROOF = CORRECTION / "deployment-source-pins-correction-02.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate_engineering_metadata_key")
            value[key] = item
        return value
    return json.loads(Path(path).read_text(encoding="utf8"), object_pairs_hook=unique)


def reference(raw, expected):
    if (not isinstance(raw, dict) or set(raw) != {"path", "sha256"}
            or Path(raw["path"]).resolve() != Path(expected).resolve()
            or raw["sha256"] != sha(expected)):
        raise ValueError("engineering_reference_path_or_hash_changed")
    return read(expected)


def runtime_paths():
    """The reviewed fixed software closure, including actual frozen compose inputs."""
    trees = [ROOT / name for name in ("scripts", "schemas", "questions")]
    trees += [RELEASE / name for name in ("scripts", "schemas", "questions")]
    trees += [ROOT.parent / repo / sub for repo, sub in (
        ("StockQAbyLLM", "src"), ("StockWiki", "stockwiki"),
        ("iqs-company-agent-lab", "src"), ("iqs-agent-runtime-lab", "src"))]
    paths = {path.resolve() for tree in trees for path in tree.rglob("*")
             if path.is_file() and path.suffix in {".py", ".json"}
             and "__pycache__" not in path.parts}
    paths.update(path.resolve() for path in (
        HERE / "controller_delivery.py", HERE / "activate_real_profile_smoke.py",
        HERE / "run_real_profile_smoke.py", HERE / "prepared-public-board.json",
        HERE / "prepared-public-board.provenance.json", HERE / "public-question-lock.json",
        BASE / "run_real_admitted_smoke.py",
        BASE / "actual-evidence-projection/project_existing_sources.py",
        ROOT / "runs/real-contrast-2026-10-16-03/inputs/frozen/pricing/s0_measurement.py",
        ROOT / "runs/real-contrast-2026-10-16-03/inputs.lock.json"))
    paths.update((BASE / "next-real-identity-preparation" / name).resolve() for name in (
        "entity-import.candidate.json", "analysis-subject-import.candidate.json", "preparation.json"))
    return paths


def inventory(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("complete_reviewed_runtime_inventory_required")
    found = {}
    for row in rows:
        path = Path(row["path"]).resolve(strict=True)
        if path in found or sha(path) != row["delivered_sha256"]:
            raise ValueError("delivered_original_source_changed_or_duplicate")
        found[path] = row
    if set(found) != runtime_paths():
        raise ValueError("complete_fixed_runtime_inventory_required")
    return found


def verify_deployment(proof_ref=None):
    """One shared refusal check for activation and execution; all reads are local."""
    if proof_ref is not None and Path(proof_ref.get("path", "")).resolve() == CORRECTION_PROOF.resolve():
        proof = reference(proof_ref, CORRECTION_PROOF)
        parent = reference(proof["parent_proof"], PROOF)
        correction = verify_correction(proof, parent)
        return _verified_parent(parent, correction=correction)
    proof = read(PROOF) if proof_ref is None else reference(proof_ref, PROOF)
    return _verified_parent(proof)


def _verified_parent(proof, correction=None):
    final = reference(proof["review_final"], REVIEW / "final.json")
    if (final.get("status") != "passed_for_exact_native_v15_source_and_controller_scope"
            or final.get("open_findings") != []
            or final.get("reviewer", {}).get("agent_id") != "/root/production_node_review18"
            or not final["reviewer"].get("author_agent_ids")
            or final["reviewer"]["agent_id"] in final["reviewer"]["author_agent_ids"]):
        raise ValueError("complete_continuation_profile_node_not_accepted")
    source = reference(final["source_cas"], SOURCE_CAS)
    controller = reference(final["controller_cas"], CONTROLLER_CAS)
    appendix = reference(proof["delivery_addendum"], REVIEW / "delivery-addendum.json")
    for key in ("review_final", "source_cas", "controller_cas"):
        expected = proof["review_final"] if key == "review_final" else final[key]
        if appendix[key] != expected or proof.get(key) != expected:
            raise ValueError("engineering_delivery_provenance_mismatch")
    if proof.get("files") != appendix.get("files"):
        raise ValueError("self_selected_runtime_inventory_forbidden")
    found = inventory(appendix["files"] if correction is None else correction["files"])
    # The independent final fixes reviewed candidate bytes; the delivery
    # appendix explains any normal-hook normalization of those exact products.
    for row in source["files"]:
        if row["kind"] == "product":
            delivered = found[Path(row["target"]).resolve()]
            if delivered["candidate_sha256"] != row["candidate_sha256"]:
                raise ValueError("reviewed_source_candidate_changed")
    for row in controller["files"]:
        path = Path(row["path"]).resolve(strict=True)
        changed = correction["changes"].get(path) if correction else None
        if changed is not None:
            if row["sha256"] != changed["base_sha256"]:
                raise ValueError("correction_controller_parent_not_reviewed_bytes")
        elif sha(path) != row["sha256"] or path.stat().st_size != row["bytes"]:
            raise ValueError("reviewed_controller_candidate_changed")
    # These are the only public onboarding drafts consumed by activation.
    # Validate their reviewed pins before the first real owner mutation.
    for name in ("entity-import.candidate.json", "analysis-subject-import.candidate.json", "preparation.json"):
        path = (BASE / "next-real-identity-preparation" / name).resolve()
        matches = [row for row in controller["input_refs"] if Path(row["path"]).resolve() == path]
        if (len(matches) != 1 or matches[0]["sha256"] != sha(path)
                or matches[0]["bytes"] != path.stat().st_size):
            raise ValueError("reviewed_public_onboarding_input_changed")
    public = final["public_context"]
    if public != controller["public_context"]:
        raise ValueError("independent_public_allowlist_changed")
    for key, name in (("board", "prepared-public-board.json"),
                      ("provenance", "prepared-public-board.provenance.json")):
        row = public[key]
        path = HERE / name
        if (Path(row["path"]).resolve() != path.resolve()
                or row["sha256"] != sha(path) or row["bytes"] != path.stat().st_size):
            raise ValueError("reviewed_public_context_changed")
    if public["identity_bridge_relative_path"] != "public-identity-bridge.json":
        raise ValueError("actual_owner_identity_bridge_path_required")
    result = dict(proof_ref=dict(path=str(PROOF), sha256=sha(PROOF)) if correction is None else correction["proof_ref"],
                  files=appendix["files"] if correction is None else correction["files"], public_context=public)
    if correction is not None:
        result.update({key: correction[key] for key in ("recovery_only", "original_run_config",
            "original_checkpoint", "original_safe_output_proof")})
    return result


def verify_public_inputs(config, own, delivered, subject=None):
    """Board is independently allowlisted; bridge is checked after native prepare."""
    if delivered.get("recovery_only") is True:
        fixed = BASE / "actual-native-catl-profile-01"
        if own != fixed.resolve():
            raise ValueError("correction_is_only_for_original_saved_run")
        original = reference(delivered["original_run_config"], fixed / "run-config.json")
        for key, expected in (("original_checkpoint", fixed / "cold-session/checkpoint.json"),
                              ("original_safe_output_proof", fixed / "crash-native-proof.json")):
            row = delivered[key]
            if (Path(row["path"]).resolve() != expected.resolve() or sha(expected) != row["sha256"]):
                raise ValueError("correction_original_safe_checkpoint_changed")
        comparison = dict(config)
        comparison["deployment_proof"] = original["deployment_proof"]
        if comparison != original:
            raise ValueError("correction_cannot_change_original_experiment_inputs")
        # The original driver refuses cold while this exact pinned checkpoint
        # directory exists. No other root/config can use the correction.
        if not (fixed / "cold-session").is_dir():
            raise ValueError("correction_requires_original_safe_checkpoint_directory")
    board = Path(delivered["public_context"]["board"]["path"]).resolve(strict=True)
    bridge = (own / "public-identity-bridge.json").resolve(strict=True)
    if (Path(config["public_board"]).resolve(strict=True) != board
            or Path(config["public_identity"]).resolve(strict=True) != bridge):
        raise ValueError("fixed_reviewed_public_context_required")
    refs = {key: dict(path=path.name, bytes=path.stat().st_size, raw_sha256=sha(path))
            for key, path in (("evidence-board.json", board), ("identity.json", bridge))}
    if config.get("public_input_refs") != refs:
        raise ValueError("exact_reviewed_public_input_refs_required")
    if subject is not None:
        expected = dict(entity_id=subject["entity_id"],
                        subject_key=subject["analysis_subject_id"] + "@" + str(subject["analysis_subject_revision"]))
        if read(bridge) != expected:
            raise ValueError("genuine_native_subject_identity_bridge_required")


def verify_question_definitions(manifest=None):
    lock = read(HERE / "public-question-lock.json")
    current = read(RELEASE / "questions/releases/current.json")
    definitions = read(RELEASE / "questions/common.json")
    by_id = {row["id"]: row for row in definitions["questions"]}
    if (current["package_id"] != lock["package_id"]
            or definitions["module_id"] != lock["module_id"]
            or definitions["version"] != lock["version"]):
        raise ValueError("reviewed_frozen_question_package_changed")
    for qid, expected in lock["definition_sha256"].items():
        raw = json.dumps(by_id[qid], ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf8")
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("reviewed_original_question_definition_changed")
    if manifest is not None:
        compiled = {row["id"]: row for row in manifest["questions"]}
        if (manifest["module_package_id"] != lock["package_id"]
                or any(compiled[qid]["definition_sha256"] != expected
                       for qid, expected in lock["definition_sha256"].items())):
            raise ValueError("composed_question_definition_differs_from_reviewed_sample")


def verify_correction(proof, parent):
    """Explicit same-node semantic supplement; the parent delivery is immutable."""
    final = reference(proof["correction_final"], CORRECTION_REVIEW)
    if (final.get("status") != "passed_for_exact_batch_carrier_channel_alignment_and_recovery_provenance"
            or final.get("open_findings") != []
            or final.get("reviewer", {}).get("agent_id") != "/root/production_node_review18"
            or not final["reviewer"].get("author_agent_ids")
            or final["reviewer"]["agent_id"] in final["reviewer"]["author_agent_ids"]):
        raise ValueError("independent_exact_correction_review_required")
    if (final.get("recovery_only") is not True or proof.get("recovery_only") is not True):
        raise ValueError("correction_is_recovery_only")
    if final["parent_proof"] != proof["parent_proof"] or final["parent_review_final"] != parent["review_final"]:
        raise ValueError("correction_parent_provenance_changed")
    cas = reference(final["source_cas"], CORRECTION_CAS)
    delivered = reference(proof["correction_delivery"], CORRECTION_DELIVERY)
    if (delivered["correction_final"] != proof["correction_final"]
            or delivered["parent_proof"] != proof["parent_proof"]
            or delivered["source_cas"] != final["source_cas"]
            or delivered.get("status") != "independently_verified_exact_correction_delivery"
            or delivered.get("open_findings") != [] or delivered["files"] != proof["files"]):
        raise ValueError("correction_delivery_not_independently_bound")
    before = {Path(row["path"]).resolve(): row for row in parent["files"]}
    after = inventory(delivered["files"])
    if len(before) != len(parent["files"]) or set(before) != set(after):
        raise ValueError("correction_must_preserve_complete_parent_closure")
    products = [row for row in cas["files"] if row["kind"] == "product"]
    changes = {Path(row["target"]).resolve(): row for row in products}
    # The fixed independent final binds the exact versioned CAS; its products
    # may only correct existing paths in the already reviewed runtime closure.
    if not products or len(changes) != len(products) or not set(changes) <= set(before):
        raise ValueError("exact_reviewed_correction_products_in_parent_closure_required")
    for path, row in before.items():
        change = changes.get(path)
        if change is None:
            if row != after[path]:
                raise ValueError("unreviewed_runtime_delta_outside_correction")
        elif (change["base_sha256"] != row["delivered_sha256"]
              or change["candidate_sha256"] != after[path]["candidate_sha256"]):
            raise ValueError("correction_not_based_on_parent_delivered_bytes")
    return dict(files=delivered["files"], changes=changes, recovery_only=True,
                original_run_config=final["original_run_config"], original_checkpoint=final["original_checkpoint"],
                original_safe_output_proof=final["original_safe_output_proof"],
                proof_ref=dict(path=str(CORRECTION_PROOF), sha256=sha(CORRECTION_PROOF)))
