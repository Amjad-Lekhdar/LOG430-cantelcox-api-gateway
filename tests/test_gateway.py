import asyncio
import json
from urllib.error import HTTPError
from urllib.error import URLError

import pytest
from fastapi.responses import Response
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


def test_upstream_http_error_is_relayed(monkeypatch, restore_route_targets):
    gateway.ROUTE_TARGETS["catalog"] = "http://catalog.example.test"

    def failing_upstream(*args, **kwargs):
        raise HTTPError(
            url="http://catalog.example.test/v1/catalog/plans",
            code=409,
            msg="Conflict",
            hdrs={"content-type": "application/json", "connection": "close"},
            fp=FakeErrorBody({"detail": "plan unavailable"}),
        )

    monkeypatch.setattr(gateway, "urlopen", failing_upstream)

    response = _call_proxy("catalog", path="plans")

    assert response.status_code == 409
    assert response.headers["content-type"] == "application/json"
    assert "connection" not in response.headers
    assert _json_body(response) == {"detail": "plan unavailable"}


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
    gateway.settings.cache_enabled = True
    gateway.settings.cache_services = "catalog"
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
    gateway.settings.cache_enabled = True
    gateway.settings.cache_services = "catalog"
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


def test_metrics_endpoint_exposes_prometheus_payload():
    response = gateway.metrics()

    assert response.media_type.startswith("text/plain")
    assert b"api_gateway_http_requests_total" in response.body


def test_observe_requests_adds_trace_id_header():
    request = _request("GET", "/health", headers=[(b"x-trace-id", b"trace-from-client")])

    async def call_next(received_request):
        assert received_request.state.trace_id == "trace-from-client"
        return Response(content=b"ok", status_code=204)

    response = asyncio.run(gateway.observe_requests(request, call_next))

    assert response.status_code == 204
    assert response.headers["x-trace-id"] == "trace-from-client"


def test_observe_requests_logs_and_reraises_failures():
    request = _request("GET", "/health")

    async def failing_call_next(received_request):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(gateway.observe_requests(request, failing_call_next))


def test_cache_key_rules_and_cacheable_service_parsing(restore_cache):
    gateway.settings.cache_enabled = True
    gateway.settings.cache_services = " catalog, billing ,, "

    assert gateway._cacheable_services() == {"catalog", "billing"}
    assert gateway._cache_key("catalog", "GET", "http://upstream/v1/catalog/plans", {}) is not None
    assert gateway._cache_key("catalog", "POST", "http://upstream/v1/catalog/plans", {}) is None
    assert gateway._cache_key("orders", "GET", "http://upstream/v1/orders", {}) is None
    assert (
        gateway._cache_key(
            "catalog",
            "GET",
            "http://upstream/v1/catalog/plans",
            {"Authorization": "Bearer token"},
        )
        is None
    )

    gateway.settings.cache_enabled = False
    assert gateway._cache_key("catalog", "GET", "http://upstream/v1/catalog/plans", {}) is None


def test_cache_read_handles_bypass_unavailable_errors_and_invalid_payload(monkeypatch, restore_cache):
    assert gateway._read_cached_response(None, "catalog") is None

    gateway.redis_client = None
    monkeypatch.setattr(gateway, "redis", None)
    assert gateway._read_cached_response("cache-key", "catalog") is None

    gateway.redis_client = FakeRedis(raise_on_get=True)
    assert gateway._read_cached_response("cache-key", "catalog") is None

    gateway.redis_client = FakeRedis(items={"cache-key": json.dumps({"body": "not-base64"})})
    assert gateway._read_cached_response("cache-key", "catalog") is None


def test_redis_client_handles_connection_error(monkeypatch, restore_cache):
    class FakeRedisFactory:
        class Redis:
            @staticmethod
            def from_url(*args, **kwargs):
                return FailingPingRedis()

    gateway.redis_client = None
    monkeypatch.setattr(gateway, "redis", FakeRedisFactory)

    assert gateway._redis_client() is None
    assert gateway.redis_client is None


def test_cache_write_skips_non_cacheable_and_handles_unavailable_or_failing_client(monkeypatch, restore_cache):
    gateway.redis_client = FakeRedis()
    response = Response(content=b"accepted", status_code=202)

    gateway._write_cached_response("cache-key", "catalog", response)
    assert gateway.redis_client.items == {}

    gateway._write_cached_response(None, "catalog", Response(content=b"ok", status_code=200))
    assert gateway.redis_client.items == {}

    gateway.redis_client = None
    monkeypatch.setattr(gateway, "redis", None)
    gateway._write_cached_response("cache-key", "catalog", Response(content=b"ok", status_code=200))

    gateway.redis_client = FakeRedis(raise_on_setex=True)
    gateway._write_cached_response("cache-key", "catalog", Response(content=b"ok", status_code=200))
    assert gateway.redis_client.items == {}


def test_header_filtering_and_route_helpers():
    filtered_request_headers = gateway._filter_request_headers(
        {
            "Host": "gateway.local",
            "Connection": "keep-alive",
            "Authorization": "Bearer undefined",
            "X-Correlation-Id": "abc",
        }
    )

    assert filtered_request_headers == {"X-Correlation-Id": "abc"}

    filtered_response_headers = gateway._filter_response_headers(
        {"Content-Type": "application/json", "Transfer-Encoding": "chunked"}
    )
    assert filtered_response_headers == {"Content-Type": "application/json"}

    cacheable_headers = gateway._cacheable_response_headers(
        {"Content-Type": "application/json", "Content-Length": "2", "X-Cache": "MISS"}
    )
    assert cacheable_headers == {"Content-Type": "application/json"}

    assert gateway._route_label(_request("GET", "/v1/catalog/plans")) == "/v1/{service}/{path}"
    assert gateway._route_label(_request("GET", "/health")) == "/health"
    routed_request = _request("GET", "/health")
    routed_request.scope["route"] = FakeRoute("/health")
    assert gateway._route_label(routed_request) == "/health"

    no_client_request = _request("GET", "/health")
    no_client_request.scope["client"] = None
    assert gateway._client_host(no_client_request) == ""
    assert gateway._client_host(_request("GET", "/health")) == "127.0.0.1"


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
    def __init__(self, items=None, raise_on_get=False, raise_on_setex=False):
        self.items = items or {}
        self.raise_on_get = raise_on_get
        self.raise_on_setex = raise_on_setex

    def get(self, key):
        if self.raise_on_get:
            raise gateway.RedisError("read failed")
        return self.items.get(key)

    def setex(self, key, ttl, value):
        if self.raise_on_setex:
            raise gateway.RedisError("write failed")
        assert ttl == gateway.settings.cache_ttl_seconds
        self.items[key] = value


class FailingPingRedis:
    def ping(self):
        raise gateway.RedisError("redis unavailable")


class FakeRoute:
    def __init__(self, path):
        self.path = path


class FakeErrorBody:
    def __init__(self, body):
        self._body = json.dumps(body).encode()

    def read(self):
        return self._body

    def close(self):
        pass


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
