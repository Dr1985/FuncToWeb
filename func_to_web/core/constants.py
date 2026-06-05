from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
INTERNAL_STATIC_DIR = BASE_DIR / "internal_static"

UVICORN_DEFAULTS = {
    "limit_concurrency": 100,
    "limit_max_requests": 10000,
    "timeout_keep_alive": 30,
}
