"""Compose an offline facts question pack from an authored company profile.

No network, no model call, no provider. Output is a fresh manifest/questions
directory that can later be registered and run under owner admission.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import standard_answers


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    result = standard_answers.compose_facts(profile, args.mode, args.output)
    manifest = json.loads((args.output / "manifest.json").read_text(encoding="utf-8"))
    result.update(
        protocol="iqs.facts_pack/1.0.0",
        mode=args.mode,
        answer_format=manifest.get("answer_format"),
        template_version=manifest.get("template_version"),
        question_ids=[q["id"] for q in manifest.get("questions", [])],
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
