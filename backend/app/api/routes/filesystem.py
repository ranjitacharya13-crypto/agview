from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ...services.filesystem import filesystem_service
from ...services.project_manager import project_manager

router = APIRouter()

class ReadFileRequest(BaseModel):
    path: str

class WriteFileRequest(BaseModel):
    path: str
    content: str
    agent: str = "user"

class CreateDirRequest(BaseModel):
    path: str

class SearchRequest(BaseModel):
    query: str

class MoveRequest(BaseModel):
    src: str
    dest: str

@router.get("/{project_id}/list")
async def list_files(project_id: str, path: str = ""):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = filesystem_service.list_directory(project_id, path)
    return result

@router.get("/{project_id}/tree")
async def get_tree(project_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = filesystem_service.get_tree(project_id)
    return result

@router.post("/{project_id}/read")
async def read_file(project_id: str, req: ReadFileRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = filesystem_service.read_file(project_id, req.path)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "File not found"))
    
    return result

@router.post("/{project_id}/write")
async def write_file(project_id: str, req: WriteFileRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = filesystem_service.write_file(project_id, req.path, req.content, agent=req.agent)
    
    # Track file change
    from ...models.project_state import FileChange
    from datetime import datetime
    import uuid
    
    # Try to get old content
    old_content = None
    try:
        from ...core.workspace import workspace_manager
        # We already handled in service, but track for project memory
        pass
    except:
        pass
    
    # Add to project file changes
    file_change = FileChange(
        path=req.path,
        operation=result.get("operation", "WRITE"),
        agent=req.agent,
        old_content=old_content,
        new_content=req.content[:1000] if len(req.content) > 1000 else req.content,
        reason=f"File {result.get('operation', 'WRITE')} by {req.agent}"
    )
    project.file_changes.append(file_change)
    project_manager.save_project(project)
    
    return result

@router.post("/{project_id}/delete")
async def delete_file(project_id: str, req: ReadFileRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = filesystem_service.delete_file(project_id, req.path)
    return result

@router.post("/{project_id}/mkdir")
async def create_directory(project_id: str, req: CreateDirRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = filesystem_service.create_directory(project_id, req.path)
    return result

@router.post("/{project_id}/search")
async def search_files(project_id: str, req: SearchRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = filesystem_service.search(project_id, req.query)
    return result

@router.post("/{project_id}/move")
async def move_file(project_id: str, req: MoveRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = filesystem_service.move_file(project_id, req.src, req.dest)
    return result

@router.get("/{project_id}/file-history")
async def get_file_history(project_id: str, path: str = None):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    changes = project.file_changes
    if path:
        changes = [c for c in changes if c.path == path]
    
    return {
        "success": True,
        "changes": [c.model_dump(mode='json') for c in changes[-50:]],
        "count": len(changes)
    }
