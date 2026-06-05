from typing import Any, Callable
from pathlib import Path

from .models import FunctionMetadata, NormalizedInput
from .utils import encode_favicon_to_base64, validate_css_vars


def normalize_input(
    user_input: Callable[..., Any] | FunctionMetadata | list,
    app_title: str | None = None,
    css_vars: dict[str, str] | None = None,
    favicon: str | Path | None = None,
    default_title: str = "Tools"
) -> NormalizedInput:
    """Normalize user input into the internal app config.

    A list is multi-function mode; anything else is a single function.
    """
    validate_css_vars(css_vars)
    favicon_data_uri = encode_favicon_to_base64(favicon) if favicon else None

    if isinstance(user_input, list):
        return NormalizedInput(
            single_function=None,
            items=normalize_items(user_input),
            title=app_title if app_title is not None else default_title,
            css_vars=css_vars,
            favicon_data_uri=favicon_data_uri,
        )

    single = normalize_function(user_input)
    return NormalizedInput(
        single_function=single,
        items=None,
        title=app_title if app_title is not None else single.name,
        css_vars=css_vars,
        favicon_data_uri=favicon_data_uri,
    )


def normalize_function(
    func_or_meta: Callable[..., Any] | FunctionMetadata
) -> FunctionMetadata:
    """Normalize a function-like input to FunctionMetadata."""
    if isinstance(func_or_meta, FunctionMetadata):
        return func_or_meta

    return FunctionMetadata(function=func_or_meta)


def normalize_items(items: list) -> list:
    """Normalize a flat list of function inputs to FunctionMetadata.

    Rejects duplicate slugs, which would map two functions to the same URL.
    """
    if not isinstance(items, list):
        raise TypeError(f"Items must be a list, got {type(items).__name__}")

    normalized = [normalize_function(item) for item in items]

    if not normalized:
        raise ValueError("Items list cannot be empty")

    seen = set()
    for meta in normalized:
        if meta.slug in seen:
            raise ValueError(
                f"Duplicate URL '/{meta.slug}' detected. Function '{meta.name}' "
                f"conflicts with another function at the same path."
            )
        seen.add(meta.slug)

    return normalized
