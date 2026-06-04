# Server Configuration

FuncToWeb runs a FastAPI/Uvicorn server. The recommended setup is binding to `127.0.0.1` and letting Nginx act as reverse proxy

## Basic

```python
from func_to_web import run

run(my_function, host="127.0.0.1", port=8000)
```

## All Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `host` | `"0.0.0.0"` | Server host |
| `port` | `8000` | Server port |
| `app_title` | auto | Page title |
| `css_vars` | `None` | CSS variable overrides |
| `favicon` | `None` | Path to favicon file |
| `uploads_dir` | OS temp dir | Uploaded files directory (defaults to `<temp>/func_to_web_uploads`) |
| `max_file_size` | `None` | Max upload size in bytes |
| `returns_dir` | OS temp dir | Returned files directory (defaults to `<temp>/func_to_web_returned_files`) |
| `returns_lifetime` | `3600` | Seconds before returned files are deleted |
| `stream_prints` | `True` | Stream `print()` to browser |
| `root_path` | `""` | URL prefix for reverse proxy |
| `fastapi_config` | `None` | Extra FastAPI options |
| `front_dir` | `None` | Directory mounted at `/front` (with `html=True` for SPA-style routing) |
| `assets_dir` | `None` | Directory mounted at `/assets` for static files |
| `**uvicorn_kwargs` | — | Any Uvicorn option |

Any option supported by Uvicorn or FastAPI can be passed through — `fastapi_config` for FastAPI constructor kwargs, and `**uvicorn_kwargs` for everything else.

## Common Setups

**Localhost only:**
```python
run(my_function, host="127.0.0.1")
```

**Custom port:**
```python
run(my_function, port=5000)
```

**Reverse proxy with path prefix:**
```python
run(my_function, root_path="/tools/my-app")
```

Set `root_path` to the prefix your proxy serves under and the whole UI works: every internal URL (styles/scripts, form submit, navigation, downloads, `ActionTable`) is derived per request from `root_path`, so nothing points at the domain root. A trailing slash is fine — it's normalized. (Mounting a FuncToWeb app inside a larger app via `create_app()` is coming next.)

**Custom frontend + static assets:**
```python
run(
    my_function,
    front_dir="./my-site",      # served at /front (SPA-style routing)
    assets_dir="./assets",      # served at /assets (images, fonts, downloads)
)
```

`front_dir` is mounted with `html=True`, so unknown paths fall back to `index.html` — drop a static site or a built React/Vue/Svelte bundle next to your Python functions and the same FuncToWeb process serves both.

## Nginx + Supervisor

The recommended setup: Supervisor keeps the process alive, Nginx handles SSL termination and proxies to FuncToWeb on localhost. Set `root_path` to match the Nginx location, and disable proxy buffering if you use `stream_prints=True`.

### Protecting the app

FuncToWeb has no built-in authentication. To restrict access, put it behind a reverse proxy with auth. With Nginx, `auth_basic` is the simplest option:

```nginx
location / {
    auth_basic           "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;   # created with `htpasswd`
    proxy_pass           http://127.0.0.1:8000;
}
```

## Production Example

```python
import os
from func_to_web import run

run(
    my_functions,
    host="127.0.0.1",
    port=8000,
)
```
