from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    PROJECT_CREATED = "PROJECT_CREATED"
    RESEARCH_STARTED = "RESEARCH_STARTED"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    ABSTRACT_STARTED = "ABSTRACT_STARTED"
    ABSTRACT_GENERATED = "ABSTRACT_GENERATED"
    ABSTRACT_REVISED = "ABSTRACT_REVISED"
    ABSTRACT_APPROVED = "ABSTRACT_APPROVED"
    FRONTEND_STARTED = "FRONTEND_STARTED"
    BACKEND_STARTED = "BACKEND_STARTED"
    FILE_CREATED = "FILE_CREATED"
    FILE_EDITED = "FILE_EDITED"
    FILE_DELETED = "FILE_DELETED"
    COMMAND_STARTED = "COMMAND_STARTED"
    COMMAND_COMPLETED = "COMMAND_COMPLETED"
    COMMAND_FAILED = "COMMAND_FAILED"
    TEST_STARTED = "TEST_STARTED"
    TEST_PASSED = "TEST_PASSED"
    TEST_FAILED = "TEST_FAILED"
    DEBUG_STARTED = "DEBUG_STARTED"
    FIX_APPLIED = "FIX_APPLIED"
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"
    RLCD_DECISION = "RLCD_DECISION"
    REWARD_RECORDED = "REWARD_RECORDED"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    PRESENTATION_STARTED = "PRESENTATION_STARTED"
    PRESENTATION_COMPLETED = "PRESENTATION_COMPLETED"
    ERROR = "ERROR"

class ProjectEvent(BaseModel):
    id: str
    project_id: str
    type: EventType
    timestamp: datetime
    agent: Optional[str] = None
    decision_id: Optional[str] = None
    data: Dict[str, Any] = {}
    message: str = ""
    
    def to_ws_message(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "agent": self.agent,
            "decision_id": self.decision_id,
            "data": self.data,
            "message": self.message
        }
