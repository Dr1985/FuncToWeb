import tempfile
from pathlib import Path
from typing import Any, Callable

from .core import save_file_handler, return_file_handler
from .core.server import create_fastapi_app, start_server, setup_static_routes
from .core.normalization import normalize_input
from .core.utils import build_static_assets

from .models import FunctionMetadata
from .routes import setup_multi_items, setup_single_function, setup_download_route, setup_doc_route


def run(
    func: Callable[..., Any] | FunctionMetadata | list,
    host: str = "0.0.0.0",
    port: int = 8000,
    app_title: str | None = None,
    css_vars: dict[str, str] | None = None,
    favicon: str | Path | None = None,
    uploads_dir: str | Path | None = None,
    max_file_size: int | None = None,
    returns_dir: str | Path | None = None,
    returns_lifetime: int = 3600,
    stream_prints: bool = True,
    root_path: str = "",
    fastapi_config: dict[str, Any] | None = None,
    front_dir: str | Path | None = None,
    assets_dir: str | Path | None = None,
    **uvicorn_kwargs
):
    """Run the web application server.

    Args:
        func: Single function, FunctionMetadata, or list of functions/groups.
        host: Server host address.
        port: Server port.
        app_title: Custom application title.
        css_vars: CSS variable overrides.
        favicon: Path to favicon file.
        uploads_dir: Directory for uploaded files. Defaults to a
            "func_to_web_uploads" folder inside the OS temp dir.
        max_file_size: Maximum size in bytes for uploaded files, None for unlimited.
        returns_dir: Directory for files returned by functions. Defaults to a
            "func_to_web_returned_files" folder inside the OS temp dir.
        returns_lifetime: Seconds before returned files are deleted (default: 3600).
        stream_prints: If True, print() output is streamed to the client in real time.
        root_path: FastAPI root path for reverse proxy.
        fastapi_config: Additional FastAPI configuration.
        front_dir: Optional directory served at /front (with html=True for SPA-style routing).
        assets_dir: Optional directory served at /assets.
        **uvicorn_kwargs: Additional Uvicorn configuration.
    """
    _auth_removed = (
        "Authentication ('auth'/'secret_key', passed by keyword or positionally) "
        "was removed in 1.5.0 and is being "
        "redesigned. For now, protect your app with a reverse proxy that handles "
        "auth (e.g. Nginx basic auth). See the changelog for details."
    )
    if "auth" in uvicorn_kwargs or "secret_key" in uvicorn_kwargs:
        raise ValueError(_auth_removed)
    # `auth` used to be the 4th positional argument; a dict landing in app_title
    # almost certainly means someone passed the old auth dict positionally.
    if isinstance(app_title, dict):
        raise ValueError(_auth_removed)

    workers = uvicorn_kwargs.get("workers")
    if workers is not None and workers > 1:
        raise ValueError(
            f"'workers={workers}' has no effect: run() starts a single process "
            "and passes the app instance to Uvicorn, which only runs multiple "
            "workers when served by import string. For multiprocess, wait for "
            "create_app() (next release) and serve it with uvicorn/gunicorn via "
            "an import string (e.g. 'uvicorn mymodule:app --workers 4')."
        )

    if uvicorn_kwargs.get("reload"):
        raise ValueError(
            "'reload=True' has no effect: run() passes the app instance to "
            "Uvicorn, whose reloader only runs when serving by import string. "
            "For auto-reload, wait for create_app() (next release) and serve it "
            "with an import string (e.g. 'uvicorn mymodule:app --reload')."
        )

    static_css, static_js = build_static_assets()

    # Normalize root_path once: a trailing slash (e.g. root_path="/tools/") would
    # produce doubled-slash internal URLs like "/tools//add". ASGI convention is
    # no trailing slash; enforce it here so the handlers don't each have to.
    root_path = root_path.rstrip("/")

    uploads_dir = (
        Path(uploads_dir) if uploads_dir is not None
        else Path(tempfile.gettempdir()) / "func_to_web_uploads"
    )
    returns_dir = (
        Path(returns_dir) if returns_dir is not None
        else Path(tempfile.gettempdir()) / "func_to_web_returned_files"
    )

    count = save_file_handler.cleanup_uploads_dir(uploads_dir)
    if count > 0:
        print(f"Cleaned up {count} leftover upload folders from previous run")

    count = return_file_handler.cleanup_returned_files(returns_dir, returns_lifetime)
    if count > 0:
        print(f"Cleaned up {count} expired returned files from previous run")

    app_input = normalize_input(func, app_title, css_vars, favicon)

    if fastapi_config is None:
        fastapi_config = {}

    app = create_fastapi_app(root_path, fastapi_config, front_dir, assets_dir)

    setup_static_routes(app, static_css, static_js)
    setup_download_route(app, returns_dir, returns_lifetime)
    setup_doc_route(app, app_input)

    if app_input.single_function:
        setup_single_function(
            app, app_input,
            uploads_dir=uploads_dir, max_file_size=max_file_size,
            returns_dir=returns_dir, returns_lifetime=returns_lifetime,
            stream_prints=stream_prints,
        )
    else:
        setup_multi_items(
            app, app_input,
            uploads_dir=uploads_dir, max_file_size=max_file_size,
            returns_dir=returns_dir, returns_lifetime=returns_lifetime,
            stream_prints=stream_prints,
        )

    start_server(app, host, port, uvicorn_kwargs)
