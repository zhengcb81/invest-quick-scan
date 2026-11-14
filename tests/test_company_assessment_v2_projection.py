"""TDD coverage for the additive StockWiki company-assessment/2 producer."""

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import question_sets as qs  # noqa: E402
from iqs_scan.questions import frozen_release_projection as projection  # noqa: E402
from iqs_scan.questions import api as questions_api  # noqa: E402
from iqs_scan.questions import question_manifest  # noqa: E402
from iqs_scan.questions import module_registry  # noqa: E402
from iqs_scan.foundation.api import module_digest  # noqa: E402


def _canonical_sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _native_path(path):
    return Path("\\\\?\\" + str(path)) if os.name == "nt" else path


def _manifest(tmp_path):
    profile = {
        **qs.read_json(ROOT / "examples/profile.json"),
        "entity_id": "EXAMPLE_ENTITY_V2",
        "security_id": "EXAMPLE_SECURITY_V2",
        "as_of": "2026-11-14",
    }
    release_root = tmp_path / "release-root"
    release_dir = release_root / "questions" / "releases"
    shutil.copytree(ROOT / "questions" / "releases",
                    "\\\\?\\" + str(release_dir) if os.name == "nt" else release_dir)
    baseline = release_root / "schemas" / "quick_scan" / "module-legacy-baseline.json"
    baseline.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "schemas" / "quick_scan" / "module-legacy-baseline.json", baseline)
    old_package_id = "pkg_ca11c5c3340cfd45b9dd3babd7f9c0ea60df82c6a489e3a46eb5a2a80fed561e"
    package, _, _, _ = module_registry.load_package(old_package_id, root=release_root)
    body = {key: value for key, value in package.items() if key != "package_id"}
    body["format_resources"] = {
        **body["format_resources"],
        "schemas/quick_scan/metric.schema.json": qs.read_json(
            ROOT / "schemas" / "quick_scan" / "metric.schema.json"),
    }
    package_id = "pkg_" + module_digest(body)
    package_path = release_dir / "packages" / f"{package_id}.json"
    _native_path(package_path).parent.mkdir(parents=True, exist_ok=True)
    _native_path(package_path).write_text(
        json.dumps({**body, "package_id": package_id}, ensure_ascii=False,
                   sort_keys=True, indent=2) + "\n", encoding="utf-8")
    _native_path(release_dir / "current.json").write_text(
        json.dumps({"package_id": package_id}, sort_keys=True) + "\n", encoding="utf-8")
    output = tmp_path / "source-run"
    with patch.object(qs, "ROOT", release_root):
        qs.compose(profile, "full", output, "standard-1")
    return qs.read_json(output / "manifest.json"), release_root


def _refs(manifest):
    return [
        {
            "observation_id": "obs_" + f"{index:064x}",
            "payload_sha256": f"{index + 1:064x}",
            "question_id": question["id"],
        }
        for index, question in enumerate(manifest["questions"], start=1)
    ]


