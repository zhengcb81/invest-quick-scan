"""OWNERPKG-INVEST-QUICK-SCAN-01: the public ``iqs-job/1`` command-line face.

Fixed-argv client for the owner job façade over the product control-plane HTTP
origin. It never takes paths, command strings or credentials: the request body
is JSON (stdin or ``--request-file``) holding only semantic parameters and the
limits reference. Transport guards (loopback Host, same-origin, CSRF) are the
service's own; this CLI fetches the CSRF token like any local same-origin
client would.

Exit codes follow the repo's public-CLI convention:
- 0  transport-level success: the service returned a well-formed ok envelope
     (an owner-side business refusal that arrives as a 4xx error envelope is
     exit 2, never 0)
- 2  request/contract error (local validation or any HTTP 4xx envelope)
- 1  transport or server failure (connection errors, HTTP 5xx, non-JSON body)
"""
from __future__ import annotations

import argparse
import http.client
import json
import sys
import urllib.parse

WIRE_PROTOCOL = "iqs-job/1"
OPERATIONS = ("submit", "get-status", "allowed-actions", "act", "list-jobs", "get-command")
_WRITE_OPERATIONS = {"submit", "act"}
MAX_BODY_BYTES = 1024 * 1024


def _envelope(data=None, error=None):
    return {"protocol": WIRE_PROTOCOL, "ok": error is None,
            "data": data, "error": error}


def _read_request(explicit_path):
    if explicit_path:
        with open(explicit_path, "rb") as stream:
            raw = stream.read()
    else:
        raw = sys.stdin.buffer.read()
    if not raw.strip():
        raise ValueError("empty request")
    if len(raw) > MAX_BODY_BYTES:
        raise ValueError("request_too_large")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
        parse_constant=lambda item: (_ for _ in ()).throw(ValueError("nonfinite_json")))
    if not isinstance(value, dict):
        raise ValueError("object_required")
    return value


def _request(origin, method, path, body=None, *, csrf_token=None, timeout_seconds=60.0):
    parsed = urllib.parse.urlsplit(origin)
    host = parsed.hostname
    if parsed.port:
        authority = f"{host}:{parsed.port}"
    else:
        authority = host
    connection = http.client.HTTPConnection(host, parsed.port or 80, timeout=timeout_seconds)
    try:
        headers = {"Host": authority, "Accept": "application/json"}
        if csrf_token:
            headers["X-IQS-CSRF"] = csrf_token
        payload = None
        if body is not None:
            payload = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(payload))
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        try:
            envelope = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError):
            return response.status, None
        return response.status, envelope if isinstance(envelope, dict) else None
    finally:
        connection.close()


