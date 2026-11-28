"""Phase 2 native IQS diagnostics for the installed local commands and listener."""
import http.client
import json
import os
import socket
import subprocess
import sys

import pytest

from test_view_launcher import ROOT, _dashboard_fixture, _env, _start_dashboard, _stop_dashboard


@pytest.fixture
def native_environment(tmp_path):
    guard = tmp_path / "offline"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import sys\n"
        "def local_only(event, args):\n"
        "    if event in ('socket.connect', 'socket.sendto'):\n"
        "        raise PermissionError('isolated IQS subprocess may only listen on loopback')\n"
        "    if event in ('socket.getaddrinfo','socket.gethostbyaddr','socket.gethostbyname') and args[0] not in ('127.0.0.1','localhost','::1'):\n"
        "        raise PermissionError('isolated IQS fixture blocks DNS')\n"
        "    if event == 'socket.bind' and args[1][0] not in ('127.0.0.1','::1'):\n"
        "        raise PermissionError('isolated IQS fixture requires loopback')\n"
        "sys.addaudithook(local_only)\n",
        encoding="utf8",
    )
    runs = tmp_path / "runs"
    return {
        **_env(tmp_path), "PYTHONPATH": str(guard),
        "IQS_FEEDBACK_RUNS_ROOT": str(runs),
        "RESEARCH_FEEDBACK_OUT": str(tmp_path / "f4.jsonl"),
        "USERPROFILE": str(tmp_path), "HOME": str(tmp_path),
    }, runs / "dashboard-runtime"


def run_entry(tmp_path, env, name, *arguments, body=b""):
    return subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts" / (name + ".py")), *map(str, arguments)],
        cwd=tmp_path, env=env, input=body, capture_output=True, timeout=12,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def diagnostics(state):
    return [json.loads(path.read_bytes()) for path in sorted((state / "diagnostics").glob("*.jsonl"))]


def test_native_cli_faults_retain_original_exit_and_actual_cause(tmp_path, native_environment):
    env, runtime = native_environment
    ui, state, cfg = _dashboard_fixture(tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"{")
    inventory = (
        ("open_dashboard", ("--port", "65536"), b"--port must be between",
         "invalid_arguments", "SystemExit"),
        ("open_dashboard", ("--port", "0", "--ui-root", ui, "--dashboard-config", bad),
         b"Dashboard configuration is invalid:", "dashboard_config_invalid", "JSONDecodeError"),
        ("workbench_snapshot_cli", ("--dashboard-config", bad, "--output", tmp_path / "out.json"),
         b"Snapshot export failed:", "snapshot_export_failed", "JSONDecodeError"),
    )
    for entry, argv, message, _, _ in inventory:
        original = run_entry(tmp_path, env, entry, *argv)
        assert (original.returncode, original.stdout) == (2, b"")
        assert message in original.stderr and b"IQS failure tracking incomplete" not in original.stderr
    assert not (tmp_path / "out.json").exists()
    found = {item["observation"]["actual"]: item["chain"][0]["type"] for item in diagnostics(runtime)}
    assert found == {code: kind for _, _, _, code, kind in inventory}

    with socket.socket() as occupied:
        if os.name == "nt":
            occupied.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        port = occupied.getsockname()[1]
        failed = run_entry(tmp_path, env, "open_dashboard", "--port", port, "--no-refresh",
                           "--ui-root", ui, "--dashboard-config", cfg)
    assert (failed.returncode, failed.stdout) == (2, b"")
    assert b"Cannot bind local dashboard:" in failed.stderr
    receipt, = diagnostics(state)
    assert receipt["observation"]["actual"] == "dashboard_bind_failed"
    assert receipt["chain"][0]["family"] == "OSError"

    blocked = tmp_path / "blocked"
    blocked.write_bytes(b"prior bytes")
    failed_both = run_entry(
        tmp_path,
        {**env, "IQS_FEEDBACK_RUNS_ROOT": str(blocked),
         "RESEARCH_FEEDBACK_OUT": str(blocked / "unused.jsonl")},
        "open_dashboard", "--port", "0", "--ui-root", ui, "--dashboard-config", bad,
    )
    assert (failed_both.returncode, failed_both.stdout, blocked.read_bytes()) == (2, b"", b"prior bytes")
    assert failed_both.stderr.count(b"IQS failure tracking incomplete") == 1
    assert b"Dashboard configuration is invalid:" in failed_both.stderr


