from typing import Any
from fastapi import FastAPI
from fastapi.responses import Response
import uvicorn

from .constants import UVICORN_DEFAULTS


def create_fastapi_app(fastapi_config: dict[str, Any] | None = None) -> FastAPI:
    """Create and configure the FastAPI app.

    root_path is intentionally absent: mounted apps get their per-request
    prefix from Starlette, and run() sets app.root_path after building for
    standalone reverse-proxy mode.
    """
    return FastAPI(**(fastapi_config or {}))


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
    """Start the Uvicorn server with merged default + user config."""
    config = {
        "host": host,
        "port": port,
        **UVICORN_DEFAULTS,
    }

    config.update(uvicorn_kwargs)

    uvicorn_config = uvicorn.Config(app, **config)
    server = uvicorn.Server(uvicorn_config)

    server.run()
