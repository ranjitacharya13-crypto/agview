from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..models.project_state import ProjectState
from ..services.project_manager import project_manager
from ..services.event_bus import event_bus
from ..services.filesystem import filesystem_service
from ..services.terminal import terminal_service
from ..services.model_provider import model_registry
from ..models.events import EventType
import uuid
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, name: str, capabilities: List[str]):
        self.name = name
        self.capabilities = capabilities
        self.model_provider = model_registry.route_by_capability(capabilities)
        self.project_manager = project_manager
        self.event_bus = event_bus
        self.filesystem = filesystem_service
        self.terminal = terminal_service
    
    def emit_event(self, project_id: str, event_type: EventType, message: str, data: Dict[str, Any] = None, decision_id: str = None):
        return self.event_bus.emit(
            project_id=project_id,
            event_type=event_type,
            message=message,
            agent=self.name,
            decision_id=decision_id,
            data=data or {}
        )
    
    def get_project(self, project_id: str) -> Optional[ProjectState]:
        return self.project_manager.get_project(project_id)
    
    def save_project(self, state: ProjectState):
        self.project_manager.save_project(state)
    
    @abstractmethod
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def log(self, project_id: str, message: str):
        self.emit_event(project_id, EventType.AGENT_STARTED, message)

class AgentTool:
    """Tool definitions for agents"""
    
    @staticmethod
    def read_file(project_id: str, path: str) -> Dict[str, Any]:
        return filesystem_service.read_file(project_id, path)
    
    @staticmethod
    def write_file(project_id: str, path: str, content: str, agent: str = "agent") -> Dict[str, Any]:
        return filesystem_service.write_file(project_id, path, content, agent=agent)
    
    @staticmethod
    def list_directory(project_id: str, path: str = "") -> Dict[str, Any]:
        return filesystem_service.list_directory(project_id, path)
    
    @staticmethod
    def search_files(project_id: str, query: str) -> Dict[str, Any]:
        return filesystem_service.search(project_id, query)
    
    @staticmethod
    def run_terminal(project_id: str, command: str, cwd: str = "") -> Dict[str, Any]:
        return terminal_service.execute(project_id, command, cwd)
    
    @staticmethod
    def create_directory(project_id: str, path: str) -> Dict[str, Any]:
        return filesystem_service.create_directory(project_id, path)
