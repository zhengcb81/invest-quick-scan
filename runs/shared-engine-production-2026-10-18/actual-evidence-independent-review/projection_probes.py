"""Independent locked-source semantics; no authority or financial positives."""
import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE.parents[2] / "iqs-company-agent-lab/src"))
sys.path.insert(0, str(BASE / "actual-evidence-projection"))
from test_projection import inputs
from project_existing_sources import ProjectionRejected, project_existing_sources


def changed_source(kwargs, mutate):
    options = copy.deepcopy(kwargs)
    source = json.loads(options["public_board_raw"])
    target = next(row for row in source["sources"] if row.get("content_hash") and not row.get("excerpt_sha256"))
    assert target["content_hash"] == hashlib.sha256(target["bounded_excerpt"].encode("utf-8")).hexdigest()
    mutate(target)
    raw = json.dumps(source, ensure_ascii=False).encode("utf-8")
    options["public_board_raw"] = raw
    options["locked_refs"]["evidence-board.json"].update(
        bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest())
    return options


def test_old_content_hash_alias_must_not_be_ignored_after_resealing_container(inputs):
    task, kwargs = inputs
    changed = changed_source(kwargs, lambda source: source.update(
        bounded_excerpt=source["bounded_excerpt"] + " CHANGED-UNSUPPORTED-SOURCE-TEXT"))
    with pytest.raises(ProjectionRejected):
        project_existing_sources(task, **changed)


def test_explicitly_ineligible_source_must_not_be_fed_as_context_after_reseal(inputs):
    task, kwargs = inputs
    changed = changed_source(kwargs, lambda source: source.update(eligible_for_context=False))
    with pytest.raises(ProjectionRejected):
        project_existing_sources(task, **changed)
