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
| `fastapi_config` | `None` | Extra FastAPI options |
| `**uvicorn_kwargs` | — | Any Uvicorn option (e.g. `root_path` for a reverse proxy) |

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

`root_path` is passed straight through to Uvicorn (via `**uvicorn_kwargs`), which injects it into the ASGI scope. Set it to the prefix your proxy serves under and the whole UI works: every internal URL (styles/scripts, form submit, navigation, downloads) is derived per request from `root_path`, so nothing points at the domain root. Use no trailing slash (`/tools/my-app`, not `/tools/my-app/`) — a trailing slash produces doubled-slash internal URLs.

**Embedding in a larger FastAPI app:**
```python
from fastapi import FastAPI
from func_to_web import create_app

host = FastAPI()
host.mount("/tools", create_app([add, multiply]))
```

`create_app()` accepts the same configuration as `run()` except the server
options (`host`, `port`, `**uvicorn_kwargs`). The mount prefix is
picked up per request automatically. Serving by import string also enables
`uvicorn mymodule:app --workers 4` and `--reload`. Note that the startup
cleanup of leftover uploads only runs in `run()` — see the changelog.

**Custom frontend / SPA next to your functions:**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from func_to_web import create_app

host = FastAPI()
host.mount("/tools", create_app(my_functions))
host.mount("/", StaticFiles(directory="dist", html=True))
```

Your SPA lives at the root, the auto-generated tools under `/tools`, one
process serves both. `html=True` gives SPA-style routing (unknown paths fall
back to `index.html`).

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
