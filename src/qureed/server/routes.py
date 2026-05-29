from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from qureed.interface.diagram import DiagramError
from qureed.interface.project import ProjectConfigError
from qureed.interface.runtime import RuntimeService
from qureed.interface.scriptgen import ScriptGenerationError


router = APIRouter()


class DiagramPathRequest(BaseModel):
    path: str


class DiagramSaveRequest(BaseModel):
    path: str
    diagram: dict[str, Any]


class ScriptGenerateRequest(BaseModel):
    diagram_path: str
    output: str | None = None


def get_runtime(request: Request) -> RuntimeService:
    project_root = getattr(request.app.state, "project_root", None)
    return RuntimeService.load_project(project_root)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/project")
async def project(request: Request) -> dict[str, Any]:
    service = get_runtime(request)
    loaded = service.project
    return {
        "name": loaded.name,
        "root": str(loaded.root),
        "config_path": str(loaded.config_path),
        "custom_device_paths": [
            str(path) for path in loaded.custom_device_paths
        ],
        "spec_output_path": str(loaded.spec_output_path),
        "diagrams_path": str(loaded.diagrams_path),
        "scripts_path": str(loaded.scripts_path),
    }


@router.get("/devices")
async def devices(request: Request) -> list[dict[str, Any]]:
    service = get_runtime(request)
    return [
        {
            "id": spec.class_path,
            "class_path": spec.class_path,
            "source": spec.source,
            "category": spec.category,
            "spec_path": str(spec.path),
            "valid": spec.valid,
        }
        for spec in service.list_available_specs()
    ]


@router.get("/specs")
async def specs(request: Request) -> list[dict[str, Any]]:
    service = get_runtime(request)
    return [
        {
            "id": spec.id,
            "class_path": spec.class_path,
            "source": spec.source,
            "category": spec.category,
            "gui_name": spec.gui_name,
            "icon": spec.icon,
            "properties": spec.properties or {},
            "path": str(spec.path),
            "valid": spec.valid,
        }
        for spec in service.list_available_specs()
    ]


@router.post("/diagrams/validate")
async def validate_diagram(
    body: DiagramPathRequest, request: Request
) -> dict[str, Any]:
    service = get_runtime(request)
    try:
        result = service.validate_diagram(body.path)
    except (DiagramError, ProjectConfigError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"valid": result.valid, "errors": list(result.errors)}


@router.get("/diagrams/load")
async def load_diagram(path: str, request: Request) -> dict[str, Any]:
    service = get_runtime(request)
    try:
        result = service.load_diagram(path)
    except (DiagramError, ProjectConfigError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "path": str(result.path),
        "diagram": result.diagram.to_dict(),
    }


@router.post("/diagrams/save")
async def save_diagram(
    body: DiagramSaveRequest, request: Request
) -> dict[str, Any]:
    service = get_runtime(request)
    try:
        result = service.save_diagram_data(body.path, body.diagram)
    except (DiagramError, ProjectConfigError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "path": str(result.path),
        "diagram": result.diagram.to_dict(),
    }


@router.post("/scripts/generate")
async def generate_script(
    body: ScriptGenerateRequest, request: Request
) -> dict[str, Any]:
    service = get_runtime(request)
    try:
        result = service.generate_script(body.diagram_path, body.output)
    except (DiagramError, ProjectConfigError, ScriptGenerationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "path": str(result.path) if result.path is not None else None,
        "content": result.content,
    }