def _comparison_role_key_paths(value, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            current = path + (key,)
            if key == "comparison_role":
                yield current
            yield from _comparison_role_key_paths(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _comparison_role_key_paths(item, path + (index,))


def test_v2_groups_preserve_frozen_release_and_partition_all_questions(tmp_path):
    manifest, root = _manifest(tmp_path)
    original = copy.deepcopy(manifest)
    refs = _refs(manifest)

    result = projection.create_company_assessment_v2(manifest, refs, root=root)

    source_release = projection.create_projection(manifest, root=root)
    assert result["entity_id"] == manifest["profile"]["entity_id"]
    owner_manifest = result["manifest"]
    assert owner_manifest["protocol"] == "stockwiki.company_assessment/2"
    assert owner_manifest["schema_version"] == "2.0.0"
    assert owner_manifest["source_release"] == source_release
    assert owner_manifest["source_release_sha256"] == _canonical_sha256(source_release)
    assert owner_manifest["lineage_provenance_sha256"] == _canonical_sha256(
        owner_manifest["lineage_provenance"])
    assert manifest == original
    provenance = owner_manifest["lineage_provenance"]
    assert set(provenance) == {
        "source_release_sha256", "module_package_id", "module_release_id",
        "metric_contract_version", "metric_schema_sha256", "question_mappings",
    }
    assert provenance["source_release_sha256"] == owner_manifest["source_release_sha256"]
    assert provenance["module_package_id"] == source_release["module_package_id"]
    assert provenance["module_release_id"] == source_release["release_id"]
    assert provenance["metric_contract_version"] == "1.1.0"
    assert provenance["metric_schema_sha256"] == module_digest(
        module_registry.load_package(manifest["module_package_id"], root=root)[0]
        ["format_resources"]["schemas/quick_scan/metric.schema.json"])
    assert [mapping["question_id"] for mapping in provenance["question_mappings"]] == sorted(source_release["questions"])
    assert all(set(mapping) == {
        "question_id", "metric_contract", "comparison_role", "construct_id",
        "rubric_version", "response_kind", "definition_sha256", "semantic_sha256",
    } for mapping in provenance["question_mappings"])

    source_ids = set(source_release["questions"])
    grouped_ids = [question_id for group in owner_manifest["lineage_groups"]
                   for question_id in group["question_ids"]]
    assert len(grouped_ids) == len(set(grouped_ids))
    assert set(grouped_ids) == source_ids

    question_by_id = {question["id"]: question for question in manifest["questions"]}
    group_by_id = {question_id: group for group in owner_manifest["lineage_groups"]
                   for question_id in group["question_ids"]}
    for question_id, source_question in question_by_id.items():
        group = group_by_id[question_id]
        assert group["rubric_version"] == source_question["rubric_version"]
        assert group["aggregation_role"] == source_question["metric_contract"]["aggregation_role"]
        assert group["lineage_group_id"] == "lg_" + _canonical_sha256({
            "source_release_sha256": owner_manifest["source_release_sha256"],
            "rubric_version": group["rubric_version"],
            "aggregation_role": group["aggregation_role"],
            "question_ids": sorted(group["question_ids"]),
        })[:20]
        assert source_release["questions"][question_id]["definition_sha256"] == source_question["definition_sha256"]
        assert source_release["questions"][question_id]["semantic_sha256"] == source_question["semantic_sha256"]

    diagnostic_ids = {
        question["id"] for question in manifest["questions"]
        if question["metric_contract"]["aggregation_role"] == "diagnostic_only"
    }
    assert diagnostic_ids
    assert all(group_by_id[qid]["aggregation_role"] == "diagnostic_only" for qid in diagnostic_ids)
    assert not any(key in owner_manifest for key in ("aggregate_score", "quality_score", "score"))


def test_v2_observation_refs_bind_source_hashes_and_derived_lineage_group(tmp_path):
    manifest, root = _manifest(tmp_path)
    refs = _refs(manifest)

    result = projection.create_company_assessment_v2(manifest, refs, root=root)

    owner_manifest = result["manifest"]
    source_hash = owner_manifest["source_release_sha256"]
    group_by_id = {question_id: group for group in owner_manifest["lineage_groups"]
                   for question_id in group["question_ids"]}
    question_by_id = {question["id"]: question for question in manifest["questions"]}
    actual_refs = {item["question_id"]: item for item in result["observations"]}
    assert set(actual_refs) == set(question_by_id)
    for question_id, question in question_by_id.items():
        ref = actual_refs[question_id]
        group = group_by_id[question_id]
        assert set(ref) == {
            "observation_id", "payload_sha256", "question_id", "source_release_sha256",
            "lineage_group_id", "question_definition_sha256", "question_semantic_sha256",
        }
        assert ref["source_release_sha256"] == source_hash
        assert ref["lineage_group_id"] == group["lineage_group_id"]
        assert ref["question_definition_sha256"] == question["definition_sha256"]
        assert ref["question_semantic_sha256"] == question["semantic_sha256"]
        assert ref["payload_sha256"] == next(x["payload_sha256"] for x in refs
                                               if x["question_id"] == question_id)


def test_v2_partial_observations_stay_partial_without_claiming_full_coverage(tmp_path):
    manifest, root = _manifest(tmp_path)
    refs = _refs(manifest)[:2]

    result = projection.create_company_assessment_v2(manifest, refs, root=root)

    assert {item["question_id"] for item in result["observations"]} == {
        reference["question_id"] for reference in refs
    }
    assert sum(len(group["question_ids"]) for group in result["manifest"]["lineage_groups"]) == len(manifest["questions"])
    assert "completeness" not in result
    assert "complete" not in result


def test_active_published_v11_release_composes_and_exports_context_only(tmp_path):
    profile = {
        **qs.read_json(ROOT / "examples/profile.json"),
        "entity_id": "EXAMPLE_ACTIVE_V11",
        "security_id": "EXAMPLE_ACTIVE_V11_SECURITY",
        "as_of": "2026-11-14",
    }
    output = tmp_path / "active-run"
    qs.compose(profile, "full", output, "standard-1")
    manifest = qs.read_json(output / "manifest.json")
    contexts = [question for question in manifest["questions"]
                if question["comparison_role"] == "context"]

    current = module_registry.read_json(ROOT / "questions" / "releases" / "current.json")
    assert manifest["module_package_id"] == current["package_id"]
    active_package, _, _, _ = module_registry.load_package(current["package_id"], root=ROOT)
    assert set(active_package["format_resources"]["schemas/quick_scan/metric.schema.json"]
               ["definitions"]["AggregationRole"]["enum"]) == {
        "quality_core", "growth_core", "valuation_core", "diagnostic_only", "context_only",
    }
    assert manifest["metric_contract_version"] == "1.1.0"
    assert qs.API_PROTOCOL == "iqs.question-composition-api/1.1.0"
    assert question_manifest.API_PROTOCOL == "iqs.question-manifest-api/1.1.0"
    assert questions_api.API_PROTOCOL == "iqs.questions-api/1.1.0"
    assert len(contexts) == 17
    assert {question["metric_contract"]["aggregation_role"] for question in contexts} == {
        "context_only"
    }
    assert all(question["construct_id"] is None for question in contexts)

    request = projection.create_company_assessment_v2(
        manifest, _refs(manifest), root=ROOT)
    context_ids = {question["id"] for question in contexts}
    grouped_context_ids = {
        question_id for group in request["manifest"]["lineage_groups"]
        if group["aggregation_role"] == "context_only"
        for question_id in group["question_ids"]
    }
    assert grouped_context_ids == context_ids
    assert request["manifest"]["lineage_provenance"]["metric_contract_version"] == "1.1.0"


def test_comparison_role_is_serialized_only_in_lineage_provenance_mappings(tmp_path):
    manifest, root = _manifest(tmp_path)
    request = projection.create_company_assessment_v2(manifest, [], root=root)
    mappings = request["manifest"]["lineage_provenance"]["question_mappings"]

    expected_paths = {
        ("manifest", "lineage_provenance", "question_mappings", index, "comparison_role")
        for index, _ in enumerate(mappings)
    }

    assert set(_comparison_role_key_paths(request)) == expected_paths


def test_new_metric_contract_routes_all_context_questions_to_context_only(tmp_path):
    manifest, _ = _manifest(tmp_path)
    contexts = [question for question in manifest["questions"]
                if question["comparison_role"] == "context"]

    assert len(contexts) == 17
    assert {question["metric_contract"]["aggregation_role"] for question in contexts} == {
        "context_only"
    }
    assert all(question["construct_id"] is None for question in contexts)
    assert question_manifest.METRIC_CONTRACT_VERSION == "1.1.0"


def test_metric_contract_version_is_explicit_and_unknown_future_versions_are_rejected():
    assert question_manifest.metric_contract_version_for_schema({}) == "1.0.0"
    assert question_manifest.metric_contract_version_for_schema(
        {"x-metric-contract-version": "1.1.0"}) == "1.1.0"
    with pytest.raises(ValueError, match="unsupported metric contract version"):
        question_manifest.metric_contract_version_for_schema(
            {"x-metric-contract-version": "1.2.0"})


def test_context_only_rows_do_not_change_core_score():
    core_dimensions = ("business", "moat", "execution", "financial", "governance", "resilience")
    core = [
        {"id": f"CORE_{index}", "construct_id": f"CORE_{index}",
         "comparison_role": "core", "dimension": dimension,
         "aggregation": "scored", "critical": False, "status": "scored", "score": 5}
        for index, dimension in enumerate(core_dimensions)
    ]
    context = {"id": "CONTEXT_01", "construct_id": None,
               "comparison_role": "context", "dimension": "business",
               "aggregation": "scored", "critical": False, "status": "scored", "score": 1}

    without_context = qs.summarize(core, "core-constructs-v1",
                                   core_ids={item["construct_id"] for item in core})
    with_context = qs.summarize(core + [context], "core-constructs-v1",
                                core_ids={item["construct_id"] for item in core})

    assert with_context["quality_score"] == without_context["quality_score"] == 5
    assert with_context["dimensions"] == without_context["dimensions"]


def test_v2_rejects_context_question_falsely_promoted_to_core(tmp_path):
    manifest, root = _manifest(tmp_path)
    question = next(question for question in manifest["questions"]
                    if question["comparison_role"] == "context")
    question["metric_contract"]["aggregation_role"] = "quality_core"
    mapping = next(mapping for mapping in manifest["question_metric_mappings"]
                   if mapping["question_id"] == question["id"])
    mapping["aggregation_role"] = "quality_core"

    with pytest.raises(ValueError, match="metric mapping"):
        projection.create_company_assessment_v2(manifest, [], root=root)


def test_frozen_v1_package_keeps_its_original_metric_mapping(tmp_path):
    profile = {
        **qs.read_json(ROOT / "examples/profile.json"),
        "entity_id": "EXAMPLE_ENTITY_OLD_RELEASE",
        "security_id": "EXAMPLE_SECURITY_OLD_RELEASE",
        "as_of": "2026-11-14",
    }
    old_package_id = "pkg_ca11c5c3340cfd45b9dd3babd7f9c0ea60df82c6a489e3a46eb5a2a80fed561e"
    output = tmp_path / "old-release"
    qs.compose(profile, "full", output, "standard-1", package_id=old_package_id)
    old_manifest = qs.read_json(output / "manifest.json")
    contexts = [question for question in old_manifest["questions"]
                if question["comparison_role"] == "context"]

    assert old_manifest["metric_contract_version"] == "1.0.0"
    assert contexts
    assert {question["metric_contract"]["aggregation_role"] for question in contexts} <= {
        "quality_core", "growth_core", "valuation_core"
    }
    assert all(question["construct_id"] is None for question in contexts)
    old_package, _, _, _ = module_registry.load_package(old_package_id, root=ROOT)
    assert set(old_package["format_resources"]["schemas/quick_scan/metric.schema.json"]
               ["definitions"]["AggregationRole"]["enum"]) == {
        "quality_core", "growth_core", "valuation_core", "diagnostic_only",
    }
    assert len(qs.validate_manifest_metric_contract(old_manifest)) == old_manifest["question_count"]
    with pytest.raises(ValueError, match="legacy context role cannot be represented"):
        projection.create_company_assessment_v2(old_manifest, [], root=ROOT)


def test_v2_fact_question_uses_information_only_and_no_score_construct(tmp_path):
    profile = {
        **qs.read_json(ROOT / "examples/profile.json"),
        "entity_id": "EXAMPLE_ENTITY_FACT",
        "security_id": "EXAMPLE_SECURITY_FACT",
        "as_of": "2026-11-14",
    }
    run_dir = tmp_path / "fact-run"
    release_root = tmp_path / "fact-resources"
    release_dir = release_root / "questions" / "releases"
    shutil.copytree(ROOT / "questions" / "releases",
                    "\\\\?\\" + str(release_dir) if os.name == "nt" else release_dir)
    baseline = release_root / "schemas" / "quick_scan" / "module-legacy-baseline.json"
    baseline.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "schemas" / "quick_scan" / "module-legacy-baseline.json", baseline)
    module_registry = __import__("module_registry")
    old_package_id = "pkg_ca11c5c3340cfd45b9dd3babd7f9c0ea60df82c6a489e3a46eb5a2a80fed561e"
    package, _, _, _ = module_registry.load_package(old_package_id, root=release_root)
    body = {key: value for key, value in package.items() if key != "package_id"}
    bank = qs.read_json(ROOT / "questions" / "facts.json")
    body["format_resources"] = {
        **body["format_resources"],
        "questions/facts.json": bank,
        "schemas/quick_scan/metric.schema.json": qs.read_json(
            ROOT / "schemas" / "quick_scan" / "metric.schema.json"),
    }
    fact_package_id = "pkg_" + module_digest(body)
    package_path = release_dir / "packages" / f"{fact_package_id}.json"
    _native_path(package_path).parent.mkdir(parents=True, exist_ok=True)
    _native_path(package_path).write_text(
        json.dumps({**body, "package_id": fact_package_id}, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    with patch.object(qs, "ROOT", release_root):
        qs.compose(profile, "full", run_dir, "standard-1",
                   package_id=fact_package_id, fact_question_ids=["FACT_10"])
    manifest = qs.read_json(run_dir / "manifest.json")
    fact = next(question for question in manifest["questions"] if question["id"] == "FACT_10")
    reference = {
        "observation_id": "obs_" + "a" * 64,
        "payload_sha256": "b" * 64,
        "question_id": fact["id"],
    }

    result = projection.create_company_assessment_v2(manifest, [reference], root=release_root)

    owner_manifest = result["manifest"]
    group = next(group for group in owner_manifest["lineage_groups"]
                 if fact["id"] in group["question_ids"])
    assert group["aggregation_role"] == "information_only"
    assert group["rubric_version"] == fact["rubric_version"]
    assert owner_manifest["source_release"]["questions"][fact["id"]]["construct_id"] is None
    assert result["observations"][0]["lineage_group_id"] == group["lineage_group_id"]
    provenance_row = next(item for item in owner_manifest["lineage_provenance"]["question_mappings"]
                          if item["question_id"] == fact["id"])
    assert provenance_row == {
        "question_id": fact["id"],
        "metric_contract": None,
        "comparison_role": None,
        "construct_id": None,
        "rubric_version": fact["rubric_version"],
        "response_kind": "fact",
        "definition_sha256": fact["definition_sha256"],
        "semantic_sha256": fact["semantic_sha256"],
    }
    assert questions_api.create_company_assessment_v2 is projection.create_company_assessment_v2
    assert "create_company_assessment_v2" in questions_api.__all__
    assert questions_api.metric_contract_version_for_schema is question_manifest.metric_contract_version_for_schema
    assert "metric_contract_version_for_schema" in questions_api.__all__


@pytest.mark.parametrize("bad_refs", [
    [{"observation_id": "bad", "payload_sha256": "0" * 64, "question_id": "MISSING"}],
    [{"observation_id": "obs_" + "1" * 64, "payload_sha256": "0" * 64,
      "question_id": "IQS_01"},
     {"observation_id": "obs_" + "1" * 64, "payload_sha256": "1" * 64,
      "question_id": "IQS_02"}],
])
def test_v2_refuses_unknown_or_repeated_observation_identity(tmp_path, bad_refs):
    manifest, root = _manifest(tmp_path)

    with pytest.raises(ValueError):
        projection.create_company_assessment_v2(manifest, bad_refs, root=root)
