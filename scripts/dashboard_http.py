"""Same-origin loopback transport for the existing dashboard server."""
from __future__ import annotations

import hmac
import json
from urllib.parse import urlsplit

MAX_BODY = 1024 * 1024


def _json_constant(value):
    raise ValueError('Non-finite JSON value')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def product_handler(base_handler, service):
    """Extend a static handler; no listener, database or model client is created here."""
    class ProductHandler(base_handler):
        def _reply(self, status, payload):
            raw = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(raw)

        def _deny(self, status, code, message):
            self.close_connection = True
            self._reply(status, {'ok': False, 'error': {'code': code, 'message': message, 'details': {}}})
            return False

        def _guard(self, write=False):
            port = self.server.server_address[1]
            allowed_hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
            hosts = self.headers.get_all('Host', [])
            if len(hosts) != 1 or hosts[0] not in allowed_hosts:
                return self._deny(403, 'invalid_host', '仅支持当前本机服务地址。')
            origins = self.headers.get_all('Origin', [])
            if len(origins) > 1 or (origins and origins[0] not in {f'http://{h}' for h in allowed_hosts}):
                return self._deny(403, 'invalid_origin', '请求必须来自当前本机界面。')
            if self.headers.get('Sec-Fetch-Site') == 'cross-site':
                return self._deny(403, 'cross_site_request', '不接受跨站请求。')
            if write:
                tokens = self.headers.get_all('X-IQS-CSRF', [])
                if len(tokens) != 1 or not hmac.compare_digest(tokens[0].encode('utf8'), service.csrf_token.encode('ascii')):
                    return self._deny(403, 'csrf_required', '请刷新本机页面后重试。')
            return True

        def _is_api(self):
            return urlsplit(self.path).path.startswith('/api/')

        def do_GET(self):
            if not self._guard():
                return
            if self._is_api():
                self._reply(*service.dispatch('GET', self.path))
            else:
                super().do_GET()

        def do_HEAD(self):
            if not self._guard():
                return
            if self._is_api():
                self._deny(405, 'method_not_allowed', '接口只支持声明的方法。')
            else:
                super().do_HEAD()

        def _write(self):
            if not self._guard(write=True):
                return
            if not self._is_api():
                self._deny(405, 'method_not_allowed', '静态资源不可写入。')
                return
            if self.headers.get('Transfer-Encoding') is not None:
                self._deny(400, 'invalid_transfer_encoding', '不支持分块请求。')
                return
            lengths = self.headers.get_all('Content-Length', [])
            try:
                if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal():
                    raise ValueError('length')
                length = int(lengths[0])
                if not 1 <= length <= MAX_BODY:
                    self._deny(413, 'body_too_large', '请求内容必须在1MiB以内。')
                    return
            except ValueError:
                self._deny(400, 'invalid_content_length', '请求长度无效。')
                return
            content_types = self.headers.get_all('Content-Type', [])
            if len(content_types) != 1 or content_types[0].split(';', 1)[0].strip().lower() != 'application/json':
                self._deny(415, 'json_required', '请提交JSON对象。')
                return
            try:
                self.connection.settimeout(10)
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError('incomplete body')
                body = json.loads(raw.decode('utf-8'), parse_constant=_json_constant, object_pairs_hook=_unique_object)
                if not isinstance(body, dict):
                    raise ValueError('object required')
                pending = [(body, 0)]
                while pending:
                    value, depth = pending.pop()
                    if depth > 64:
                        raise ValueError('JSON depth limit')
                    if isinstance(value, dict):
                        pending.extend((item, depth + 1) for item in value.values())
                    elif isinstance(value, list):
                        pending.extend((item, depth + 1) for item in value)
            except (ValueError, UnicodeError, OSError, RecursionError):
                self._deny(400, 'invalid_json', '请求须为有效且无重复字段的JSON对象。')
                return
            self._reply(*service.dispatch(self.command, self.path, body))

        do_POST = _write
        do_PUT = _write

        def do_DELETE(self):
            if self._guard(write=True):
                self._deny(405, 'method_not_allowed', '不支持删除接口。')

    return ProductHandler
