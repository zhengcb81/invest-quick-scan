"""Reuse the existing node's generic test audit; no transport/owner overrides."""
import hashlib
import importlib.util
import os
from pathlib import Path

try:
    own = Path(__file__).resolve().parents[1]
    if Path(os.environ["IQS_PROFILE_SMOKE_TEST_ROOT"]).resolve() != own:
        raise ValueError("wrong_isolated_test_root")
    if Path(os.environ["IQS_CONTINUATION_OWN"]).resolve() != own:
        raise ValueError("wrong_isolated_audit_root")
    audit_path = own.parent / "native-continuation-v15-candidate/guard/write_audit.py"
    if hashlib.sha256(audit_path.read_bytes()).hexdigest() != "e8361a340a6307e9e7d6605828d614e057bd5134e8ed790c2faebd9e177f29b5":
        raise ValueError("existing_write_audit_changed")
    spec = importlib.util.spec_from_file_location("profile_existing_write_audit", audit_path)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
except BaseException:
    # Python normally logs and ignores sitecustomize import failures. Such a
    # failure must not silently turn a denied-network test into an online run.
    os.write(2, b"isolated profile test guard failed closed\n")
    os._exit(78)
