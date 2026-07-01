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


@pytest.fixture
def restore_cache():
    original_client = gateway.redis_client
    original_cache_enabled = gateway.settings.cache_enabled
    original_cache_services = gateway.settings.cache_services
    original_cache_ttl_seconds = gateway.settings.cache_ttl_seconds
    yield
    gateway.redis_client = original_client
    gateway.settings.cache_enabled = original_cache_enabled
    gateway.settings.cache_services = original_cache_services
    gateway.settings.cache_ttl_seconds = original_cache_ttl_seconds


def test_health_returns_ok():
    assert gateway.health_check() == {"status": "ok", "service": "api-gateway"}


def test_routes_returns_configured_upstreams():
    routes = gateway.list_routes()

    assert "/v1/users/*" in routes
    assert "/v1/orders/*" in routes
    assert "/v1/lines/*" in routes
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


def test_catalog_get_is_cached_after_first_upstream_call(
    monkeypatch,
    restore_route_targets,
    restore_cache,
):
    gateway.ROUTE_TARGETS["catalog"] = "http://catalog.example.test"
    gateway.redis_client = FakeRedis()
    upstream_calls = []

    def mock_upstream(upstream_request, timeout):
        upstream_calls.append(upstream_request.full_url)
        return FakeUpstreamResponse(
            status=200,
            headers={"content-type": "application/json"},
            body={"plans": [{"id": "mobile-10", "price": "39.99"}]},
        )

    monkeypatch.setattr(gateway, "urlopen", mock_upstream)

    first_response = _call_proxy("catalog", path="plans")
    second_response = _call_proxy("catalog", path="plans")

    assert first_response.headers["x-cache"] == "MISS"
    assert second_response.headers["x-cache"] == "HIT"
    assert _json_body(second_response) == {"plans": [{"id": "mobile-10", "price": "39.99"}]}
    assert upstream_calls == ["http://catalog.example.test/v1/catalog/plans"]


def test_authenticated_get_bypasses_cache(monkeypatch, restore_route_targets, restore_cache):
    gateway.ROUTE_TARGETS["catalog"] = "http://catalog.example.test"
    gateway.redis_client = FakeRedis()
    upstream_calls = []

    def mock_upstream(upstream_request, timeout):
        upstream_calls.append(upstream_request.full_url)
        return FakeUpstreamResponse(
            status=200,
            headers={"content-type": "application/json"},
            body={"call": len(upstream_calls)},
        )

    monkeypatch.setattr(gateway, "urlopen", mock_upstream)

    first_response = _call_proxy(
        "catalog",
        path="plans",
        headers=[(b"authorization", b"Bearer valid-token")],
    )
    second_response = _call_proxy(
        "catalog",
        path="plans",
        headers=[(b"authorization", b"Bearer valid-token")],
    )

    assert first_response.headers["x-cache"] == "BYPASS"
    assert second_response.headers["x-cache"] == "BYPASS"
    assert _json_body(first_response) == {"call": 1}
    assert _json_body(second_response) == {"call": 2}
    assert len(upstream_calls) == 2


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


class FakeRedis:
    def __init__(self):
        self.items = {}

    def get(self, key):
        return self.items.get(key)

    def setex(self, key, ttl, value):
        assert ttl == gateway.settings.cache_ttl_seconds
        self.items[key] = value


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
