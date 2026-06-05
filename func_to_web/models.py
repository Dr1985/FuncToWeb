from typing import Callable, Any
from dataclasses import dataclass

from .utils import slugify, validate_slug


@dataclass
class FunctionMetadata:
    """Metadata for exposing a callable as a web page.

    Missing values are derived in `__post_init__`.
    """
    function: Callable[..., Any]
    name: str | None = None
    slug: str | None = None
    description: str | None = None

    def __post_init__(self):
        if not callable(self.function):
            raise TypeError(
                f"function must be callable, got {type(self.function).__name__}"
            )

        if self.name is not None and self.name.strip() == "":
            self.name = None

        if self.name is None:
            func_name = getattr(self.function, "__name__", None)
            if func_name is None:
                func_name = type(self.function).__name__
            self.name = func_name.replace("_", " ").capitalize()

        if self.slug is None:
            self.slug = slugify(self.name)

        validate_slug(self.slug)

        if self.description is None:
            self.description = (
                self.function.__doc__.strip()
                if self.function.__doc__
                else ""
            )

@dataclass
class NormalizedInput:
    """Normalized internal input for `run()` / `create_app()`.

    Exactly one of `single_function` or `items` (a list of FunctionMetadata)
    must be set. `items` is the single source of truth for multi-function mode:
    each function's URL is `/<slug>`.
    """
    single_function: FunctionMetadata | None
    items: list | None
    title: str
    css_vars: dict[str, str] | None
    favicon_data_uri: str | None

    def __post_init__(self):
        if sum(x is not None for x in [self.single_function, self.items]) != 1:
            raise ValueError(
                "Exactly one of single_function or items must be provided."
            )
