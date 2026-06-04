from typing import Any
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
import uvicorn

from .constants import UVICORN_DEFAULTS


def create_fastapi_app(
    root_path: str = "",
    fastapi_config: dict[str, Any] | None = None,
    front_dir: str | Path | None = None,
    assets_dir: str | Path | None = None,
) -> FastAPI:
    """Create and configure the FastAPI app."""
    base_config = {"root_path": root_path}

    if fastapi_config:
        clean_config = {k: v for k, v in fastapi_config.items() if k != "root_path"}
        base_config.update(clean_config)

    app = FastAPI(**base_config)

    if front_dir is not None:
        app.mount("/front", StaticFiles(directory=Path(front_dir), html=True), name="front")

    if assets_dir is not None:
        app.mount("/assets", StaticFiles(directory=Path(assets_dir)), name="assets")

    return app


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

    clean_kwargs = {k: v for k, v in uvicorn_kwargs.items() if k != "root_path"}
    config.update(clean_kwargs)

    uvicorn_config = uvicorn.Config(app, **config)
    server = uvicorn.Server(uvicorn_config)

    server.run()
