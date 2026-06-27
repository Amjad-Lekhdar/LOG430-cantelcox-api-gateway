import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request
from urllib.request import urlopen

import pytest
import uvicorn

import app.main as gateway


@pytest.fixture(scope="session")
def gateway_url():
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            gateway.app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    _wait_until_ready(f"{base_url}/health")

    yield base_url

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def mock_upstream_url():
    server = ThreadingHTTPServer(("127.0.0.1", _free_port()), MockUpstreamHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{server.server_port}"

    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture
def restore_route_targets():
    original = gateway.ROUTE_TARGETS.copy()
    yield
    gateway.ROUTE_TARGETS.clear()
    gateway.ROUTE_TARGETS.update(original)


def test_health_returns_ok(gateway_url):
    response = _request(f"{gateway_url}/health")

    assert response["status"] == 200
    assert response["headers"]["x-trace-id"]
    assert response["json"] == {"status": "ok", "service": "api-gateway"}


def test_routes_returns_configured_upstreams(gateway_url):
    response = _request(f"{gateway_url}/routes")

    assert response["status"] == 200
    assert "/v1/users/*" in response["json"]
    assert "/v1/orders/*" in response["json"]
    assert "/v1/catalog/*" in response["json"]


def test_unknown_route_returns_404(gateway_url):
    response = _request(f"{gateway_url}/v1/unknown/resource")

    assert response["status"] == 404
    assert response["json"]["detail"] == "No upstream service configured for /v1/unknown"


def test_known_unconfigured_route_returns_503(gateway_url, restore_route_targets):
    gateway.ROUTE_TARGETS["catalog"] = ""

    response = _request(f"{gateway_url}/v1/catalog/plans")

    assert response["status"] == 503
    assert response["json"]["detail"] == "No upstream service configured for /v1/catalog"


def test_unavailable_upstream_returns_502(gateway_url, restore_route_targets):
    gateway.ROUTE_TARGETS["catalog"] = f"http://127.0.0.1:{_free_port()}"

    response = _request(f"{gateway_url}/v1/catalog/plans")

    assert response["status"] == 502
    assert response["json"]["detail"] == "Upstream service unavailable"
    assert response["json"]["upstream"].startswith("http://127.0.0.1:")


def test_proxy_forwards_request_to_mock_upstream(
    gateway_url,
    mock_upstream_url,
    restore_route_targets,
):
    gateway.ROUTE_TARGETS["orders"] = mock_upstream_url

    response = _request(
        f"{gateway_url}/v1/orders/test-resource?foo=bar",
        headers={"X-Trace-Id": "test-trace-id"},
    )

    assert response["status"] == 200
    assert response["headers"]["x-trace-id"] == "test-trace-id"
    assert response["json"] == {
        "method": "GET",
        "path": "/v1/orders/test-resource",
        "query": "foo=bar",
        "trace_id": "test-trace-id",
    }


class MockUpstreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(
            {
                "method": "GET",
                "path": self.path.split("?", 1)[0],
                "query": self.path.split("?", 1)[1] if "?" in self.path else "",
                "trace_id": self.headers.get("X-Trace-Id"),
            }
        ).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def _request(url, headers=None):
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=5) as response:
            return _response_payload(response)
    except HTTPError as exc:
        return _response_payload(exc)


def _response_payload(response):
    body = response.read()
    headers = {key.lower(): value for key, value in response.headers.items()}
    return {
        "status": response.status,
        "headers": headers,
        "body": body,
        "json": json.loads(body.decode()) if body else None,
    }


def _wait_until_ready(url):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            if _request(url)["status"] == 200:
                return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError(f"Server did not become ready: {url}")


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
