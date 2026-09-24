from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ...services.terminal import terminal_service
from ...services.project_manager import project_manager
from ...services.event_bus import event_bus
from ...models.events import EventType

router = APIRouter()

class TerminalRequest(BaseModel):
    command: str
    cwd: str = ""
    timeout: int = 120
    approve: bool = False

@router.post("/{project_id}/execute")
async def execute_command(project_id: str, req: TerminalRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    event_bus.emit(
        project_id=project_id,
        event_type=EventType.COMMAND_STARTED,
        message=f"Executing: {req.command}",
        data={"command": req.command, "cwd": req.cwd}
    )
    
    result = terminal_service.execute(
        project_id=project_id,
        command=req.command,
        cwd=req.cwd,
        timeout=req.timeout,
        approve=req.approve
    )
    
    if result.get("requires_approval"):
        event_bus.emit(
            project_id=project_id,
            event_type=EventType.COMMAND_FAILED,
            message=f"Command requires approval: {req.command}",
            data=result
        )
    elif result.get("success"):
        event_bus.emit(
            project_id=project_id,
            event_type=EventType.COMMAND_COMPLETED,
            message=f"Command completed: {req.command}",
            data=result
        )
    else:
        event_bus.emit(
            project_id=project_id,
            event_type=EventType.COMMAND_FAILED,
            message=f"Command failed: {req.command}",
            data=result
        )
    
    return result

@router.get("/{project_id}/processes")
async def list_processes(project_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    processes = terminal_service.list_processes(project_id)
    return {"success": True, "processes": processes}

@router.get("/{project_id}/process/{process_id}")
async def get_process(project_id: str, process_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    proc = terminal_service.get_process(process_id)
    if not proc:
        raise HTTPException(status_code=404, detail="Process not found")
    
    return {"success": True, "process": proc}

@router.post("/{project_id}/process/{process_id}/kill")
async def kill_process(project_id: str, process_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = terminal_service.kill_process(process_id)
    return result

@router.post("/{project_id}/install")
async def install_dependency(project_id: str, req: TerminalRequest):
    # Special handling for npm install
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    command = req.command
    if not command.startswith("npm") and not command.startswith("pip") and not command.startswith("yarn"):
        command = f"npm install {command}" if command else "npm install"
    
    result = terminal_service.execute(project_id, command, req.cwd, req.timeout, req.approve)
    return result
