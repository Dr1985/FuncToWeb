from typing import Any, Callable
from pathlib import Path

from ..models import FunctionMetadata, NormalizedInput
from .utils import detect_input_type, encode_favicon_to_base64, validate_css_vars


def normalize_input(
    user_input: Callable[..., Any] | FunctionMetadata | list,
    app_title: str | None = None,
    css_vars: dict[str, str] | None = None,
    favicon: str | Path | None = None,
    default_title: str = "Tools"
) -> NormalizedInput:
    """Normalize user input into the internal app config."""
    validate_css_vars(css_vars)

    input_type = detect_input_type(user_input)
    title = app_title if app_title is not None else default_title

    favicon_data_uri = None
    if favicon:
        favicon_data_uri = encode_favicon_to_base64(favicon)

    config = {
        "single_function": None,
        "items": None,
        "title": title,
        "css_vars": css_vars,
        "favicon_data_uri": favicon_data_uri,
    }

    if input_type == "single":
        config["single_function"] = normalize_function(user_input)
        if app_title is None:
            config["title"] = config["single_function"].name
    else:
        config["items"] = normalize_items(user_input)

    return NormalizedInput(**config)


def normalize_function(
    func_or_meta: Callable[..., Any] | FunctionMetadata
) -> FunctionMetadata:
    """Normalize a function-like input to FunctionMetadata."""
    if isinstance(func_or_meta, FunctionMetadata):
        return func_or_meta

    return FunctionMetadata(function=func_or_meta)


def normalize_items(items: list) -> list:
    """Normalize a flat list of function inputs to FunctionMetadata."""
    if not isinstance(items, list):
        raise TypeError(f"Items must be a list, got {type(items).__name__}")

    normalized = [normalize_function(item) for item in items]

    if not normalized:
        raise ValueError("Items list cannot be empty")

    return normalized


def build_navigation_structure(items: list) -> list[dict]:
    """Build the navigation list and validate route uniqueness."""
    seen_urls = set()
    nav_items = []

    for meta in items:
        url = f"/{meta.slug}"

        if url in seen_urls:
            raise ValueError(
                f"Duplicate URL '{url}' detected. "
                f"Function '{meta.name}' conflicts with another function at the same path."
            )
        seen_urls.add(url)

        nav_items.append({
            "name": meta.name,
            "slug": meta.slug,
            "description": meta.description,
            "url": url,
        })

    return nav_items