def _error_from(envelope, fallback_code):
    error = envelope.get("error") if isinstance(envelope, dict) else None
    if isinstance(error, dict) and error.get("code"):
        return {"code": str(error["code"])[:200],
                "message": str(error.get("message", ""))[:500],
                "details": error.get("details") if isinstance(error.get("details"), dict) else {}}
    return {"code": fallback_code, "message": "响应不是有效的产品envelope。", "details": {}}


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="owner_job_cli.py",
        description=("invest-quick-scan公共job面（iqs-job/1）：把Dashboard命令提交为owner job、"
                     "查询JobView/allowed_actions、执行动作并列出有界job目录。"
                     "只接受语义参数与limits引用；不收路径、命令串或凭据；"
                     "预算授权走owner既有spend_authorization链，本CLI不做任何绕过。"))
    parser.add_argument("--origin", required=True,
                        help="本机产品控制面origin，例如 http://127.0.0.1:8765（由open_dashboard启动输出）")
    parser.add_argument("--operation", choices=OPERATIONS, required=True)
    parser.add_argument("--owner-job-id", help="run-*/prepjob_*/deliveryjob_*/batch-* 之ID")
    parser.add_argument("--command-id", help="get-command的命令ID")
    parser.add_argument("--action", choices=("cancel", "resume", "retry", "reconcile"),
                        help="act的动作；幂等键必须随动作一起提供")
    parser.add_argument("--idempotency-key", help="act的动作幂等键（同键重放返回同一结果）")
    parser.add_argument("--cursor", help="list-jobs续页cursor（首页省略）")
    parser.add_argument("--limit", type=int, default=50, help="list-jobs页大小（1-100，默认50）")
    parser.add_argument("--request-file", help="submit/act的JSON请求体文件；缺省读stdin")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--pretty", action="store_true", help="缩进输出")
    args = parser.parse_args(argv)

    origin = args.origin.strip()
    parsed = urllib.parse.urlsplit(origin)
    if parsed.scheme not in ("http", "https") or not parsed.hostname \
            or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        print(_emit(_envelope(error={"code": "origin_invalid",
              "message": "--origin必须是本机loopback http(s) origin。", "details": {}}), args.pretty))
        return 2
    try:
        if args.operation == "submit":
            body = _read_request(args.request_file)
            status, envelope = _request(origin, "GET", "/api/product/status",
                                        timeout_seconds=args.timeout_seconds)
            if status != 200 or not isinstance(envelope, dict) or not envelope.get("ok"):
                print(_emit(_envelope(error=_error_from(envelope, "status_unavailable")), args.pretty))
                return 2 if status < 500 else 1
            token = (envelope.get("data") or {}).get("csrf_token")
            status, envelope = _request(origin, "POST", "/api/product/jobs/submit", body,
                csrf_token=token, timeout_seconds=args.timeout_seconds)
        elif args.operation == "act":
            if not args.owner_job_id or not args.action or not args.idempotency_key:
                parser.error("act需要--owner-job-id、--action与--idempotency-key")
            body = {"idempotency_key": args.idempotency_key}
            status, envelope = _request(origin, "GET", "/api/product/status",
                                        timeout_seconds=args.timeout_seconds)
            if status != 200 or not isinstance(envelope, dict) or not envelope.get("ok"):
                print(_emit(_envelope(error=_error_from(envelope, "status_unavailable")), args.pretty))
                return 2 if status < 500 else 1
            token = (envelope.get("data") or {}).get("csrf_token")
            status, envelope = _request(origin, "POST",
                f"/api/product/jobs/{args.owner_job_id}/{args.action}", body,
                csrf_token=token, timeout_seconds=args.timeout_seconds)
        elif args.operation == "get-status":
            if not args.owner_job_id:
                parser.error("get-status需要--owner-job-id")
            status, envelope = _request(origin, "GET", f"/api/product/jobs/{args.owner_job_id}",
                                        timeout_seconds=args.timeout_seconds)
        elif args.operation == "allowed-actions":
            if not args.owner_job_id:
                parser.error("allowed-actions需要--owner-job-id")
            status, envelope = _request(origin, "GET",
                f"/api/product/jobs/{args.owner_job_id}", timeout_seconds=args.timeout_seconds)
            if status == 200 and isinstance(envelope, dict) and envelope.get("ok"):
                data = envelope.get("data") or {}
                view = data.get("job_view") or {}
                envelope = {**envelope, "data": {"protocol": WIRE_PROTOCOL,
                    "owner_job_id": args.owner_job_id,
                    "status": view.get("status"), "status_known": view.get("status_known"),
                    "allowed_actions": view.get("allowed_actions"),
                    "recovery_capability": view.get("recovery_capability"),
                    "mapping_version": data.get("annotation", {}).get("mapping_version"),
                    "API_requests": 0}}
        elif args.operation == "list-jobs":
            query = {"limit": str(args.limit)}
            if args.cursor:
                query["cursor"] = args.cursor
            status, envelope = _request(origin, "GET",
                "/api/product/jobs?" + urllib.parse.urlencode(query),
                timeout_seconds=args.timeout_seconds)
        elif args.operation == "get-command":
            if not args.command_id:
                parser.error("get-command需要--command-id")
            status, envelope = _request(origin, "GET",
                f"/api/product/jobs/commands/{args.command_id}",
                timeout_seconds=args.timeout_seconds)
        else:  # pragma: no cover - argparse restricts choices
            parser.error("未知操作")
    except (OSError, ValueError, UnicodeError) as exc:
        print(_emit(_envelope(error={"code": "transport_error",
              "message": str(exc)[:500], "details": {}}), args.pretty))
        return 1
    if envelope is None:
        print(_emit(_envelope(error={"code": "invalid_envelope",
              "message": "服务响应不是有效JSON对象。", "details": {"http_status": status}}), args.pretty))
        return 1 if status >= 500 or status < 400 else 2
    if status < 400 and envelope.get("ok") is True:
        print(_emit(_envelope(data=envelope.get("data")), args.pretty))
        return 0
    error = _error_from(envelope, "operation_failed")
    print(_emit(_envelope(error=error), args.pretty))
    return 2 if 400 <= status < 500 else 1


def _emit(payload, pretty):
    return json.dumps(payload, ensure_ascii=False, allow_nan=False,
                      indent=2 if pretty else None)


if __name__ == "__main__":
    raise SystemExit(main())
