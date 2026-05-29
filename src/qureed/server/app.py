from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response

from qureed.server.routes import router


def create_app(
    project_root: str | Path | None = None,
    *,
    serve_frontend: bool = True,
) -> FastAPI:
    app = FastAPI(title="QuReed Local Server")
    app.state.project_root = (
        Path(project_root).expanduser().resolve()
        if project_root is not None
        else None
    )
    app.include_router(router)
    if serve_frontend:
        mount_frontend(app)
    return app


def mount_frontend(app: FastAPI) -> None:
    static_dir = frontend_static_dir()
    index_path = static_dir / "index.html"
    if not index_path.exists():
        return

    @app.get("/assets/{path:path}", include_in_schema=False)
    async def frontend_asset(path: str) -> Response:
        asset_path = safe_static_path(static_dir / "assets", path)
        if not asset_path.is_file():
            raise HTTPException(status_code=404, detail="Asset not found")
        media_type = mimetypes.guess_type(asset_path.name)[0]
        return Response(
            asset_path.read_bytes(),
            media_type=media_type or "application/octet-stream",
        )

    @app.get("/", include_in_schema=False)
    async def frontend_index() -> HTMLResponse:
        return HTMLResponse(index_path.read_text(encoding="utf-8"))

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend_fallback(path: str) -> HTMLResponse:
        return HTMLResponse(index_path.read_text(encoding="utf-8"))


def frontend_static_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "gui" / "static"


def safe_static_path(root: Path, path: str) -> Path:
    resolved_root = root.resolve()
    resolved_path = (resolved_root / path).resolve()
    if resolved_root != resolved_path and resolved_root not in (
        resolved_path.parents
    ):
        raise HTTPException(status_code=404, detail="Asset not found")
    return resolved_path


app = create_app()
