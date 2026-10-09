"""Actual first-party offline producer, synthetic company input, isolated release root."""
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
import question_sets as qs
import routing


def main():
    request = json.loads(Path(sys.argv[1]).read_bytes())
    root = Path(request["root"]).resolve()
    own = Path(os.environ["IQS_ROUTE_TEST_OWNED_ROOT"]).resolve()
    assert root.is_relative_to(own) and not root.exists()
    shutil.copytree(ROOT / "questions", root / "questions", ignore=shutil.ignore_patterns("releases"))
    for ref in ("schemas/answer-content.schema.json", "schemas/quick_scan/metric.schema.json",
                "schemas/quick_scan/score.schema.json", "schemas/observation.schema.json",
                "schemas/quick_scan/module-legacy-baseline.json"):
        destination = root / ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / ref, destination)
    package = routing.publish_routing_package(root=root, renderer_version=qs.RENDERER_VERSION,
                                            renderer_rules_sha256=qs.renderer_rules_sha256())
    route = routing.resolve_route_decision(request["identity"], package_id=package["package_id"],
                                          now_utc=request["now"], root=root)
    qs.ROOT = root  # Isolated owner configuration, no mocked product behavior.
    qs.compose_from_route(route, root / "run", now_utc=request["now"], expected_route_decision_id=route["decision_id"])
    (root / "run/route.json").write_bytes(json.dumps(route, ensure_ascii=False, indent=2).encode("utf-8") + b"\r\n")
    print(json.dumps({"decision_id": route["decision_id"], "synthetic_company": True, "model_API_requests": 0}))


if __name__ == "__main__":
    main()
