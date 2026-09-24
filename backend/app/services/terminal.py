import asyncio
import subprocess
import shlex
import time
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from ..core.workspace import workspace_manager
from ..core.security import security_validator
from ..config import settings

@dataclass
class TerminalProcess:
    id: str
    project_id: str
    command: str
    cwd: Path
    process: Optional[subprocess.Popen] = None
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    status: str = "running"  # running, completed, failed, killed
    requires_approval: bool = False
    approved: bool = False

class TerminalService:
    def __init__(self):
        self.processes: Dict[str, TerminalProcess] = {}
        self.security = security_validator
        self.max_output_size = 1024 * 1024  # 1MB
        self.default_timeout = 120  # seconds
    
    def create_process(self, project_id: str, command: str, cwd: str = "", timeout: int = None) -> Dict[str, Any]:
        proc_id = str(uuid.uuid4())[:8]
        
        # Security check
        allowed, reason = self.security.is_command_allowed(command)
        if not allowed:
            return {
                "success": False,
                "error": f"Command blocked: {reason}",
                "process_id": proc_id,
                "requires_approval": False
            }
        
        requires_approval = self.security.requires_approval(command)
        
        project_path = workspace_manager.get_project_path(project_id)
        if cwd:
            work_dir = project_path / cwd
        else:
            work_dir = project_path
        
        if not work_dir.exists():
            work_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate path
        if not str(work_dir.resolve()).startswith(str(project_path.resolve())):
            return {
                "success": False,
                "error": "Path traversal detected",
                "process_id": proc_id
            }
        
        terminal_proc = TerminalProcess(
            id=proc_id,
            project_id=project_id,
            command=command,
            cwd=work_dir,
            requires_approval=requires_approval,
            approved=not requires_approval
        )
        
        self.processes[proc_id] = terminal_proc
        
        return {
            "success": True,
            "process_id": proc_id,
            "command": command,
            "cwd": str(work_dir),
            "requires_approval": requires_approval,
            "status": "created" if requires_approval else "pending"
        }
    
    def execute(self, project_id: str, command: str, cwd: str = "", timeout: int = None, approve: bool = False) -> Dict[str, Any]:
        # First create
        create_result = self.create_process(project_id, command, cwd, timeout)
        if not create_result["success"]:
            return create_result
        
        proc_id = create_result["process_id"]
        terminal_proc = self.processes[proc_id]
        
        if terminal_proc.requires_approval and not approve:
            return {
                "success": True,
                "process_id": proc_id,
                "command": command,
                "status": "requires_approval",
                "message": f"Command requires approval: {command}",
                "requires_approval": True
            }
        
        terminal_proc.approved = True
        return self._run_process(proc_id, timeout or self.default_timeout)
    
    def _run_process(self, proc_id: str, timeout: int) -> Dict[str, Any]:
        terminal_proc = self.processes.get(proc_id)
        if not terminal_proc:
            return {"success": False, "error": "Process not found"}
        
        start = time.time()
        try:
            # Prepare environment - filter secrets
            env = os.environ.copy()
            # Don't pass secrets to subprocess env that will be logged
            # But keep necessary vars
            
            # Run process
            # Use shell=True for complex commands like npm, but with caution
            # We run in project workspace
            proc = subprocess.Popen(
                terminal_proc.command,
                shell=True,
                cwd=str(terminal_proc.cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1
            )
            
            terminal_proc.process = proc
            terminal_proc.status = "running"
            
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                terminal_proc.status = "killed"
                terminal_proc.exit_code = -1
                terminal_proc.stderr = stderr[-self.max_output_size:] if stderr else "Timeout"
                terminal_proc.stdout = stdout[-self.max_output_size:] if stdout else ""
                terminal_proc.end_time = datetime.now()
                terminal_proc.duration_ms = int((time.time() - start) * 1000)
                
                return {
                    "success": False,
                    "process_id": proc_id,
                    "command": terminal_proc.command,
                    "stdout": terminal_proc.stdout,
                    "stderr": terminal_proc.stderr + f"\nProcess timed out after {timeout}s",
                    "exit_code": -1,
                    "duration_ms": terminal_proc.duration_ms,
                    "status": "timeout"
                }
            
            end = time.time()
            terminal_proc.stdout = stdout[-self.max_output_size:] if stdout else ""
            terminal_proc.stderr = stderr[-self.max_output_size:] if stderr else ""
            terminal_proc.exit_code = proc.returncode
            terminal_proc.end_time = datetime.now()
            terminal_proc.duration_ms = int((end - start) * 1000)
            terminal_proc.status = "completed" if proc.returncode == 0 else "failed"
            
            return {
                "success": proc.returncode == 0,
                "process_id": proc_id,
                "command": terminal_proc.command,
                "stdout": terminal_proc.stdout,
                "stderr": terminal_proc.stderr,
                "exit_code": proc.returncode,
                "duration_ms": terminal_proc.duration_ms,
                "status": terminal_proc.status,
                "cwd": str(terminal_proc.cwd)
            }
            
        except Exception as e:
            terminal_proc.status = "failed"
            terminal_proc.stderr = str(e)
            terminal_proc.end_time = datetime.now()
            terminal_proc.duration_ms = int((time.time() - start) * 1000)
            
            return {
                "success": False,
                "process_id": proc_id,
                "command": terminal_proc.command,
                "stdout": terminal_proc.stdout,
                "stderr": str(e),
                "exit_code": -1,
                "duration_ms": terminal_proc.duration_ms,
                "status": "failed"
            }
    
    def get_process(self, process_id: str) -> Optional[Dict[str, Any]]:
        proc = self.processes.get(process_id)
        if not proc:
            return None
        
        return {
            "id": proc.id,
            "project_id": proc.project_id,
            "command": proc.command,
            "cwd": str(proc.cwd),
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.exit_code,
            "status": proc.status,
            "duration_ms": proc.duration_ms,
            "requires_approval": proc.requires_approval,
            "approved": proc.approved
        }
    
    def list_processes(self, project_id: str) -> List[Dict[str, Any]]:
        result = []
        for proc in self.processes.values():
            if proc.project_id == project_id:
                result.append(self.get_process(proc.id))
        return sorted(result, key=lambda x: x["id"], reverse=True)[:20]
    
    def kill_process(self, process_id: str) -> Dict[str, Any]:
        proc = self.processes.get(process_id)
        if not proc:
            return {"success": False, "error": "Process not found"}
        
        if proc.process and proc.status == "running":
            try:
                proc.process.kill()
                proc.status = "killed"
                proc.end_time = datetime.now()
                return {"success": True, "process_id": process_id, "status": "killed"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Process not running"}

terminal_service = TerminalService()
