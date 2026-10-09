"""QA-C06-02 subprocess guard: synthetic only, no provider calls."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

OWNED = Path(os.environ["E97_OWNED_ROOT"]).resolve()
KEY_LEDGER = OWNED / "key-opens.jsonl"
NET_LEDGER = OWNED / "network-attempts.jsonl"
_pair_sockets = []


def _inside(raw):
    if isinstance(raw, int):
        return True
    path = Path(os.fsdecode(raw)).resolve()
    if path == Path(os.devnull).resolve():
        return True
    return path.is_relative_to(OWNED)


def _append(ledger, payload):
    with Path(ledger).open("a", encoding="utf-8") as stream:
        stream.write(payload + "\n")


def audit(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "socket.bind", "socket.sendto"}:
        # Windows asyncio's internal socketpair: the exact ephemeral loopback
        # bind (127.0.0.1 or ::1, port 0) and connects to exactly that socket.
        # No external address, listener or model/search HTTP is admitted, so
        # the pair never counts as a network attempt.
        if event == "socket.bind" and args[1] in {("127.0.0.1", 0), ("::1", 0)}:
            _pair_sockets.append(args[0])
            return
        if event == "socket.connect":
            for sock in _pair_sockets:
                try:
                    if sock.getsockname() == args[1]:
                        return
                except OSError:
                    pass
        _append(NET_LEDGER, event)
        raise PermissionError("network is forbidden in this test root")
    if event == "open":
        mode, flags = args[1], args[2]
        writing = (isinstance(mode, str) and any(ch in mode for ch in "wax+")) or (
            isinstance(flags, int)
            and flags
            & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        )
        if writing:
            if not _inside(args[0]):
                raise PermissionError("write outside the owned test root")
        elif Path(os.fsdecode(args[0])).name == "llm_apis.json":
            _append(KEY_LEDGER, os.fsdecode(args[0]))
    if event in {"os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.utime"}:
        if not _inside(args[0]):
            raise PermissionError("write outside the owned test root")
    if event in {"os.rename", "os.replace", "os.link", "os.symlink"}:
        if not (_inside(args[0]) and _inside(args[1])):
            raise PermissionError("write outside the owned test root")
    if event in {"os.system", "os.exec", "os.posix_spawn"}:
        raise PermissionError("shell execution is forbidden in this test root")
    if event == "subprocess.Popen":
        executable, argv, cwd, env = args
        same_python = (
            (Path(executable).resolve() == Path(sys.executable).resolve())
            if executable
            else (
                isinstance(argv, str)
                and argv.startswith(subprocess.list2cmdline([sys.executable]) + " ")
            )
        )
        if not same_python:
            raise PermissionError("only Python child processes are allowed")
        if cwd is None or not Path(cwd).resolve().is_relative_to(OWNED):
            raise PermissionError("child cwd outside the owned test root")
        if env is None or env.get("E97_OWNED_ROOT") != str(OWNED):
            raise PermissionError("child guard not inherited")
        if any(key.upper().endswith("_API_KEY") for key in env):
            raise PermissionError("credentials in the child environment")


sys.addaudithook(audit)

if os.environ.get("QA100_STUB_HTTP") == "1":
    import requests

    responses = json.loads((OWNED / "stub-responses.json").read_text(encoding="utf-8"))

    class _StubResponse:
        status_code = 200

        def __init__(self, payload, question_id):
            self._payload = payload
            self.headers = {"x-request-id": "req_" + question_id}

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    def _post(self, *args, **kwargs):
        match = re.search(r"Target question_id: ([A-Za-z0-9_.]+)\.", kwargs["json"]["input"])
        if match is None:
            raise AssertionError("dispatch text is missing its target question id")
        question_id = match.group(1)
        _append(
            OWNED / "http-stub-sends.jsonl",
            json.dumps({"question_id": question_id, "model_requested": kwargs["json"]["model"], "synthetic_only": True}),
        )
        return _StubResponse(json.loads(responses[question_id]), question_id)

    requests.Session.post = _post

import hashlib
import time
import requests
from src.utils.quick_scan_work_store import QuickScanWorkStore

def _clock():
    return float((OWNED / "store-clock.txt").read_text("utf-8"))

_original_init = QuickScanWorkStore.__init__
def _store_init(self, path, **kwargs):
    kwargs["clock"] = _clock
    _original_init(self, path, **kwargs)
QuickScanWorkStore.__init__ = _store_init

def _pause(point):
    if os.environ.get("IQS_CHILD_PAUSE") != point:
        return
    (OWNED / "child-barrier.json").write_text(
        json.dumps({"point": point, "pid": os.getpid()}), encoding="utf-8")
    # Parent really terminates this process. A timeout raises if that never
    # happens, so a hung fixture cannot silently become a successful run.
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        time.sleep(0.02)
    raise RuntimeError("synthetic parent did not terminate the child")

_original_search_result = QuickScanWorkStore.record_external_search
def _record_search(self, *args, **kwargs):
    result = _original_search_result(self, *args, **kwargs)
    _pause("search_settled")
    return result
QuickScanWorkStore.record_external_search = _record_search

_original_mcp_result = QuickScanWorkStore.record_mcp_stage
def _record_control(self, *args, **kwargs):
    result = _original_mcp_result(self, *args, **kwargs)
    _pause("settled:" + result["stage"])
    return result
QuickScanWorkStore.record_mcp_stage = _record_control

def _sent(kind, *, payload=None):
    entry = {"kind": kind, "pid": os.getpid(), "synthetic_only": True}
    if payload is not None and kind == "model":
        entry.update(model=payload["model"],
            has_context="Synthetic margin disclosure" in payload["input"],
            native_tools="tools" in payload,
            thinking=payload.get("reasoning"),
            input_sha256=hashlib.sha256(payload["input"].encode()).hexdigest())
    _append(OWNED / "external-child-http.jsonl", json.dumps(entry))
    _pause("sent:" + kind)

def _response(payload, *, status=200, headers=None):
    response = requests.Response()
    response.status_code = status
    response.headers.update({"Content-Type": "application/json", "x-request-id": "synthetic-child-request", **(headers or {})})
    response._content = b"" if payload is None else json.dumps(payload).encode()
    response._content_consumed = True
    response.encoding = "utf-8"
    return response

def _source():
    return {"title": "Synthetic issuer", "url": "https://fixture.example/ir",
        "description": "Synthetic margin disclosure", "page_age": "2026-09-01"}

def _search_request(self, method, url, **kwargs):
    if url == "https://api.search.brave.com/res/v1/web/search":
        assert method == "GET"
        _sent("search")
        return _response({"web": {"results": [_source()]}})
    assert url == "https://api.z.ai/api/mcp/web_search_prime/mcp" and method == "POST"
    message = kwargs["json"]
    rpc_method = message["method"]
    _sent(rpc_method)
    if rpc_method == "initialize":
        result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
            "serverInfo": {"name": "synthetic-child", "version": "1"}}
        return _response({"jsonrpc": "2.0", "id": message["id"], "result": result},
            headers={"Mcp-Session-Id": "SYNTHETIC_PRIVATE_SESSION"})
    assert kwargs["headers"]["Mcp-Session-Id"] == "SYNTHETIC_PRIVATE_SESSION"
    assert kwargs["headers"]["MCP-Protocol-Version"] == "2024-11-05"
    if rpc_method == "notifications/initialized":
        assert "id" not in message
        return _response(None, status=202)
    if rpc_method == "tools/list":
        result = {"tools": [{"name": "web_search_prime", "inputSchema": {
            "type": "object", "properties": {"search_query": {"type": "string"}},
            "required": ["search_query"], "additionalProperties": False}}]}
    else:
        assert rpc_method == "tools/call"
        assert message["params"]["name"] == "web_search_prime"
        assert set(message["params"]["arguments"]) == {"search_query"}
        result = {"content": [{"type": "text", "text": json.dumps([{
            "title": "Synthetic issuer", "url": "https://fixture.example/ir",
            "content": "Synthetic margin disclosure", "publish_date": "2026-09-01"}])}]}
    return _response({"jsonrpc": "2.0", "id": message["id"], "result": result})

def _model_post(self, url, **kwargs):
    assert url in {"https://api.openai.com/v1/responses", "https://api.deepseek.com/responses"}
    payload = kwargs["json"]
    _sent("model", payload=payload)
    body = {"entity_id": "ENT_SYNTHETIC", "company_name": "Fixture Corp", "question_id": "IQS_05",
        "status": "scored", "score": 6, "description": "Synthetic supported answer"}
    standard_path = OWNED / "standard-synthetic.json"
    if standard_path.exists():
        standard = json.loads(standard_path.read_text("utf-8"))
        body.update(status=standard["status"], score=standard["score"],
            information_as_of=standard["information_as_of"], description=json.dumps(standard))
    output = [{"type": "reasoning", "content": [{"type": "reasoning_text", "text": "PRIVATE_CHILD_THINKING"}]}]
    if "tools" in payload:
        output.append({"type": "web_search_call", "id": "synthetic-native-call", "status": "completed",
            "action": {"type": "search", "sources": [{"url": "https://fixture.example/ir"}]}})
    output.append({"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": json.dumps(body)}]})
    return _response({"id": "synthetic-child-model", "model": payload["model"], "status": "completed",
        "usage": {"input_tokens": 1000, "output_tokens": 10, "input_tokens_details": {"cached_tokens": 0}}, "output": output})

if os.environ.get("IQS_CHILD_HTTP") == "1":
    requests.Session.request = _search_request
    requests.Session.post = _model_post