def test_native_http_keeps_original_400_and_each_original_cause(tmp_path, native_environment):
    env, _ = native_environment
    process, reader, ready, _, state, _ = _start_dashboard(tmp_path, no_refresh=True, environment=env)
    port = ready["port"]
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", "/api/product/status")
        status = connection.getresponse()
        assert status.status == 200
        csrf = json.loads(status.read())["data"]["csrf_token"]
        headers = {"Content-Type": "application/json", "X-IQS-CSRF": csrf,
                   "Origin": f"http://127.0.0.1:{port}"}
        connection.request("POST", "/api/product/universe/apply", b"{", headers=headers)
        refused = connection.getresponse()
        assert refused.status == 400
        malformed_body = refused.read()

        with socket.create_connection(("127.0.0.1", port), timeout=6) as stream:
            request = (
                f"POST /api/product/universe/apply HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n"
                f"Origin: http://127.0.0.1:{port}\r\nX-IQS-CSRF: {csrf}\r\n"
                "Content-Type: application/json\r\nContent-Length: 10\r\nConnection: close\r\n\r\n{"
            )
            stream.sendall(request.encode("ascii"))
            stream.shutdown(socket.SHUT_WR)
            truncated = http.client.HTTPResponse(stream)
            truncated.begin()
            assert truncated.status == 400 and truncated.read() == malformed_body
        assert json.loads(malformed_body)["error"]["code"] == "invalid_json"
        errors = diagnostics(state)
        assert sorted(error["chain"][0]["type"] for error in errors) == ["JSONDecodeError", "ValueError"]
        assert len({error["details_ref"] for error in errors}) == 2
        assert all(error["observation"]["step_id"] == "http.transport" for error in errors)
        assert not (state / "preparation-jobs").exists()
        assert ready["model_calls"] == ready["network_calls"] == 0
    finally:
        connection.close()
        _stop_dashboard(process, reader)


def test_native_rotation_respects_open_archive_handles(tmp_path, native_environment):
    env, runtime = native_environment
    runtime.mkdir(parents=True)
    log = runtime / "runtime-failures.jsonl"
    newest, oldest, staging = (log.with_name(log.name + suffix) for suffix in (".1", ".2", ".rotating"))
    body = b"{" + b"x" * (2 * 1024 * 1024) + b"}\n"
    old_newest, old_oldest = b'{"mark":"newest"}\n', b'{"mark":"oldest"}\n'
    log.write_bytes(body)
    newest.write_bytes(old_newest)
    oldest.write_bytes(old_oldest)
    with newest.open("rb") as held:
        first = run_entry(tmp_path, env, "open_dashboard", "--port", "65536")
        assert (first.returncode, first.stdout) == (2, b"")
        assert held.read() == old_newest
        if os.name == "nt":
            assert oldest.read_bytes() == old_oldest
            assert newest.read_bytes() == old_newest
            assert staging.read_bytes() == body
        else:
            assert oldest.read_bytes() == old_newest
            assert newest.read_bytes() == body
            assert not staging.exists()
    second = run_entry(tmp_path, env, "open_dashboard", "--port", "65536")
    assert (second.returncode, second.stdout, second.stderr) == (2, b"", first.stderr)
    assert newest.read_bytes() == body and oldest.read_bytes() == old_newest and not staging.exists()
    assert len(log.read_bytes().splitlines()) == 2


