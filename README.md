# Func To Web 1.5.0

[![PyPI version](https://img.shields.io/pypi/v/func-to-web.svg)](https://pypi.org/project/func-to-web/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Type hints → Web UI. Turn Python functions into web apps — standalone or mounted inside yours.

![func-to-web Demo](/docs/images/functoweb.jpg)

One typed Python function → form + iframe + HTTP endpoint, simultaneously. It's a library, not a framework: it composes with what you already have.

- **Standalone** — `run(func)`. Internal tools, admin panels, scripts. The auto-generated UI is the app.
- **Mounted** — `create_app(funcs)` returns a plain FastAPI app. Mount it under any prefix of your existing app; every URL adapts automatically.
- **Embedded** — drop forms into existing sites via `<iframe>` with URL prefill. "Export to PDF" buttons, CSV importers, modal editors.

Validation, file uploads, SSE streaming, downloads, custom widgets and outputs via return types and Annotated metadata — all built-in. Auto-generated API docs at /doc for scripts and AI agents: write a function, get a UI and an API for free.

## Quick start

```bash
pip install func-to-web
```

```python
from func_to_web import run

def divide(a: float, b: float):
    return a / b

run(divide)
```

![divide demo](/docs/images/quick.jpg)

Open `http://127.0.0.1:8000`. Done.

## Or mount it inside your FastAPI app

```python
from fastapi import FastAPI
from func_to_web import create_app

def add(a: int, b: int):
    return a + b

host = FastAPI()
host.mount("/tools", create_app(add))
```

```bash
uvicorn app:host
```

Open `http://127.0.0.1:8000/tools/`. Forms, validation, downloads, navigation — everything works under the prefix, zero configuration.

**Full docs with examples and screenshots:** [`docs/`](docs/index.md) — one page per feature, browsable right here on GitHub.

## Inputs

| Type | Widget | Docs |
|------|--------|------|
| `int`, `float` | Number / slider | [→](docs/inputs/numeric.md) |
| `str`, `Email` | Text / textarea / password | [→](docs/inputs/string.md) |
| `bool` | Toggle | [→](docs/inputs/boolean.md) |
| `date`, `time` | Pickers | [→](docs/inputs/datetime.md) |
| `Color` | Hex picker | [→](docs/inputs/color.md) |
| `File`, `ImageFile`, `VideoFile`, ... | Upload | [→](docs/inputs/files.md) |
| `Literal`, `Enum`, `Dropdown(func)` | Select | [→](docs/inputs/dropdown.md) |
| `list[T]` | Dynamic list | [→](docs/inputs/lists.md) |
| `T \| None` | Toggle + input | [→](docs/inputs/optional.md) |
| `Params` | Reusable groups | [→](docs/inputs/params.md) |
| `Annotated[T, ...]` | Type Composition, Constraints, labels, sliders | [→](docs/inputs/composition.md) |

## Outputs

| Return type | Rendered as | Docs |
|-------------|-------------|------|
| `str`, `int`, `float`, `None` | Text + copy button | [→](docs/outputs/index.md#text) |
| `PIL Image`, `Matplotlib Figure` | Inline image | [→](docs/outputs/index.md#images) |
| `FileResponse` | Download button | [→](docs/outputs/index.md#file-downloads) |
| `DataFrame`, `list[dict]`, ... | Table| [→](docs/outputs/index.md#tables) |
| `tuple` / `list` | Multiple outputs | [→](docs/outputs/index.md#multiple-outputs) |
| `print()` | Streamed live | [→](docs/outputs/index.md#print-output) |

## Features

- **`create_app()`** — get a mountable FastAPI app, serve by import string (workers, reload) — [docs](docs/features/configuration.md)
- **Multiple functions** with index page and navigation — [docs](docs/features/multiple-functions.md)
- **URL prefill** — open forms with values from query params — [docs](docs/features/url-prefill.md)
- **Embed mode** — drop any form into your site via `?__embed=1` — [docs](docs/features/embed.md)
- **Auto-generated API docs** at `/doc` for scripts and AI agents — [docs](docs/features/api-docs.md)
- **Server config** — host, port, reverse proxy — [docs](docs/features/configuration.md)

## Examples

**File transfer**

```python
from func_to_web import run, File
import shutil, os

downloads = os.path.expanduser("~/Downloads")

def upload_files(files: list[File]):
    for f in files:
        shutil.move(f, downloads)
    return "Done."

run(upload_files)
```

**QR code generator**

```python
import qrcode
from func_to_web import run

def make_qr(text: str):
    return qrcode.make(text).get_image()

run(make_qr)
```

**Admin panel**

```python
import subprocess
from typing import Literal
from func_to_web import run

def restart_service(service: Literal['nginx', 'gunicorn', 'celery']):
    subprocess.run(["sudo", "supervisorctl", "restart", service], check=True)
    return f"{service} restarted."

# Deploy sensitive tools behind a reverse proxy with auth (e.g. Nginx
# basic auth) — see docs/features/configuration.md.
run(restart_service)
```

More in [`examples/`](examples/).

## Install

```bash
pip install func-to-web                                     # stable
pip install git+https://github.com/offerrall/FuncToWeb.git  # latest
```

**Requirements:** Python 3.10+. Core deps installed automatically; Pillow, Matplotlib, Pandas, NumPy and Polars are optional.

## Stability

FuncToWeb is in its fast-iteration phase, and that's deliberate. Until 2.0.0
the priority is getting the design right, not preserving it: features that
turn out to have a better home in another layer get removed, APIs get
reshaped, and minor releases can break things. Every breaking change is
explicit — documented in the [CHANGELOG](CHANGELOG.md) with the reasoning and
the migration path, never silent.

If you depend on it today, **pin your version** (`func-to-web==1.5.0`) and
read the changelog before upgrading.

**The 2.0.0 commitment:** from 2.0.0 onwards, FuncToWeb adopts semantic
versioning for real — breaking changes only in major releases, with
deprecation warnings beforehand. The churn now is what buys a stable, small
API later.

Built on [pytypeinput](https://github.com/offerrall/pytypeinput) and [pytypeinputweb](https://github.com/offerrall/pytypeinputweb), usable standalone for CLIs, Qt apps, etc.

Feedback, issues and contributions welcome — they keep the project moving.

[MIT License](LICENSE) · Made by [Beltrán Offerrall](https://github.com/offerrall)