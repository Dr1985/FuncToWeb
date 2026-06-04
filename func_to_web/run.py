import tempfile
from pathlib import Path
from typing import Any, Callable

from .core import save_file_handler, return_file_handler
from .core.server import create_fastapi_app, start_server
from .core.normalization import normalize_input
from .core.utils import create_pytypeinput_assets

from .models import FunctionMetadata
from .routes import setup_multi_items, setup_single_function, setup_download_route, setup_doc_route
from . import call_function


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

    create_pytypeinput_assets()

    if uploads_dir is None:
        uploads_dir = Path(tempfile.gettempdir()) / "func_to_web_uploads"
    save_file_handler.UPLOADS_DIR = Path(uploads_dir)
    save_file_handler.MAX_FILE_SIZE = max_file_size

    if returns_dir is None:
        returns_dir = Path(tempfile.gettempdir()) / "func_to_web_returned_files"
    return_file_handler.RETURNS_DIR = Path(returns_dir)
    return_file_handler.RETURNS_LIFETIME_SECONDS = returns_lifetime

    call_function.STREAM_PRINTS = stream_prints

    count = save_file_handler.cleanup_uploads_dir()
    if count > 0:
        print(f"Cleaned up {count} leftover upload folders from previous run")

    count = return_file_handler.cleanup_returned_files()
    if count > 0:
        print(f"Cleaned up {count} expired returned files from previous run")

    return_file_handler.start_cleanup_timer()

    app_input = normalize_input(func, app_title, css_vars, favicon)

    if fastapi_config is None:
        fastapi_config = {}

    app = create_fastapi_app(root_path, fastapi_config, front_dir, assets_dir)

    setup_download_route(app)
    setup_doc_route(app, app_input)

    if app_input.single_function:
        setup_single_function(app, app_input)
    else:
        setup_multi_items(app, app_input)

    start_server(app, host, port, uvicorn_kwargs)
