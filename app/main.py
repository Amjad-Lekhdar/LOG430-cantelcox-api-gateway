import json
import logging
import time
from base64 import b64decode
from base64 import b64encode
from uuid import uuid4
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram
from prometheus_client import generate_latest

from app.core.config import settings

try:
    import redis
    from redis.exceptions import RedisError
except ImportError:
    class RedisError(Exception):
        pass

    redis = None

app = FastAPI(title="CanTelcoX API Gateway", version="0.1.0")

logger = logging.getLogger("cantelcox.api_gateway")
logging.basicConfig(level=logging.INFO, format="%(message)s")

HTTP_REQUESTS_TOTAL = Counter(
    "api_gateway_http_requests_total",
    "Total HTTP requests received by the API Gateway.",
    ["method", "route", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "api_gateway_http_request_duration_seconds",
    "HTTP request duration observed by the API Gateway.",
    ["method", "route", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
HTTP_IN_PROGRESS = Gauge(
    "api_gateway_http_requests_in_progress",
    "HTTP requests currently being processed by the API Gateway.",
    ["method", "route"],
)
CACHE_REQUESTS_TOTAL = Counter(
    "api_gateway_cache_requests_total",
    "Total cache lookups by result.",
    ["service", "result"],
)

redis_client = None

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|10\.0\.2\.2|192\.168\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROUTE_TARGETS = {
    "users": settings.identity_service_url,
    "auth": settings.identity_service_url,
    "orders": settings.order_service_url,
    "lines": settings.line_service_url,
    "catalog": settings.catalog_service_url,
    "customers": settings.customers_service_url,
    "billing": settings.billing_service_url,
    "audit": settings.audit_service_url,
}

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
}

INVALID_AUTHORIZATION_HEADERS = {
    "bearer",
    "bearer undefined",
    "bearer null",
    "bearer none",
}


@app.middleware("http")
async def observe_requests(request: Request, call_next) -> Response:
    started_at = time.perf_counter()
    trace_id = request.headers.get("x-trace-id") or str(uuid4())
    request.state.trace_id = trace_id
    in_progress_route = _route_label(request)
    method = request.method

    HTTP_IN_PROGRESS.labels(method=method, route=in_progress_route).inc()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Trace-Id"] = trace_id
        return response
    except Exception:
        logger.exception(
            _json_log(
                event="http_request_failed",
                trace_id=trace_id,
                method=method,
                path=request.url.path,
                route=_route_label(request),
                status=status_code,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
                client=_client_host(request),
            )
        )
        raise
    finally:
        duration = time.perf_counter() - started_at
        status = str(status_code)
        route = _route_label(request)
        HTTP_IN_PROGRESS.labels(method=method, route=in_progress_route).dec()
        HTTP_REQUESTS_TOTAL.labels(method=method, route=route, status=status).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            route=route,
            status=status,
        ).observe(duration)
        logger.info(
            _json_log(
                event="http_request",
                trace_id=trace_id,
                method=method,
                path=request.url.path,
                route=route,
                status=status_code,
                duration_ms=round(duration * 1000, 2),
                client=_client_host(request),
            )
        )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/routes")
def list_routes() -> dict[str, str]:
    return {
        "/v1/users/*": settings.identity_service_url,
        "/v1/auth/*": settings.identity_service_url,
        "/v1/orders/*": settings.order_service_url,
        "/v1/lines/*": settings.line_service_url,
        "/v1/catalog/*": settings.catalog_service_url,
        "/v1/customers/*": settings.customers_service_url,
        "/v1/billing/*": settings.billing_service_url,
        "/v1/audit/*": settings.audit_service_url,
    }


@app.api_route(
    "/v1/{service}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
@app.api_route(
    "/v1/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy_v1(service: str, request: Request, path: str = "") -> Response:
    target_base_url = ROUTE_TARGETS.get(service)
    if target_base_url is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"No upstream service configured for /v1/{service}"},
        )

    if not target_base_url:
        return JSONResponse(
            status_code=503,
            content={"detail": f"No upstream service configured for /v1/{service}"},
        )

    body = await request.body()
    upstream_path = f"/v1/{service}"
    if path:
        upstream_path = f"{upstream_path}/{path}"

    upstream_url = f"{target_base_url.rstrip('/')}{upstream_path}"
    if request.query_params:
        upstream_url = f"{upstream_url}?{urlencode(request.query_params.multi_items())}"

    headers = _filter_request_headers(dict(request.headers.items()))
    headers["X-Trace-Id"] = request.state.trace_id
    cache_key = _cache_key(service, request.method, upstream_url, headers)

    cached_response = _read_cached_response(cache_key, service)
    if cached_response is not None:
        cached_response.headers["X-Cache"] = "HIT"
        return cached_response

    upstream_request = UrlRequest(
        upstream_url,
        data=body if body else None,
        headers=headers,
        method=request.method,
    )

    try:
        with urlopen(upstream_request, timeout=15) as upstream_response:
            content = upstream_response.read()
            response_headers = _filter_response_headers(dict(upstream_response.headers.items()))
            response = Response(
                content=content,
                status_code=upstream_response.status,
                headers=response_headers,
                media_type=upstream_response.headers.get("content-type"),
            )
            _write_cached_response(cache_key, service, response)
            response.headers["X-Cache"] = "MISS" if cache_key else "BYPASS"
            return response
    except HTTPError as exc:
        content = exc.read()
        response_headers = _filter_response_headers(dict(exc.headers.items()))
        return Response(
            content=content,
            status_code=exc.code,
            headers=response_headers,
            media_type=exc.headers.get("content-type"),
        )
    except URLError as exc:
        return JSONResponse(
            status_code=502,
            content={
                "detail": "Upstream service unavailable",
                "upstream": target_base_url,
                "reason": str(exc.reason),
            },
        )


def _cache_key(service: str, method: str, upstream_url: str, headers: dict[str, str]) -> str | None:
    if not settings.cache_enabled:
        return None

    if method.upper() != "GET":
        return None

    if service not in _cacheable_services():
        return None

    if any(key.lower() == "authorization" for key in headers):
        return None

    return f"api-gateway:v1:{service}:{method.upper()}:{upstream_url}"


def _cacheable_services() -> set[str]:
    return {
        service.strip()
        for service in settings.cache_services.split(",")
        if service.strip()
    }


def _read_cached_response(cache_key: str | None, service: str) -> Response | None:
    if cache_key is None:
        CACHE_REQUESTS_TOTAL.labels(service=service, result="bypass").inc()
        return None

    client = _redis_client()
    if client is None:
        CACHE_REQUESTS_TOTAL.labels(service=service, result="unavailable").inc()
        return None

    try:
        cached_payload = client.get(cache_key)
    except RedisError as exc:
        logger.warning(_json_log(event="cache_read_failed", service=service, reason=str(exc)))
        CACHE_REQUESTS_TOTAL.labels(service=service, result="error").inc()
        return None

    if cached_payload is None:
        CACHE_REQUESTS_TOTAL.labels(service=service, result="miss").inc()
        return None

    try:
        payload = json.loads(cached_payload)
        content = b64decode(payload["body"])
        headers = payload.get("headers", {})
        CACHE_REQUESTS_TOTAL.labels(service=service, result="hit").inc()
        return Response(
            content=content,
            status_code=payload["status_code"],
            headers=headers,
            media_type=payload.get("media_type"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning(_json_log(event="cache_payload_invalid", service=service, reason=str(exc)))
        CACHE_REQUESTS_TOTAL.labels(service=service, result="invalid").inc()
        return None


def _write_cached_response(cache_key: str | None, service: str, response: Response) -> None:
    if cache_key is None or response.status_code != 200:
        return

    client = _redis_client()
    if client is None:
        return

    payload = {
        "status_code": response.status_code,
        "headers": _cacheable_response_headers(dict(response.headers.items())),
        "media_type": response.media_type,
        "body": b64encode(response.body).decode("ascii"),
    }

    try:
        client.setex(cache_key, settings.cache_ttl_seconds, json.dumps(payload))
    except RedisError as exc:
        logger.warning(_json_log(event="cache_write_failed", service=service, reason=str(exc)))


def _cacheable_response_headers(headers: dict[str, str]) -> dict[str, str]:
    excluded = {"content-length", "x-cache"}
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in excluded
    }


def _redis_client():
    global redis_client
    if redis_client is not None:
        return redis_client

    if redis is None:
        logger.warning(_json_log(event="cache_unavailable", reason="redis package not installed"))
        return None

    try:
        redis_client = redis.Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
        )
        redis_client.ping()
    except RedisError as exc:
        logger.warning(_json_log(event="cache_unavailable", reason=str(exc)))
        redis_client = None

    return redis_client


def _filter_response_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }


def _filter_request_headers(headers: dict[str, str]) -> dict[str, str]:
    filtered_headers = {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    authorization_header = next(
        (
            key
            for key, value in filtered_headers.items()
            if key.lower() == "authorization"
            and value.strip().lower() in INVALID_AUTHORIZATION_HEADERS
        ),
        None,
    )
    if authorization_header is not None:
        del filtered_headers[authorization_header]

    return filtered_headers


def _route_label(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path

    path_parts = request.url.path.strip("/").split("/")
    if len(path_parts) >= 2 and path_parts[0] == "v1":
        return "/v1/{service}/{path}"

    return request.url.path


def _client_host(request: Request) -> str:
    if request.client is None:
        return ""
    return request.client.host


def _json_log(**fields: object) -> str:
    return json.dumps(fields, separators=(",", ":"), ensure_ascii=False)
