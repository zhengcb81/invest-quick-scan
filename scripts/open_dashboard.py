"""Start the existing company/question UI from the main project."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description="打开公司与题库浏览器；刷新只读数据，不调用模型。日常启动不运行测试。")
    parser.add_argument("--ui-root", type=Path, default=ROOT.parent / "iqs-question-bank-ui-lab")
    parser.add_argument("--data-root", type=Path, default=ROOT, help="快扫数据根；默认当前项目")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-refresh", action="store_true", help="仅看已构建快照；不重建UI数据")
    parser.add_argument("--plan", action="store_true", help="显示启动范围，不执行")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    ui_root, data_root = args.ui_root.resolve(), args.data_root.resolve()
    serve = ui_root / "scripts" / "serve.py"
    if not serve.is_file():
        parser.exit(2, "UI source is missing; provide --ui-root pointing to iqs-question-bank-ui-lab.\n")
    if not (data_root / "questions" / "catalog.json").is_file():
        parser.exit(2, "Data root has no questions/catalog.json; provide --data-root.\n")
    command = [sys.executable, "-u", "-B", "-X", "utf8", str(serve), "--no-test", "--port", str(args.port)]
    if args.no_refresh:
        command.append("--no-build")
    if args.plan:
        print(json.dumps({"command": command, "cwd": str(ui_root), "data_root": str(data_root),
                          "refresh": not args.no_refresh, "tests": False, "model_calls": False}, ensure_ascii=False))
        return 0
    environment = {**os.environ, "IQS_DATA_ROOT": str(data_root), "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    print("公司与题库浏览器：本机只读展示；缺失评分保持空白。Ctrl+C停止。", flush=True)
    try:
        return subprocess.run(command, cwd=ui_root, env=environment).returncode
    except OSError as exc:
        sys.stderr.write(f"Cannot start UI: {exc}\n")
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
