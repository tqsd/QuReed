from __future__ import annotations

import webbrowser

import uvicorn

from qureed.server.app import create_app


def run_gui(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    project_root: str | None = None,
    open_browser: bool = False,
) -> None:
    url = f"http://{host}:{port}"
    print(f"QuReed GUI: {url}")
    if open_browser:
        webbrowser.open(url)
    uvicorn.run(
        create_app(project_root, serve_frontend=True),
        host=host,
        port=port,
    )
