"""Launch the existing read-only VIEW package; no API or database access here."""
from __future__ import annotations

import argparse
from pathlib import Path
import runpy
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description="查看已有快扫导出；不扫描、不刷新、不调用模型。关闭终端或 Ctrl+C 停止服务。")
    parser.add_argument("--bundle", required=True, help="已导出的 bundle.json；不默认载入合成示例")
    parser.add_argument("--viewer-root", type=Path,
                        default=Path(__file__).resolve().parents[2] / "iqs-viewer-lab",
                        help="VIEW 源码目录，默认同级 iqs-viewer-lab")
    parser.add_argument("--port", type=int, default=0, help="默认随机本机端口")
    parser.add_argument("--open", dest="open_browser", action="store_true", help="同时打开浏览器")
    args = parser.parse_args(argv)
    source = args.viewer_root.resolve() / "src"
    if not (source / "iqs_viewer_lab" / "__main__.py").is_file():
        sys.stderr.write("Viewer source is missing; provide --viewer-root pointing to iqs-viewer-lab.\n")
        return 2
    command = ["serve", "--bundle", str(Path(args.bundle).resolve()), "--host", "127.0.0.1", "--port", str(args.port)]
    if args.open_browser:
        command.append("--open")
    # Run the public -m entry in this process so existing launchers still own
    # the listener PID and terminating that PID closes the listener.
    argv, search_path = sys.argv[:], sys.path[:]
    try:
        sys.argv[1:] = command
        sys.path.insert(0, str(source))
        runpy.run_module("iqs_viewer_lab", run_name="__main__", alter_sys=True)
    except SystemExit as exit_status:
        return exit_status.code
    finally:
        sys.argv[:] = argv
        sys.path[:] = search_path
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
