"""Archive the ongoing IQS evidence only; never publish StockQA or close gates."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

IQS = Path(__file__).resolve().parents[5]
CONTROL = Path(__file__).parent
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context"
OWN = IQS / "runs/n111a/qa"
INDEX = OUT / "checkpoint-index-01.json"
MANIFEST = IQS / "runs/n111a/checkpoint-paths-01.nul"
BASELINE = "8363b49a7a2799ff5f2ee6afe57c797ef6ca65fb"

HEADER = """**2026-10-09 Phase111正在实施，优先于下文历史：** 下一动作是冻结v1.1外部检索执行计划和已验证计价，并接context→LLM/独立来源proof/公开CLI，见[连续批次计划](reviews/QA-NET-01/external-context-2026-10-09/plan.md)和[精确范围](reviews/QA-NET-01/external-context-2026-10-09/scope.json)。仅IQS自有runs/n111a/qa私有副本有实现，StockQA源仍42a517c/schema8，未发布本批代码。基础24P、传输60P；检索耐久段最终155P、缓存/总保存cap159P、真实耐久permit适配82P，均是分批受影响结果，不能相加作独立覆盖率或声称完整生产链验收。原13/20/4/4 RED及中间4/14失败、300秒超时均留档；155P还覆盖真实OS旧库/crash/race入口，已修正新循环导入和真实旧schema夹具。

**恢复与权限：** 原session66094/86609/17210/71783/66689/24906均已终态，不再凭旧handle等待或重启。runs/n111a仍是本批独占未完成环境，禁止用硬编码Phase110 cleanup/publish helper；共享TEMP、原Phase92、opencode与源七未知项保留。所有本批测试无真实key/外网/收费API，HTTP替身+真实私有SQLite，guard是Python审计边界。schema9只在副本：不可变检索意图/dispatch/短结果、原Q09同事务预留/结算、多题共用查询、跨查询公司保存cap。MCP、执行策略和回答proof未完成；整批静态、公开CLI、集中一次review/源发布及最终严格清理尚未执行。当前提交只是IQS进度和证据checkpoint，以progress实际Git回执为准，不提升任何验收状态。StockQA旧全仓授权须先报备；StockWiki JR1/JR3四新路径仍未获准，G3/F05/真实identity/facts golden/THIN源仓写授权原门保持。

以下为保留的历史交付，不覆盖上方当前状态。

"""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    result = subprocess.run(["git", *args], cwd=IQS, capture_output=True)
    if result.returncode:
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(result.returncode)
    return result.stdout


def prepare():
    assert not INDEX.exists() and not MANIFEST.exists()
    assert git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not git("diff", "--cached", "--name-only").strip()
    latest = json.loads((OUT / "verification/durable-transport-green-01/process.json").read_text("utf-8"))
    assert latest["returncode"] == 0 and not latest["timeout"] and latest["executed_source_unchanged"]
    for name, expected in latest["executed_source_hashes"].items():
        assert sha((OWN / name).read_bytes()) == expected, name
    handoff = IQS / "docs/implementation/handoff-for-new-agent.md"
    original = handoff.read_text("utf-8")
    marker = "**2026-10-09 Phase110当前交付：**"
    assert original.count(marker) == 1
    handoff.write_text(HEADER + original[original.index(marker):], encoding="utf-8")
    paths = sorted(p for root in (OUT, CONTROL) for p in root.rglob("*") if p.is_file())
    assert all(not p.is_symlink() for p in paths)
    records = [{"path": p.relative_to(IQS).as_posix(), "size": p.stat().st_size, "sha256": sha(p.read_bytes())} for p in paths]
    for path in CONTROL.glob("*.py"):
        ast.parse(path.read_text("utf-8"), filename=str(path))
    document = {"phase": 111, "state": "in_progress_private_implementation_not_published", "source_head": "42a517c4bd6bc8219f926957c6c332944da3278a", "production_schema_version": 8, "private_schema_version": 9,
                "latest_executed_source_hashes": latest["executed_source_hashes"], "records": records,
                "pending": ["v1.1_frozen_execution_plan_and_pricing", "mcp_handshake", "external_context_llm_proof", "public_cli", "concentrated_review", "source_publish", "strict_final_cleanup"], "whole_project_gates_closed": False}
    INDEX.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    root_paths = [".gitattributes", "task_plan.md", "progress.md", "findings.md", "docs/implementation/handoff-for-new-agent.md"]
    selected = root_paths + [r["path"] for r in records] + [INDEX.relative_to(IQS).as_posix()]
    MANIFEST.write_bytes(b"".join(p.encode("utf-8") + b"\0" for p in selected))
    print(json.dumps({"artifacts": len(records), "selected": len(selected), "index_sha256": sha(INDEX.read_bytes()), "production_published": False}))


def publish_checkpoint():
    assert git("rev-parse", "HEAD").decode().strip() == BASELINE
    assert not git("diff", "--cached", "--name-only").strip()
    document = json.loads(INDEX.read_text("utf-8"))
    for record in document["records"]:
        raw = (IQS / record["path"]).read_bytes()
        assert len(raw) == record["size"] and sha(raw) == record["sha256"], record["path"]
    selected = MANIFEST.read_bytes().split(b"\0")[:-1]
    assert all(b"opencode" not in p and not p.startswith(b"runs/") for p in selected)
    git("add", "-f", "--pathspec-from-file=" + str(MANIFEST), "--pathspec-file-nul")
    staged = git("diff", "--cached", "--name-only", "-z").split(b"\0")[:-1]
    assert set(staged) == set(selected)
    for record in document["records"]:
        assert sha(git("show", ":" + record["path"])) == record["sha256"], record["path"]
    assert git("show", ":" + INDEX.relative_to(IQS).as_posix()) == INDEX.read_bytes()
    git("diff", "--cached", "--check")
    output = git("commit", "-m", "docs: checkpoint external retrieval journal development")
    sys.stdout.buffer.write(output)
    output = git("push", "origin", "HEAD:master")
    sys.stdout.buffer.write(output)
    print(json.dumps({"commit": git("rev-parse", "HEAD").decode().strip(), "remaining_status": git("status", "--porcelain=v1").decode("utf-8"), "artifacts": len(document["records"]), "production_published": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "git"])
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        publish_checkpoint()
