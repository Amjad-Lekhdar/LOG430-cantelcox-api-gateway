from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.core.config import settings

app = FastAPI(title="CanTelcoX API Gateway", version="0.1.0")

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


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.get("/routes")
def list_routes() -> dict[str, str]:
    return {
        "/v1/users/*": settings.identity_service_url,
        "/v1/auth/*": settings.identity_service_url,
        "/v1/orders/*": settings.order_service_url,
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
            return Response(
                content=content,
                status_code=upstream_response.status,
                headers=response_headers,
                media_type=upstream_response.headers.get("content-type"),
            )
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
