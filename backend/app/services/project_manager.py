import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from ..models.project_state import ProjectState, ProjectStage
from ..config import settings
from ..core.workspace import workspace_manager
from .event_bus import event_bus
from ..models.events import EventType

class ProjectManager:
    def __init__(self):
        self.projects_root = settings.projects_root
        self.projects_root.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, ProjectState] = {}
    
    def _project_file(self, project_id: str) -> Path:
        return self.projects_root / f"{project_id}.json"
    
    def create_project(self, name: str, problem_statement: str = "") -> ProjectState:
        project_id = str(uuid.uuid4())
        root_dir = str(workspace_manager.create_project_workspace(project_id, name))
        
        state = ProjectState(
            project_id=project_id,
            name=name,
            root_directory=root_dir,
            problem_statement=problem_statement,
            stage=ProjectStage.INITIAL
        )
        
        self.save_project(state)
        self._cache[project_id] = state
        
        event_bus.emit(
            project_id=project_id,
            event_type=EventType.PROJECT_CREATED,
            message=f"Project '{name}' created",
            data={"name": name, "problem": problem_statement[:100]}
        )
        
        return state
    
    def get_project(self, project_id: str) -> Optional[ProjectState]:
        if project_id in self._cache:
            return self._cache[project_id]
        
        file_path = self._project_file(project_id)
        if not file_path.exists():
            return None
        
        try:
            data = json.loads(file_path.read_text())
            state = ProjectState(**data)
            self._cache[project_id] = state
            return state
        except Exception as e:
            print(f"Error loading project {project_id}: {e}")
            return None
    
    def save_project(self, state: ProjectState):
        state.last_modified = datetime.now()
        file_path = self._project_file(state.project_id)
        
        # Convert to dict with json serializable
        data = state.model_dump(mode='json')
        file_path.write_text(json.dumps(data, indent=2, default=str))
        self._cache[state.project_id] = state
    
    def list_projects(self) -> List[Dict[str, Any]]:
        projects = []
        for file_path in self.projects_root.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                projects.append({
                    "project_id": data.get("project_id"),
                    "name": data.get("name"),
                    "stage": data.get("stage"),
                    "created_date": data.get("created_date"),
                    "last_modified": data.get("last_modified"),
                    "problem_statement": data.get("problem_statement", "")[:100]
                })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return sorted(projects, key=lambda x: x.get("last_modified", ""), reverse=True)
    
    def update_problem(self, project_id: str, problem: str) -> Optional[ProjectState]:
        state = self.get_project(project_id)
        if not state:
            return None
        
        state.problem_statement = problem
        state.stage = ProjectStage.ANALYZING
        self.save_project(state)
        return state
    
    def update_stage(self, project_id: str, stage: ProjectStage) -> Optional[ProjectState]:
        state = self.get_project(project_id)
        if not state:
            return None
        
        state.stage = stage
        self.save_project(state)
        return state
    
    def add_requirement(self, project_id: str, req: Dict[str, Any]) -> Optional[ProjectState]:
        from ..models.project_state import Requirement
        state = self.get_project(project_id)
        if not state:
            return None
        
        requirement = Requirement(**req)
        state.requirements.append(requirement)
        self.save_project(state)
        return state
    
    def add_research(self, project_id: str, research: Dict[str, Any]) -> Optional[ProjectState]:
        from ..models.project_state import ResearchItem
        state = self.get_project(project_id)
        if not state:
            return None
        
        item = ResearchItem(**research)
        state.research.append(item)
        self.save_project(state)
        return state
    
    def add_memory(self, project_id: str, category: str, content: Dict[str, Any]) -> Optional[ProjectState]:
        state = self.get_project(project_id)
        if not state:
            return None
        
        if category not in state.memory:
            state.memory[category] = []
        
        content["timestamp"] = datetime.now().isoformat()
        state.memory[category].append(content)
        self.save_project(state)
        return state
    
    def delete_project(self, project_id: str) -> bool:
        file_path = self._project_file(project_id)
        if file_path.exists():
            file_path.unlink()
        
        if project_id in self._cache:
            del self._cache[project_id]
        
        # Delete workspace
        workspace_path = workspace_manager.get_project_path(project_id)
        if workspace_path.exists():
            import shutil
            shutil.rmtree(workspace_path)
        
        return True

project_manager = ProjectManager()
