"""Serve a static site / SPA next to your functions.

The SPA lives at the root, the auto-generated tools under /tools,
one process serves both.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from func_to_web import create_app


def greet(name: str):
    return f"Hello, {name}!"


app = FastAPI()
app.mount("/tools", create_app(greet))
app.mount("/", StaticFiles(directory="./site", html=True))

# Or by import string: uvicorn 04_static_frontend:app --reload
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
