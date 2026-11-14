"""IQS-owned, read-only export for the company/question workbench.

This module composes IQS question-domain readers with the StockWiki public
owner adapter. It never imports the UI package, reads UI-generated files, or
opens owner storage directly.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

_SCRIPT_ROOT = str(Path(__file__).resolve().parent)
if _SCRIPT_ROOT not in sys.path:
    sys.path.insert(0, _SCRIPT_ROOT)

import question_library


PROTOCOL = "iqs.workbench-snapshot/1.0.0"
SECTIONS = ("bank", "versions", "roster", "answers", "manifest")
_COUNT_KEYS = (
    "modules", "questions", "entities", "runs", "versioned_runs", "fact_questions",
    "core_constructs", "common_extensions", "locks", "packages", "routers", "rubrics",
    "applicability_cells", "applicability_not_evaluated", "applicability_applicable",
    "applicability_distribution",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json(path: Path) -> Any:
    return question_library.read_json(path)


def _source(path: Path, root: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def _record_sources(paths: set[Path], root: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        try:
            if path.is_file() and path.resolve().is_relative_to(root.resolve()):
                result.append(_source(path, root))
        except (OSError, ValueError):
            continue
    return result


def _load_bank(root: Path, source_paths: set[Path]) -> dict[str, Any]:
    questions_root = root / "questions"
    catalog, modules = question_library.load_library(root=root)
    module_ids = [entry["id"] for entry in catalog["modules"]]
    all_questions = [question for module_id in module_ids for question in modules[module_id]["questions"]]
    common_questions = modules.get("common", {}).get("questions", [])
    core_ids = [question["id"] for question in common_questions
                if question.get("comparison_role") == "core"]
    extension_ids = [question["id"] for question in common_questions
                     if question.get("comparison_role") != "core"]

    facts = _json(questions_root / "facts.json")
    facts = {**facts, "count": len(facts.get("questions", []))}
    metric_registry = _json(questions_root / "metric-registry.json")
    routing_policy = _json(questions_root / "routing-policy.v2.json")
    rubric_paths = sorted((questions_root / "scoring-rubrics").glob("*.json"))
    rubrics = [_json(path) for path in rubric_paths]

    source_paths.add(questions_root / "catalog.json")
    source_paths.update(root / entry["path"] for entry in catalog["modules"])
    source_paths.update({questions_root / name for name in (
        "facts.json", "metric-registry.json", "routing-policy.v2.json", "scoring-contexts.json")})
    source_paths.update(rubric_paths)
    return {
        "catalog": catalog,
        "modules": modules,
        "questions_by_module": {module_id: [question["id"] for question in modules[module_id]["questions"]]
                                for module_id in module_ids},
        "module_kinds": {entry["id"]: entry["kind"] for entry in catalog["modules"]},
        "module_names": {entry["id"]: entry["name"] for entry in catalog["modules"]},
        "question_count": len(all_questions),
        "always_applicable_modules": ["common", *question_library.ALWAYS_APPLICABLE_DIAGNOSTICS],
        "core_constructs": {"ids": core_ids, "count": len(core_ids),
                            "extension_ids": extension_ids,
                            "extension_count": len(extension_ids),
                            "common_question_count": len(common_questions)},
        "facts": facts,
        "routing_policy": routing_policy,
        "metric_registry": metric_registry,
        "rubrics": rubrics,
    }


def _release_path(path: Path, root: Path) -> Path:
    resolved_root = (root / "questions" / "releases").resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(resolved_root) or path.is_symlink():
        raise ValueError("release artifact leaves the IQS release directory")
    return resolved


def _artifact_anchors(root: Path, reference: str, expected_sha256: str | None,
                      source_paths: set[Path]) -> dict[str, dict[str, Any]] | None:
    if (not isinstance(reference, str) or not reference.startswith("questions/releases/artifacts/")
            or ".." in Path(reference).parts):
        return None
    try:
        path = _release_path(root / reference, root)
        if not path.is_file():
            return None
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if expected_sha256 and digest != expected_sha256:
            return None
        document = json.loads(raw.decode("utf-8-sig"))
    except (OSError, ValueError, UnicodeError, RecursionError):
        return None
    source_paths.add(path)
    questions = document.get("questions") if isinstance(document, dict) else None
    if not isinstance(questions, list):
        return None
    result = {}
    for question in questions:
        if not isinstance(question, dict) or not isinstance(question.get("id"), str):
            continue
        anchors = question.get("anchors")
        if isinstance(anchors, dict):
            result[question["id"]] = anchors
    return result


def _lock_diff(left: dict[str, Any], right: dict[str, Any], root: Path,
               source_paths: set[Path]) -> dict[str, Any]:
    left_modules = {item.get("module_id"): item for item in left.get("modules", [])
                    if isinstance(item, dict) and isinstance(item.get("module_id"), str)}
    right_modules = {item.get("module_id"): item for item in right.get("modules", [])
                     if isinstance(item, dict) and isinstance(item.get("module_id"), str)}
    question_diffs: list[dict[str, Any]] = []
    comparable = True
    for module_id in sorted(set(left_modules) | set(right_modules)):
        left_module, right_module = left_modules.get(module_id), right_modules.get(module_id)
        if left_module is None or right_module is None:
            comparable = False
            question_diffs.append({"category": "incomparable", "module_id": module_id,
                                   "field": "module", "synthetic": False})
            continue
        left_semantics = {item.get("question_id"): item for item in left_module.get("question_semantics", [])
                          if isinstance(item, dict) and isinstance(item.get("question_id"), str)}
        right_semantics = {item.get("question_id"): item for item in right_module.get("question_semantics", [])
                           if isinstance(item, dict) and isinstance(item.get("question_id"), str)}
        left_anchors = _artifact_anchors(root, left_module.get("artifact_ref"),
                                         left_module.get("artifact_sha256"), source_paths)
        right_anchors = _artifact_anchors(root, right_module.get("artifact_ref"),
                                          right_module.get("artifact_sha256"), source_paths)
        for question_id in sorted(set(left_semantics) | set(right_semantics)):
            before, after = left_semantics.get(question_id), right_semantics.get(question_id)
            if before is None:
                question_diffs.append({"category": "question_added", "question_id": question_id,
                                       "module_id": module_id, "after": after.get("definition_sha256"),
                                       "synthetic": False})
                continue
            if after is None:
                question_diffs.append({"category": "question_removed", "question_id": question_id,
                                       "module_id": module_id, "after": before.get("definition_sha256"),
                                       "synthetic": False})
                continue
            if before.get("definition_sha256") != after.get("definition_sha256"):
                question_diffs.append({"category": "semantics_changed", "question_id": question_id,
                                       "module_id": module_id, "field": "definition_sha256",
                                       "before": before.get("definition_sha256"),
                                       "after": after.get("definition_sha256"), "synthetic": False})
            if before.get("rubric_version") != after.get("rubric_version"):
                question_diffs.append({"category": "semantics_changed", "question_id": question_id,
                                       "module_id": module_id, "field": "rubric_version",
                                       "before": before.get("rubric_version"),
                                       "after": after.get("rubric_version"), "synthetic": False})
            left_anchor = (left_anchors or {}).get(question_id)
            right_anchor = (right_anchors or {}).get(question_id)
            if not isinstance(left_anchor, dict) or not isinstance(right_anchor, dict):
                comparable = False
                question_diffs.append({"category": "incomparable", "question_id": question_id,
                                       "module_id": module_id, "field": "anchors", "synthetic": False})
                continue
            for tier in ("1", "5", "10"):
                if left_anchor.get(tier) != right_anchor.get(tier):
                    question_diffs.append({"category": "anchors_changed", "question_id": question_id,
                                           "module_id": module_id, "field": tier,
                                           "before": left_anchor.get(tier), "after": right_anchor.get(tier),
                                           "synthetic": False})
    metadata_diffs = []
    for field in ("catalog_version", "release_id", "router_version", "renderer_version", "schema_version"):
        if left.get(field) != right.get(field):
            metadata_diffs.append({"field": field, "before": left.get(field), "after": right.get(field),
                                   "synthetic": False})
    question_identical = comparable and not question_diffs
    return {"left": {"kind": "lock", "id": left["lock_id"]},
            "right": {"kind": "lock", "id": right["lock_id"]},
            "comparable": comparable, "question_level_identical": question_identical,
            "question_diffs": question_diffs, "metadata_diffs": metadata_diffs,
            "synthetic_mode": False,
            "notice": "已确认无差异" if question_identical else f"{len(question_diffs)} 条差异"}


def _brief_package(package: dict[str, Any], path: Path) -> dict[str, Any]:
    result = {key: value for key, value in package.items() if key != "format_resources"}
    resources = package.get("format_resources")
    if isinstance(resources, dict):
        keys = sorted(resources)
        result["format_resource_keys"] = keys
        result["format_resources"] = {
            "_note": "Schema 正文保留在 IQS 版本资源；此 UI 快照仅提供键名与源包摘要。",
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "keys": keys,
        }
    return result


def _load_versions(root: Path, source_paths: set[Path]) -> dict[str, Any]:
    release_root = root / "questions" / "releases"
    current_path = release_root / "current.json"
    current = _json(current_path)
    source_paths.add(current_path)
    package_paths = sorted((release_root / "packages").glob("*.json"))
    lock_paths = sorted((release_root / "locks").glob("*.json"))
    router_paths = sorted((release_root / "routing").glob("*.json"))
    packages = []
    for path in package_paths:
        package = _json(path)
        packages.append(_brief_package(package, path))
        source_paths.add(path)
    locks = []
    for path in lock_paths:
        lock = _json(path)
        locks.append({**lock, "lock_id": path.stem,
                      "source_file": path.relative_to(root).as_posix()})
        source_paths.add(path)
    routers = []
    for path in router_paths:
        router = _json(path)
        routers.append({**router, "file": path.relative_to(root).as_posix(),
                        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        source_paths.add(path)
    lock_diffs = []
    for index, left in enumerate(locks):
        for right in locks[index + 1:]:
            lock_diffs.append(_lock_diff(left, right, root, source_paths))
    by_package = {item.get("package_id"): item for item in packages}
    package_id = current.get("package_id") if isinstance(current, dict) else None
    current_package = by_package.get(package_id, {})
    return {"current": current, "current_package": current_package, "locks": locks,
            "packages": packages, "routers": routers, "lock_diffs": lock_diffs,
            "package_diffs": []}


def _market_group(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    market = value.strip().upper()
    if market.startswith("CN-") or market in {"SSE", "SZSE", "BSE"}:
        return "CN"
    if market == "HK" or market.startswith("HK-") or market == "SEHK":
        return "HK"
    if market.startswith("US-") or market in {"NASDAQ", "NYSE", "NYSEAMERICAN", "NYSE-ARCA"}:
        return "US"
    return market


def _load_roster(owner: Any, universe_id: str) -> dict[str, Any]:
    reply = owner.universe_list(universe_id)
    members = reply.get("members") if isinstance(reply, dict) else None
    if not isinstance(members, list):
        raise ValueError("owner membership projection is unavailable")
    rows = []
    seen = set()
    by_market: dict[str, int] = {}
    by_next_action: dict[str, int] = {}
    verified = provisional = unknown_identity = 0
    for member in members:
        if not isinstance(member, dict) or not isinstance(member.get("entity_id"), str):
            raise ValueError("owner returned a malformed membership projection")
        entity_id = member["entity_id"]
        if entity_id in seen:
            raise ValueError("owner returned a duplicate entity in the universe")
        seen.add(entity_id)
        identity_state = member.get("identity_state")
        if identity_state == "verified":
            verified += 1
            next_action = "ready_for_profile" if member.get("membership_status", "active") == "active" else "needs_owner_admission"
        elif identity_state == "provisional":
            provisional += 1
            next_action = "needs_verified_identity"
        else:
            unknown_identity += 1
            next_action = "needs_verified_identity"
        securities = member.get("securities", [])
        if not isinstance(securities, list):
            securities = []
        listings = []
        entity_markets = set()
        for security in securities:
            if not isinstance(security, dict):
                continue
            market = _market_group(security.get("market"))
            if market:
                entity_markets.add(market)
            listings.append({"market": market or security.get("market"),
                             "ticker": security.get("ticker"),
                             "status": security.get("listing_status", security.get("status"))})
        for market in entity_markets:
            by_market[market] = by_market.get(market, 0) + 1
        by_next_action[next_action] = by_next_action.get(next_action, 0) + 1
        name = member.get("canonical_name")
        rows.append({"entity_id": entity_id, "name": name if isinstance(name, str) and name else entity_id,
                     "identity_state": identity_state if isinstance(identity_state, str) else "unknown",
                     "identity_revision": member.get("identity_revision"), "listings": listings,
                     "bindings": len(member["bindings"]) if isinstance(member.get("bindings"), list) else None,
                     "observations": None, "search_backed": None, "next_action": next_action})
    rows.sort(key=lambda row: (row["name"].casefold(), row["entity_id"]))
    declared_count = reply.get("member_count")
    if declared_count is not None and (type(declared_count) is not int or declared_count != len(rows)):
        raise ValueError("owner membership count disagrees with its rows")
    return {"protocol": "stockwiki.quick_scan_dashboard_reply/1.0.0",
            "universe_id": universe_id, "entities": len(rows), "verified": verified,
            "provisional": provisional, "identity_unknown": unknown_identity,
            "by_market": by_market, "by_next_action": by_next_action, "rows": rows,
            "route_decisions": {},
            "applicability_source": {"status": "no_route_snapshot", "evidence_horizon": None}}


def _unavailable(section: str, code: str, message: str) -> dict[str, str]:
    return {"section": section, "code": code, "message": message}


def build_workbench_snapshot(data_root: Path, config: dict[str, Any], *, owner: Any = None,
                             generated_at: str | None = None) -> dict[str, Any]:
    """Build one immutable-in-memory view; unavailable sources remain unknown."""
    root = Path(data_root).resolve()
    timestamp = generated_at or _now()
    payload: dict[str, Any] = {name: None for name in SECTIONS}
    availability = {name: "unavailable" for name in SECTIONS}
    warnings: list[dict[str, str]] = []
    source_paths: set[Path] = set()

    try:
        payload["bank"] = _load_bank(root, source_paths)
        availability["bank"] = "available"
    except Exception as error:  # section-local failure must not hide product APIs
        warnings.append(_unavailable("bank", getattr(error, "code", "bank_unavailable"),
                                     "题库或评分配置暂不可用；公司结果和扫描服务仍可使用。"))

    try:
        payload["versions"] = _load_versions(root, source_paths)
        availability["versions"] = "available"
    except Exception as error:
        warnings.append(_unavailable("versions", getattr(error, "code", "versions_unavailable"),
                                     "题库版本历史暂不可用；其他展示和产品服务仍可使用。"))

    workspace_root = config.get("workspace_root") if isinstance(config, dict) else None
    if owner is None and isinstance(workspace_root, str) and workspace_root.strip():
        try:
            if __package__:
                from .dashboard_owner import OwnerGateway
            else:  # pragma: no cover - direct CLI execution
                from dashboard_owner import OwnerGateway
            owner = OwnerGateway(config)
        except Exception:
            owner = None
    universe_id = config.get("universe_id", "default") if isinstance(config, dict) else "default"
    if owner is not None:
        try:
            payload["roster"] = _load_roster(owner, universe_id)
            availability["roster"] = "available"
        except Exception as error:
            warnings.append(_unavailable("roster", getattr(error, "code", "owner_roster_unavailable"),
                                         "正式公司名单暂不可用；没有把缺少的公司当成空名单。"))
    else:
        warnings.append(_unavailable("roster", "owner_workspace_unconfigured",
                                     "尚未连接 StockWiki 工作区；公司数量未知，不代表名单为空。"))

    warnings.append(_unavailable("answers", "history_source_not_selected",
                                 "历史薄草稿源尚未明确选择；未将缺少的历史数据表示为零。"))

    counts: dict[str, Any] = {key: None for key in _COUNT_KEYS}
    bank = payload["bank"]
    versions = payload["versions"]
    roster = payload["roster"]
    if bank is not None:
        counts.update({
            "modules": len(bank["catalog"]["modules"]),
            "questions": bank["question_count"],
            "fact_questions": bank["facts"]["count"],
            "core_constructs": bank["core_constructs"]["count"],
            "common_extensions": bank["core_constructs"]["extension_count"],
            "rubrics": len(bank["rubrics"]),
            "runs": None, "versioned_runs": None,
        })
    if versions is not None:
        counts.update({"locks": len(versions["locks"]), "packages": len(versions["packages"]),
                       "routers": len(versions["routers"])})
    if roster is not None and bank is not None:
        entity_count = roster["entities"]
        module_count = counts["modules"]
        always = len(bank["always_applicable_modules"])
        cells = entity_count * module_count
        applicable = entity_count * always
        not_evaluated = cells - applicable
        counts.update({"entities": entity_count, "applicability_cells": cells,
                       "applicability_applicable": applicable,
                       "applicability_not_evaluated": not_evaluated,
                       "applicability_distribution": {"applicable": applicable,
                           "not_applicable": 0, "unknown": 0, "not_evaluated": not_evaluated}})

    manifest = {
        "generated_at": timestamp,
        "counts": counts,
        "expected": {key: counts[key] for key in ("modules", "questions", "entities", "runs",
                                                   "versioned_runs", "fact_questions")},
        "data_root": str(root), "read_only_data_root": True,
        "sources": _record_sources(source_paths, root),
        "synthetic": {"enabled": False,
                      "notice": "快照不含合成数据；演示样例仅由 UI 在明确开启时加载。"},
        "network_scope": "none",
        "applicability_source": ((roster or {}).get("applicability_source")
                                 or {"status": "unavailable", "evidence_horizon": None}),
    }
    payload["manifest"] = manifest
    availability["manifest"] = "available"
    return {"protocol": PROTOCOL, "generated_at": timestamp, **payload,
            "availability": availability, "warnings": warnings}


def unavailable_workbench_snapshot(reason: str = "展示快照尚未生成。") -> dict[str, Any]:
    return {"protocol": PROTOCOL, "generated_at": None,
            **{name: None for name in SECTIONS},
            "availability": {name: "unavailable" for name in SECTIONS},
            "warnings": [_unavailable("snapshot", "snapshot_unavailable", reason)]}


def load_workbench_snapshot(path: Path) -> dict[str, Any]:
    """Read only a current-format snapshot; a missing/bad one stays local-unavailable."""
    path = Path(path)
    try:
        if not path.is_file() or path.stat().st_size > 64 * 1024 * 1024:
            return unavailable_workbench_snapshot("展示快照不存在或超过读取上限。")
        def pairs(items):
            out = {}
            for key, value in items:
                if key in out:
                    raise ValueError("duplicate_json_key")
                out[key] = value
            return out
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite_json")))
        if (not isinstance(data, dict) or data.get("protocol") != PROTOCOL
                or not isinstance(data.get("availability"), dict)
                or not isinstance(data.get("warnings"), list)
                or any(section not in data for section in SECTIONS)):
            return unavailable_workbench_snapshot("展示快照格式无效。")
        if any(data["availability"].get(section) not in {"available", "partial", "unavailable"}
               for section in SECTIONS):
            return unavailable_workbench_snapshot("展示快照状态无效。")
        return data
    except (OSError, UnicodeError, ValueError, RecursionError):
        return unavailable_workbench_snapshot("展示快照无法读取或解析。")


def write_workbench_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    """Atomically publish only the requested snapshot path."""
    path = Path(path)
    raw = (json.dumps(snapshot, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
