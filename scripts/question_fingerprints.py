"""Stable semantic fingerprints for question answers across published releases."""

import module_contract
from question_prompts import applied_contexts


def question_fingerprint(question, profile, contexts, package, release, answer_format):
    """Return the immutable fingerprint used by manifests and observations."""
    payload = {
        "definition": module_contract.question_definition_sha256(question),
        "applied_contexts": applied_contexts(question, profile, contexts),
        "renderer_rules_sha256": package["renderer_rules_sha256"],
        "renderer_version": release["renderer_version"],
        "answer_format": answer_format,
    }
    # Version 1 packages are immutable historical evidence. Keep their exact
    # original fingerprint algorithm while new releases bind each schema and
    # registry used to render or validate the selected answer format.
    if package.get("semantic_fingerprint_version", "1.0.0") == "2.0.0":
        resource_names = ["schemas/quick_scan/metric.schema.json"]
        if answer_format == "standard-1":
            resource_names += ["schemas/answer-content.schema.json",
                               "questions/metric-registry.json", "schemas/observation.schema.json"]
        elif answer_format == "screening-1":
            resource_names.append("schemas/quick_scan/score.schema.json")
        payload["format_resource_digests"] = {
            name: module_contract.digest(package["format_resources"][name])
            for name in resource_names
        }
    return module_contract.digest(payload)