def test_folded_auth_and_uri_userinfo_keep_the_following_diagnostic(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    from iqs_scan.foundation.api import redact_diagnostic_text

    text = ("HTTP 403-https://synthetic-user:fixture-pass@example.invalid/ref\n"
            "Authorization: Bearer fixture-auth\r\n"
            "\tfixture-continuation\r\n"
            "next original diagnostic\n")
    projected = redact_diagnostic_text(text)
    assert projected.startswith("HTTP 403-https://[REDACTED]@example.invalid/ref\n")
    assert projected.endswith("next original diagnostic\n")
    assert all(value not in projected for value in ("fixture-auth", "fixture-continuation", "fixture-pass"))


@pytest.mark.parametrize(("header", "scheme"), (("Authorization", "Bearer"), ("Proxy-Authorization", "Basic")))
def test_authentication_value_on_first_fold_preserves_next_diagnostic(monkeypatch, header, scheme):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    from iqs_scan.foundation.api import redact_diagnostic_text

    values = ("fixture-first-value", "fixture-second-value")
    diagnostic = f"{header}: {scheme} \r\n\t{values[0]}\n  {values[1]}\nNext original diagnostic\n"
    projected = redact_diagnostic_text(diagnostic)
    assert all(value not in projected for value in values)
    assert projected.endswith("Next original diagnostic\n")


@pytest.mark.parametrize("scheme", ("Bearer", "Basic"))
@pytest.mark.parametrize("starts_on_header", (True, False), ids=("inline-start", "folded-start"))
def test_native_invalid_choice_masks_rendered_authorization_folds(
    tmp_path, native_environment, scheme, starts_on_header
):
    env, runtime = native_environment
    tokens = ("synthetic-first-segment", "synthetic-second-segment", "synthetic-third-segment")
    first_separator = " " if starts_on_header else " \r\n\t"
    credential = (
        f"Authorization: {scheme}{first_separator}{tokens[0]}"
        f"\r\n\t{tokens[1]}\n  {tokens[2]}\nRetain this reason"
    )
    refused = run_entry(tmp_path, env, "owner_job_cli", "--operation", credential)
    assert (refused.returncode, refused.stdout) == (2, b"")
    assert b"invalid choice" in refused.stderr and b"Retain this reason" in refused.stderr
    assert b"(choose from" in refused.stderr
    failure, = diagnostics(runtime)
    assert failure["observation"]["actual"] == "invalid_arguments"
    assert failure["chain"][0]["type"] == "SystemExit"
    rendered = refused.stderr + json.dumps(failure).encode("ascii")
    assert all(token.encode("ascii") not in rendered for token in tokens)


@pytest.mark.parametrize("entry", (
    "view_quick_scan", "run_answers_page", "one_click", "thin_scan", "question_sets",
    "owner_job_cli", "identity_contract_cli", "query_contract_cli", "refresh_contract_cli",
    "subject_dispatch_cli", "parallel_handoff_cli", "status_report",
))
def test_published_argument_refusal_reuses_the_native_owner(entry, tmp_path, native_environment):
    env, runtime = native_environment
    refused = run_entry(tmp_path, env, entry, "--unknown-phase2-fixture-option")
    assert (refused.returncode, refused.stdout) == (2, b"") and b"usage:" in refused.stderr
    receipt, = diagnostics(runtime)
    assert receipt["observation"]["actual"] == "invalid_arguments"
    assert receipt["chain"][0]["type"] == "SystemExit"


@pytest.mark.parametrize(("entry", "step"), (
    ("dashboard_owner", "owner.worker.request"), ("dashboard_prepare", "prepare.worker.request"),
))
def test_worker_bad_stdin_before_config_keeps_the_existing_json(entry, step, tmp_path, native_environment):
    env, runtime = native_environment
    refused = run_entry(tmp_path, env, entry, "--worker", body=b"{")
    assert refused.returncode == 2 and not refused.stderr
    reply = json.loads(refused.stdout)
    assert "error" in reply
    receipt, = diagnostics(runtime)
    assert receipt["observation"]["step_id"] == step
    assert receipt["chain"][0]["type"] == "JSONDecodeError"
