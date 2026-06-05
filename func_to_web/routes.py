import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse as FastAPIFileResponse, JSONResponse
from fastapi.responses import PlainTextResponse, RedirectResponse

from .builder import render_index
from .models import FunctionMetadata, NormalizedInput
from .core.docs import build_doc
from .core.normalization import get_all_functions
from .core.return_file_handler import get_returned_file, maybe_cleanup
from .route_handlers import create_handlers


UUID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


def register_function_routes(
    app: FastAPI,
    meta: FunctionMetadata,
    app_input: NormalizedInput,
    url: str,
    *,
    uploads_dir: Path,
    max_file_size: int | None,
    returns_dir: Path,
    returns_lifetime: int,
    stream_prints: bool,
) -> None:
    """Register routes for a single function."""
    page_handler, submit_handler = create_handlers(
        meta, app_input, base_url=url,
        uploads_dir=uploads_dir, max_file_size=max_file_size,
        returns_dir=returns_dir, returns_lifetime=returns_lifetime, stream_prints=stream_prints,
    )

    app.get(url, response_class=HTMLResponse)(page_handler)
    app.post(f"{url}/submit")(submit_handler)


def register_navigation_routes(
    app: FastAPI,
    nav_items: list,
    app_input: NormalizedInput,
    *,
    uploads_dir: Path,
    max_file_size: int | None,
    returns_dir: Path,
    returns_lifetime: int,
    stream_prints: bool,
) -> None:
    """Recursively register routes for all navigation items."""
    # Resolve all functions once, then match them by slug.
    all_functions = get_all_functions(app_input.items)

    for item in nav_items:
        if item["type"] == "function":
            meta = next((m for m in all_functions if m.slug == item["slug"]), None)
            if meta:
                register_function_routes(
                    app, meta, app_input, item["url"],
                    uploads_dir=uploads_dir, max_file_size=max_file_size,
                    returns_dir=returns_dir, returns_lifetime=returns_lifetime, stream_prints=stream_prints,
                )
        else:
            register_navigation_routes(
                app, item["children"], app_input,
                uploads_dir=uploads_dir, max_file_size=max_file_size,
                returns_dir=returns_dir, returns_lifetime=returns_lifetime, stream_prints=stream_prints,
            )


def setup_multi_items(
    app: FastAPI,
    app_input: NormalizedInput,
    *,
    uploads_dir: Path,
    max_file_size: int | None,
    returns_dir: Path,
    returns_lifetime: int,
    stream_prints: bool,
) -> None:

    top_level_functions = [item for item in app_input.navigation_data if item["type"] == "function"]

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        prefix = request.scope.get("root_path", "")
        if len(top_level_functions) == 1:
            return RedirectResponse(url=f"{prefix}{top_level_functions[0]['url']}")
        return render_index(app_input, prefix=prefix)

    register_navigation_routes(
        app, app_input.navigation_data, app_input,
        uploads_dir=uploads_dir, max_file_size=max_file_size,
        returns_dir=returns_dir, returns_lifetime=returns_lifetime, stream_prints=stream_prints,
    )


def setup_single_function(
    app: FastAPI,
    app_input: NormalizedInput,
    *,
    uploads_dir: Path,
    max_file_size: int | None,
    returns_dir: Path,
    returns_lifetime: int,
    stream_prints: bool,
) -> None:
    """Set up routes for single-function mode."""
    meta = app_input.single_function

    page_handler, submit_handler = create_handlers(
        meta, app_input, base_url="",
        uploads_dir=uploads_dir, max_file_size=max_file_size,
        returns_dir=returns_dir, returns_lifetime=returns_lifetime, stream_prints=stream_prints,
    )

    app.get("/", response_class=HTMLResponse)(page_handler)
    app.post("/submit")(submit_handler)


def setup_download_route(app: FastAPI, returns_dir: Path, returns_lifetime: int) -> None:
    """Register the file download route."""

    @app.get("/download/{file_id}")
    async def download_file(file_id: str):
        # Reject invalid IDs before touching the file store.
        if not UUID_PATTERN.match(file_id):
            return JSONResponse({"error": "Invalid file ID"}, status_code=400)

        # Opportunistic, throttled cleanup of expired files on download activity.
        maybe_cleanup(returns_dir, returns_lifetime)

        file_info = get_returned_file(file_id, returns_dir)
        if not file_info:
            return JSONResponse({"error": "File not found or expired"}, status_code=404)

        return FastAPIFileResponse(
            path=file_info["path"],
            filename=file_info["filename"],
            media_type="application/octet-stream",
        )

def setup_doc_route(app: FastAPI, app_input: NormalizedInput) -> None:
    @app.get("/doc", response_class=PlainTextResponse)
    async def doc():
        return build_doc(app_input)
