import asyncio
import json
from urllib.error import URLError

import pytest
from starlette.requests import Request

import app.main as gateway


@pytest.fixture
def restore_route_targets():
    original = gateway.ROUTE_TARGETS.copy()
    yield
    gateway.ROUTE_TARGETS.clear()
    gateway.ROUTE_TARGETS.update(original)


def test_health_returns_ok():
    assert gateway.health_check() == {"status": "ok", "service": "api-gateway"}


def test_routes_returns_configured_upstreams():
    routes = gateway.list_routes()

    assert "/v1/users/*" in routes
    assert "/v1/orders/*" in routes
    assert "/v1/catalog/*" in routes


def test_unknown_route_returns_404():
    response = _call_proxy("unknown", path="resource")

    assert response.status_code == 404
    assert _json_body(response)["detail"] == "No upstream service configured for /v1/unknown"


def test_known_unconfigured_route_returns_503(restore_route_targets):
    gateway.ROUTE_TARGETS["catalog"] = ""

    response = _call_proxy("catalog", path="plans")

    assert response.status_code == 503
    assert _json_body(response)["detail"] == "No upstream service configured for /v1/catalog"


def test_unavailable_upstream_returns_502(monkeypatch, restore_route_targets):
    gateway.ROUTE_TARGETS["catalog"] = "http://catalog.example.test"

    def unavailable_upstream(*args, **kwargs):
        raise URLError("connection refused")

    monkeypatch.setattr(gateway, "urlopen", unavailable_upstream)

    response = _call_proxy("catalog", path="plans")

    assert response.status_code == 502
    assert _json_body(response)["detail"] == "Upstream service unavailable"
    assert _json_body(response)["upstream"] == "http://catalog.example.test"


def test_proxy_forwards_request_to_mock_upstream(monkeypatch, restore_route_targets):
    gateway.ROUTE_TARGETS["orders"] = "http://orders.example.test"

    def mock_upstream(upstream_request, timeout):
        assert timeout == 15
        assert upstream_request.full_url == "http://orders.example.test/v1/orders/test-resource?foo=bar"
        assert upstream_request.get_method() == "GET"
        assert upstream_request.headers["X-trace-id"] == "test-trace-id"
        return FakeUpstreamResponse(
            status=200,
            headers={"content-type": "application/json", "x-upstream": "mock"},
            body={
                "method": upstream_request.get_method(),
                "url": upstream_request.full_url,
                "trace_id": upstream_request.headers["X-trace-id"],
            },
        )

    monkeypatch.setattr(gateway, "urlopen", mock_upstream)

    response = _call_proxy(
        "orders",
        path="test-resource",
        query_string=b"foo=bar",
        headers=[(b"x-trace-id", b"test-trace-id")],
    )

    assert response.status_code == 200
    assert response.headers["x-upstream"] == "mock"
    assert _json_body(response) == {
        "method": "GET",
        "url": "http://orders.example.test/v1/orders/test-resource?foo=bar",
        "trace_id": "test-trace-id",
    }


class FakeUpstreamResponse:
    def __init__(self, status, headers, body):
        self.status = status
        self.headers = headers
        self._body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self._body


def _call_proxy(service, path="", query_string=b"", headers=None):
    request = _request("GET", f"/v1/{service}/{path}".rstrip("/"), query_string, headers)
    request.state.trace_id = request.headers.get("x-trace-id", "test-generated-trace-id")
    return asyncio.run(gateway.proxy_v1(service=service, request=request, path=path))


def _request(method, path, query_string=b"", headers=None):
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "query_string": query_string,
            "headers": headers or [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
        },
        receive,
    )


def _json_body(response):
    return json.loads(response.body.decode())
