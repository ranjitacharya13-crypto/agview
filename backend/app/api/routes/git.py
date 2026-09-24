from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from ...services.project_manager import project_manager
from pathlib import Path
import subprocess

router = APIRouter()

class GitRequest(BaseModel):
    command: str
    args: str = ""

@router.get("/{project_id}/status")
async def git_status(project_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        from ...core.workspace import workspace_manager
        project_path = workspace_manager.get_project_path(project_id)
        
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # If not a git repo, init
        if result.returncode != 0 and "not a git repository" in result.stderr:
            subprocess.run(["git", "init"], cwd=str(project_path), capture_output=True, timeout=10)
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=10
            )
        
        return {
            "success": True,
            "status": result.stdout,
            "is_repo": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "is_repo": False
        }

@router.get("/{project_id}/diff")
async def git_diff(project_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        from ...core.workspace import workspace_manager
        project_path = workspace_manager.get_project_path(project_id)
        
        result = subprocess.run(
            ["git", "diff"],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            "success": True,
            "diff": result.stdout[:10000]  # Limit
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/{project_id}/commit")
async def git_commit(project_id: str, req: GitRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        from ...core.workspace import workspace_manager
        project_path = workspace_manager.get_project_path(project_id)
        
        # Add all
        subprocess.run(["git", "add", "."], cwd=str(project_path), capture_output=True, timeout=10)
        
        # Commit
        message = req.args or "Update via Agentic IDE"
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/{project_id}/branch")
async def git_branch(project_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        from ...core.workspace import workspace_manager
        project_path = workspace_manager.get_project_path(project_id)
        
        result = subprocess.run(
            ["git", "branch"],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            "success": True,
            "branches": result.stdout
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/{project_id}/log")
async def git_log(project_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Return file change history as git-like log
    changes = project.file_changes[-20:]
    
    return {
        "success": True,
        "log": [
            {
                "id": c.id,
                "timestamp": c.timestamp.isoformat(),
                "path": c.path,
                "operation": c.operation,
                "agent": c.agent,
                "reason": c.reason
            }
            for c in changes
        ]
    }
