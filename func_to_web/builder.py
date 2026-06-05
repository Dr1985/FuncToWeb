import json

from jinja2 import Environment, FileSystemLoader
from pytypeinput import ParamMetadata

from .core.constants import TEMPLATES_DIR
from .models import NormalizedInput, FunctionMetadata


# Shared Jinja environment (templates are static → no auto reload)
_jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    auto_reload=False
)


def render_page(
    params: list[ParamMetadata],
    meta: FunctionMetadata,
    app_input: NormalizedInput,
    base_url: str = "",
    prefix: str = "",
    embed: bool = False
) -> str:
    """Render a function page (form + layout).

    `prefix` is the per-request root_path ("" at root, "/tools" when mounted or
    behind a proxy); it is prepended to internal absolute URLs.

    `embed` (from `?__embed=1`) renders the bare form for iframing: no "back to
    index" button (other chrome is stripped client-side).
    """
    # Frontend builds the form from serialized param metadata
    params_json = json.dumps([p.to_dict() for p in params])

    form_html = _jinja_env.get_template("form.html").render(
        title=meta.name,
        description=meta.description,
        action=f"{prefix}{base_url}/submit",
        params_json=params_json,
    )

    # Show a "back to index" button only in multi-function mode, where an
    # index page with at least 2 functions exists. Single-function apps (and
    # 1-item lists, which redirect straight to the function) have no index.
    # Embed mode renders the bare form, so never show it there.
    show_back = not embed and bool(app_input.items) and len(app_input.items) >= 2

    return _jinja_env.get_template("page.html").render(
        page_title=meta.name,
        form_html=form_html,
        css_vars=app_input.css_vars,
        favicon=app_input.favicon_data_uri,
        show_back=show_back,
        prefix=prefix,
    )


def render_index(app_input: NormalizedInput, prefix: str = "") -> str:
    """Render the index page (multi-function mode).

    `prefix` is the per-request root_path, prepended to internal absolute URLs.
    """
    return _jinja_env.get_template("index.html").render(
        page_title=app_input.title,
        items=app_input.items,
        css_vars=app_input.css_vars,
        favicon=app_input.favicon_data_uri,
        prefix=prefix,
    )
