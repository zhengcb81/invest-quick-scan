"""Retired command stub for the former engineering task-receipt verifier.

Historical source and tests are preserved in
docs/implementation/archive/task-receipts-v2-legacy/ and are not active gates.
"""
import json


def main() -> int:
    print(json.dumps({
        "status": "retired",
        "code": "task_receipt_workflow_retired",
        "archive": "docs/implementation/archive/task-receipts-v2-legacy/README.md",
    }, separators=(",", ":")))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
