from typing import Any
from fastapi import FastAPI
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
    """Serve the combined CSS/JS bundles from memory (no disk writes).

    The bundles are captured by closure. No cache headers / ETag / compression.
    """
    @app.get("/_functoweb/static/styles.css")
    async def _functoweb_styles():
        return Response(css, media_type="text/css")

    @app.get("/_functoweb/static/scripts.js")
    async def _functoweb_scripts():
        return Response(js, media_type="application/javascript")


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
