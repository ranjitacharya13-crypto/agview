from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid

class ProjectStage(str, Enum):
    INITIAL = "INITIAL"
    ANALYZING = "ANALYZING"
    RESEARCHING = "RESEARCHING"
    ABSTRACT_GENERATION = "ABSTRACT_GENERATION"
    ABSTRACT_REVIEW = "ABSTRACT_REVIEW"
    ABSTRACT_APPROVED = "ABSTRACT_APPROVED"
    ARCHITECTURE = "ARCHITECTURE"
    FRONTEND = "FRONTEND"
    BACKEND = "BACKEND"
    INTEGRATION = "INTEGRATION"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    VERIFICATION = "VERIFICATION"
    PRESENTATION = "PRESENTATION"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"

class Requirement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    description: str
    type: str = "feature"  # feature, actor, workflow, entity, screen, constraint
    priority: str = "medium"
    source: str = "abstract"

class ResearchItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    query: str
    source: str
    url: str
    title: str
    claim: str
    confidence: float = 0.8
    date: Optional[str] = None

class DecisionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.now)
    type: str  # CHOICE, SCORE, NOUL
    state: str
    action: Optional[str] = None
    probabilities: Optional[Dict[str, float]] = None
    score_name: Optional[str] = None
    score_value: Optional[float] = None
    question: Optional[str] = None
    yes_prob: Optional[float] = None
    no_prob: Optional[float] = None
    raw_confidence: float
    calibrated_confidence: float
    risk: float = 0.1
    requires_verification: bool = True
    requires_approval: bool = False
    evidence: List[str] = []
    agent: str = "master"

class Trajectory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.now)
    state: Dict[str, Any]
    action: str
    raw_probability: float
    result: str  # success, failure
    reward: float
    next_state: Dict[str, Any]
    decision_id: Optional[str] = None
    agent: str
    tool_calls: int = 0
    latency_ms: int = 0
    cost: float = 0.0

class FileChange(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.now)
    path: str
    operation: str  # CREATE, READ, UPDATE, DELETE, MOVE, RENAME
    agent: str
    decision_id: Optional[str] = None
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    reason: str = ""

class ProjectState(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    root_directory: str
    created_date: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    current_branch: str = "main"
    stage: ProjectStage = ProjectStage.INITIAL
    
    problem_statement: str = ""
    requirements: List[Requirement] = []
    research: List[ResearchItem] = []
    abstract: str = ""
    abstract_approved: bool = False
    
    solution: Dict[str, Any] = {}
    frontend: Dict[str, Any] = {}
    backend: Dict[str, Any] = {}
    database: Dict[str, Any] = {}
    tests: Dict[str, Any] = {}
    verification: Dict[str, Any] = {}
    presentation: Dict[str, Any] = {}
    
    decisions: List[DecisionRecord] = []
    trajectories: List[Trajectory] = []
    file_changes: List[FileChange] = []
    user_approvals: List[Dict[str, Any]] = []
    
    # Memory categories
    memory: Dict[str, List[Dict[str, Any]]] = Field(default_factory=lambda: {
        "PROJECT": [],
        "RESEARCH": [],
        "ABSTRACT": [],
        "ARCHITECTURE": [],
        "DECISIONS": [],
        "FILES": [],
        "ERRORS": [],
        "FIXES": [],
        "TESTS": [],
        "USER_PREFERENCES": [],
        "APPROVALS": [],
        "TRAJECTORIES": []
    })
    
    # Metadata
    tech_stack: Dict[str, Any] = {}
    actors: List[str] = []
    features: List[str] = []
    screens: List[str] = []
    
    def to_summary(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "stage": self.stage,
            "problem_statement": self.problem_statement[:200],
            "requirements_count": len(self.requirements),
            "research_count": len(self.research),
            "has_abstract": bool(self.abstract),
            "decisions_count": len(self.decisions),
            "file_changes_count": len(self.file_changes)
        }
