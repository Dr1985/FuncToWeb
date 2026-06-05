from importlib.metadata import PackageNotFoundError, version

from .types import *
from .run import run, create_app
from .models import FunctionMetadata
from .utils import list_css_variables


try:
    # Single source of truth: read the installed package version so it can never
    # drift from pyproject.toml. Falls back when running from an uninstalled checkout.
    __version__ = version("func-to-web")
except PackageNotFoundError:
    __version__ = "unknown"
