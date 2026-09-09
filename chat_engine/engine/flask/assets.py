import os

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _read_asset(filename: str) -> str:
    with open(os.path.join(_ASSETS_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()


# Frontend bundle (HTML shell, compiled CSS/JS) lives in ./assets/ as real
# files now, not embedded as Python string literals — read once at import
# time so `from .assets import html_content, css_content, js_content` keeps
# working unchanged for every existing caller in flask/__init__.py.
html_content = _read_asset("index.html")
css_content = _read_asset("index.css")
js_content = _read_asset("index.js")
