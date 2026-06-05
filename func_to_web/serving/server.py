import hashlib
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import Response
import uvicorn


def create_fastapi_app(fastapi_config: dict[str, Any] | None = None) -> FastAPI:
    """Create and configure the FastAPI app.

    FastAPI's auto-generated Swagger UI (`/docs`), ReDoc (`/redoc`) and
    `/openapi.json` are off by default: the functions are exposed by name,
    not as typed OpenAPI operations, so that schema would misdescribe them —
    `/doc` is the honest, machine-readable description. Re-enable any of them
    via `fastapi_config` (e.g. `{"docs_url": "/docs"}`).

    root_path is intentionally absent: mounted apps get their per-request
    prefix from Starlette, and for standalone reverse-proxy mode run() passes
    root_path through to Uvicorn, which injects it into the ASGI scope.
    """
    return FastAPI(**{
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
        **(fastapi_config or {}),
    })


def setup_static_routes(app: FastAPI, css: str, js: str) -> None:
    """Serve the combined CSS/JS bundles from memory, browser-cacheable.

    max-age: repeat loads within the window (e.g. reopening a modal) hit the
    browser cache with zero requests. ETag: once max-age expires, the browser
    revalidates cheaply (304, ~200 bytes) instead of re-downloading; a restart
    with new code changes the hash, so stale bundles fix themselves.
    """
    css_etag = f'"{hashlib.md5(css.encode()).hexdigest()}"'
    js_etag = f'"{hashlib.md5(js.encode()).hexdigest()}"'
    CACHE = "max-age=3600"

    def _serve(request: Request, body: str, etag: str, media_type: str):
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304,
                            headers={"ETag": etag, "Cache-Control": CACHE})
        return Response(body, media_type=media_type,
                        headers={"ETag": etag, "Cache-Control": CACHE})

    @app.get("/_functoweb/static/styles.css")
    async def _functoweb_styles(request: Request):
        return _serve(request, css, css_etag, "text/css")

    @app.get("/_functoweb/static/scripts.js")
    async def _functoweb_scripts(request: Request):
        return _serve(request, js, js_etag, "application/javascript")


def start_server(
    app: FastAPI,
    host: str,
    port: int,
    uvicorn_kwargs: dict[str, Any]
) -> None:
    """Start the Uvicorn server with user-provided config.

    No deployment opinions are hardcoded: Uvicorn's own defaults apply, and any
    tuning (limits, timeouts, workers...) is passed through via uvicorn_kwargs.
    """
    uvicorn_config = uvicorn.Config(app, host=host, port=port, **uvicorn_kwargs)
    server = uvicorn.Server(uvicorn_config)

    server.run()
