import tempfile
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI

from .core import save_file_handler, return_file_handler
from .core.server import create_fastapi_app, start_server, setup_static_routes
from .core.normalization import normalize_input
from .core.utils import build_static_assets

from .models import FunctionMetadata
from .routes import setup_multi_items, setup_single_function, setup_download_route, setup_doc_route


def _resolve_dirs(
    uploads_dir: str | Path | None,
    returns_dir: str | Path | None,
) -> tuple[Path, Path]:
    """Resolve the uploads/returns directories, defaulting to the OS temp dir.

    Single source of truth for the defaults. Used by create_app() and also by
    run(), which needs the resolved paths *before* building the app in order
    to perform the boot sweeps (run()-only; see create_app docstring).
    """
    uploads = (
        Path(uploads_dir) if uploads_dir is not None
        else Path(tempfile.gettempdir()) / "func_to_web_uploads"
    )
    returns = (
        Path(returns_dir) if returns_dir is not None
        else Path(tempfile.gettempdir()) / "func_to_web_returned_files"
    )
    return uploads, returns


def create_app(
    func: Callable[..., Any] | FunctionMetadata | list,
    app_title: str | None = None,
    css_vars: dict[str, str] | None = None,
    favicon: str | Path | None = None,
    uploads_dir: str | Path | None = None,
    max_file_size: int | None = None,
    returns_dir: str | Path | None = None,
    returns_lifetime: int = 3600,
    stream_prints: bool = True,
    fastapi_config: dict[str, Any] | None = None,
) -> FastAPI:
    """Build the FuncToWeb FastAPI application without starting a server.

    Use this to mount FuncToWeb inside a larger app, or to serve it yourself
    by import string (which enables `uvicorn --workers N` and `--reload`,
    both rejected by run() because it serves an app instance):

        # mounted inside a larger app
        host = FastAPI()
        host.mount("/tools", create_app([add, multiply]))

        # served by import string: `uvicorn mymodule:app --workers 4`
        app = create_app(my_function)

    To serve a static site or SPA next to your functions, compose with
    Starlette's StaticFiles instead of a built-in option:

        host.mount("/tools", create_app(funcs))
        host.mount("/", StaticFiles(directory="dist", html=True))

    All internal URLs are derived per request from the ASGI root_path, so a
    mounted app works under any prefix with no extra configuration.

    Args:
        Same meaning as in run() (see run() docstring). There is no
        `root_path` parameter: when mounted, Starlette sets the per-request
        root_path automatically; standalone behind a proxy, run() handles it.

    Note:
        Unlike run(), create_app() does NOT sweep leftover upload folders or
        expired returned files at build time. Under multiple workers each
        worker builds its own app instance, and a sweep on every build could
        delete a sibling worker's in-flight uploads during rolling restarts.
        Expired returned files are still cleaned up opportunistically at
        runtime (on save and on /download); leftover upload folders are only
        swept by run() at startup.
    """
    static_css, static_js = build_static_assets()

    uploads_dir, returns_dir = _resolve_dirs(uploads_dir, returns_dir)

    app_input = normalize_input(func, app_title, css_vars, favicon)

    # root_path is never set at build time: mounts get their prefix from
    # Starlette per request; standalone proxy mode is run()'s responsibility.
    app = create_fastapi_app(fastapi_config)

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

    return app


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
    **uvicorn_kwargs
):
    """Run the web application server.

    Builds the app via create_app() and serves it with Uvicorn. For mounting
    inside a larger app, serving by import string (multiprocess / reload), or
    serving a static site/SPA alongside your functions, use create_app()
    directly and compose with FastAPI.

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
        **uvicorn_kwargs: Additional Uvicorn configuration.
    """
    workers = uvicorn_kwargs.get("workers")
    if workers is not None and workers > 1:
        raise ValueError(
            f"'workers={workers}' has no effect: run() starts a single process "
            "and passes the app instance to Uvicorn, which only runs multiple "
            "workers when served by import string. For multiprocess, build the "
            "app with create_app() and serve it with uvicorn/gunicorn via an "
            "import string (e.g. 'uvicorn mymodule:app --workers 4')."
        )

    if uvicorn_kwargs.get("reload"):
        raise ValueError(
            "'reload=True' has no effect: run() passes the app instance to "
            "Uvicorn, whose reloader only runs when serving by import string. "
            "For auto-reload, build the app with create_app() and serve it "
            "with an import string (e.g. 'uvicorn mymodule:app --reload')."
        )

    # Normalize root_path once: a trailing slash (e.g. root_path="/tools/") would
    # produce doubled-slash internal URLs like "/tools//add". ASGI convention is
    # no trailing slash; enforce it here so the handlers don't each have to.
    root_path = root_path.rstrip("/")

    uploads_dir, returns_dir = _resolve_dirs(uploads_dir, returns_dir)

    # Boot sweeps are run()-only on purpose: create_app() is built once per
    # worker, and a sweep on every build could delete in-flight uploads of a
    # sibling worker during rolling restarts.
    count = save_file_handler.cleanup_uploads_dir(uploads_dir)
    if count > 0:
        print(f"Cleaned up {count} leftover upload folders from previous run")

    count = return_file_handler.cleanup_returned_files(returns_dir, returns_lifetime)
    if count > 0:
        print(f"Cleaned up {count} expired returned files from previous run")

    app = create_app(
        func,
        app_title=app_title,
        css_vars=css_vars,
        favicon=favicon,
        uploads_dir=uploads_dir,
        max_file_size=max_file_size,
        returns_dir=returns_dir,
        returns_lifetime=returns_lifetime,
        stream_prints=stream_prints,
        fastapi_config=fastapi_config,
    )

    # Standalone reverse-proxy mode: create_app() builds with root_path=""
    # (mounted apps get their prefix from Starlette per request). FastAPI's
    # __call__ injects self.root_path into scope["root_path"] when set, so
    # assigning the attribute here reproduces the previous
    # create_fastapi_app(root_path=...) behavior exactly.
    if root_path:
        app.root_path = root_path

    start_server(app, host, port, uvicorn_kwargs)
