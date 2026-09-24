from pathlib import Path
from typing import List, Dict, Any, Optional
import os
import json
import shutil
from ..config import settings

class WorkspaceManager:
    def __init__(self):
        self.root = settings.workspace_root
        self.root.mkdir(parents=True, exist_ok=True)
    
    def get_project_path(self, project_id: str) -> Path:
        return self.root / project_id
    
    def create_project_workspace(self, project_id: str, name: str) -> Path:
        project_path = self.get_project_path(project_id)
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create standard structure
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "public").mkdir(exist_ok=True)
        (project_path / "backend").mkdir(exist_ok=True)
        (project_path / "docs").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        (project_path / "presentations").mkdir(exist_ok=True)
        
        # Create README
        readme_path = project_path / "README.md"
        if not readme_path.exists():
            readme_path.write_text(f"# {name}\n\nProject ID: {project_id}\n")
        
        # Create .env.example
        env_example = project_path / ".env.example"
        if not env_example.exists():
            env_example.write_text("# Environment variables\nNODE_ENV=development\n")
        
        return project_path
    
    def list_files(self, project_id: str, subpath: str = "") -> List[Dict[str, Any]]:
        project_path = self.get_project_path(project_id)
        target = project_path / subpath if subpath else project_path
        
        if not target.exists():
            return []
        
        result = []
        try:
            for item in sorted(target.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                # Skip hidden and node_modules for performance
                if item.name.startswith('.') and item.name not in ['.env.example', '.gitignore']:
                    continue
                if item.name in ['node_modules', '__pycache__', '.git']:
                    result.append({
                        "name": item.name,
                        "path": str(item.relative_to(project_path)),
                        "type": "directory" if item.is_dir() else "file",
                        "size": 0,
                        "is_hidden": True
                    })
                    continue
                
                stat = item.stat()
                result.append({
                    "name": item.name,
                    "path": str(item.relative_to(project_path)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": stat.st_mtime,
                    "is_hidden": item.name.startswith('.')
                })
        except Exception as e:
            print(f"Error listing files: {e}")
        
        return result
    
    def recursive_tree(self, project_id: str, max_depth: int = 4) -> Dict[str, Any]:
        project_path = self.get_project_path(project_id)
        
        def build_tree(path: Path, depth: int) -> Dict[str, Any]:
            if depth > max_depth:
                return None
            
            name = path.name
            if name in ['node_modules', '.git', '__pycache__', 'dist', 'build']:
                return {
                    "name": name,
                    "path": str(path.relative_to(project_path)),
                    "type": "directory",
                    "children": [],
                    "collapsed": True
                }
            
            if path.is_file():
                return {
                    "name": name,
                    "path": str(path.relative_to(project_path)),
                    "type": "file",
                    "size": path.stat().st_size
                }
            else:
                children = []
                try:
                    for child in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                        if child.name.startswith('.') and child.name not in ['.env.example', '.gitignore']:
                            continue
                        subtree = build_tree(child, depth+1)
                        if subtree:
                            children.append(subtree)
                except:
                    pass
                
                return {
                    "name": name,
                    "path": str(path.relative_to(project_path)) if path != project_path else "",
                    "type": "directory",
                    "children": children
                }
        
        return build_tree(project_path, 0)
    
    def read_file(self, project_id: str, file_path: str) -> str:
        project_path = self.get_project_path(project_id)
        full_path = project_path / file_path
        
        # Security check
        if not str(full_path.resolve()).startswith(str(project_path.resolve())):
            raise ValueError("Path traversal detected")
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if full_path.is_dir():
            raise ValueError(f"Path is directory: {file_path}")
        
        # Limit file size to 1MB for reading
        if full_path.stat().st_size > 1024*1024:
            raise ValueError("File too large")
        
        return full_path.read_text(encoding='utf-8', errors='ignore')
    
    def write_file(self, project_id: str, file_path: str, content: str) -> Path:
        project_path = self.get_project_path(project_id)
        full_path = project_path / file_path
        
        if not str(full_path.resolve()).startswith(str(project_path.resolve())):
            raise ValueError("Path traversal detected")
        
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        return full_path
    
    def delete_file(self, project_id: str, file_path: str) -> bool:
        project_path = self.get_project_path(project_id)
        full_path = project_path / file_path
        
        if not str(full_path.resolve()).startswith(str(project_path.resolve())):
            raise ValueError("Path traversal detected")
        
        if not full_path.exists():
            return False
        
        if full_path.is_dir():
            shutil.rmtree(full_path)
        else:
            full_path.unlink()
        return True
    
    def create_directory(self, project_id: str, dir_path: str) -> Path:
        project_path = self.get_project_path(project_id)
        full_path = project_path / dir_path
        
        if not str(full_path.resolve()).startswith(str(project_path.resolve())):
            raise ValueError("Path traversal detected")
        
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path
    
    def search_files(self, project_id: str, query: str) -> List[Dict[str, Any]]:
        project_path = self.get_project_path(project_id)
        results = []
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                if query.lower() in file_path.name.lower():
                    results.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(project_path)),
                        "type": "file",
                        "match": "filename"
                    })
                elif file_path.stat().st_size < 500*1024:  # Only search small files
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if query.lower() in content.lower():
                            # Find line numbers
                            lines = []
                            for i, line in enumerate(content.split('\n'), 1):
                                if query.lower() in line.lower():
                                    lines.append({"line": i, "content": line.strip()[:100]})
                                    if len(lines) >= 5:
                                        break
                            
                            results.append({
                                "name": file_path.name,
                                "path": str(file_path.relative_to(project_path)),
                                "type": "file",
                                "match": "content",
                                "lines": lines
                            })
                    except:
                        continue
            
            if len(results) >= 50:
                break
        
        return results

workspace_manager = WorkspaceManager()
