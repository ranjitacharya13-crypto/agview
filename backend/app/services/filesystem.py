from pathlib import Path
from typing import List, Dict, Any
from ..core.workspace import workspace_manager
from ..core.security import security_validator

class FilesystemService:
    def __init__(self):
        self.workspace = workspace_manager
        self.security = security_validator
    
    def list_directory(self, project_id: str, path: str = "") -> Dict[str, Any]:
        try:
            files = self.workspace.list_files(project_id, path)
            return {"success": True, "files": files, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e), "files": []}
    
    def get_tree(self, project_id: str) -> Dict[str, Any]:
        try:
            tree = self.workspace.recursive_tree(project_id)
            return {"success": True, "tree": tree}
        except Exception as e:
            return {"success": False, "error": str(e), "tree": None}
    
    def read_file(self, project_id: str, file_path: str) -> Dict[str, Any]:
        try:
            content = self.workspace.read_file(project_id, file_path)
            # Check for secrets
            secrets = self.security.detect_secrets(content)
            return {
                "success": True,
                "path": file_path,
                "content": content,
                "secrets_detected": len(secrets) > 0,
                "operation": "READ"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "path": file_path}
    
    def write_file(self, project_id: str, file_path: str, content: str, agent: str = "user", decision_id: str = None) -> Dict[str, Any]:
        try:
            # Check for secrets before writing
            secrets = self.security.detect_secrets(content)
            if secrets:
                # Still allow but warn
                pass
            
            old_content = None
            try:
                old_content = self.workspace.read_file(project_id, file_path)
                operation = "EDIT"
            except:
                operation = "CREATE"
            
            self.workspace.write_file(project_id, file_path, content)
            
            # Track file change in project
            try:
                from .project_manager import project_manager
                from ..models.project_state import FileChange
                project = project_manager.get_project(project_id)
                if project:
                    file_change = FileChange(
                        path=file_path,
                        operation=operation,
                        agent=agent,
                        decision_id=decision_id,
                        old_content=old_content[:1000] if old_content and len(old_content) > 1000 else old_content,
                        new_content=content[:1000] if len(content) > 1000 else content,
                        reason=f"{operation} by {agent}"
                    )
                    project.file_changes.append(file_change)
                    project_manager.save_project(project)
            except Exception as e:
                print(f"Failed to track file change: {e}")
            
            return {
                "success": True,
                "path": file_path,
                "operation": operation,
                "agent": agent,
                "decision_id": decision_id,
                "secrets_warning": secrets
            }
        except Exception as e:
            return {"success": False, "error": str(e), "path": file_path, "operation": "WRITE"}
    
    def delete_file(self, project_id: str, file_path: str, agent: str = "user") -> Dict[str, Any]:
        try:
            success = self.workspace.delete_file(project_id, file_path)
            return {
                "success": success,
                "path": file_path,
                "operation": "DELETE",
                "agent": agent
            }
        except Exception as e:
            return {"success": False, "error": str(e), "path": file_path}
    
    def create_directory(self, project_id: str, dir_path: str) -> Dict[str, Any]:
        try:
            self.workspace.create_directory(project_id, dir_path)
            return {"success": True, "path": dir_path, "operation": "CREATE_DIR"}
        except Exception as e:
            return {"success": False, "error": str(e), "path": dir_path}
    
    def search(self, project_id: str, query: str) -> Dict[str, Any]:
        try:
            results = self.workspace.search_files(project_id, query)
            return {"success": True, "query": query, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e), "query": query, "results": []}
    
    def move_file(self, project_id: str, src: str, dest: str) -> Dict[str, Any]:
        try:
            project_path = self.workspace.get_project_path(project_id)
            src_path = project_path / src
            dest_path = project_path / dest
            
            if not str(src_path.resolve()).startswith(str(project_path.resolve())):
                raise ValueError("Path traversal detected")
            if not str(dest_path.resolve()).startswith(str(project_path.resolve())):
                raise ValueError("Path traversal detected")
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            src_path.rename(dest_path)
            
            return {"success": True, "src": src, "dest": dest, "operation": "MOVE"}
        except Exception as e:
            return {"success": False, "error": str(e)}

filesystem_service = FilesystemService()
