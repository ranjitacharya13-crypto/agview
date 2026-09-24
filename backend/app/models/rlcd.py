from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from enum import Enum

class DecisionType(str, Enum):
    CHOICE = "choice"
    SCORE = "score"
    NOUL = "noul"

class ActionSpace(str, Enum):
    ANALYZE_PROBLEM = "ANALYZE_PROBLEM"
    RESEARCH = "RESEARCH"
    CREATE_ABSTRACT = "CREATE_ABSTRACT"
    REVISE_ABSTRACT = "REVISE_ABSTRACT"
    CREATE_SOLUTION = "CREATE_SOLUTION"
    CREATE_FRONTEND = "CREATE_FRONTEND"
    CREATE_BACKEND = "CREATE_BACKEND"
    CREATE_DATABASE = "CREATE_DATABASE"
    INTEGRATE = "INTEGRATE"
    RUN_TESTS = "RUN_TESTS"
    DEBUG = "DEBUG"
    VERIFY = "VERIFY"
    CREATE_PRESENTATION = "CREATE_PRESENTATION"
    ASK_USER = "ASK_USER"
    STOP = "STOP"
    
    # Frontend specific
    ANALYZE_REQUIREMENTS = "ANALYZE_REQUIREMENTS"
    INSPECT_REPOSITORY = "INSPECT_REPOSITORY"
    SEARCH_CODE = "SEARCH_CODE"
    READ_FILE = "READ_FILE"
    PLAN_FRONTEND = "PLAN_FRONTEND"
    CREATE_FILE = "CREATE_FILE"
    EDIT_FILE = "EDIT_FILE"
    MOVE_FILE = "MOVE_FILE"
    DELETE_FILE = "DELETE_FILE"
    INSTALL_DEPENDENCY = "INSTALL_DEPENDENCY"
    RUN_COMMAND = "RUN_COMMAND"
    START_SERVER = "START_SERVER"
    STOP_SERVER = "STOP_SERVER"
    RUN_BUILD = "RUN_BUILD"
    RUN_TEST = "RUN_TEST"
    RUN_BROWSER_TEST = "RUN_BROWSER_TEST"
    INSPECT_ERROR = "INSPECT_ERROR"
    FIX_ERROR = "FIX_ERROR"
    REVIEW_UI = "REVIEW_UI"

class ChoiceDecision(BaseModel):
    type: DecisionType = DecisionType.CHOICE
    selected_action: str
    probabilities: Dict[str, float]
    raw_confidence: float
    calibrated_confidence: float
    risk: float = 0.1
    evidence: List[str] = []
    reasoning_summary: str = ""
    requires_verification: bool = True
    requires_approval: bool = False

class ScoreDecision(BaseModel):
    type: DecisionType = DecisionType.SCORE
    name: str  # abstract_quality, frontend_readiness, etc
    value: float  # 0-1 normalized
    raw_value: float
    calibrated_value: float
    confidence: float
    evidence: List[str] = []

class NoulDecision(BaseModel):
    type: DecisionType = DecisionType.NOUL
    question: str
    yes_prob: float
    no_prob: float
    decision: bool  # True = YES
    raw_confidence: float
    calibrated_confidence: float
    evidence: List[str] = []
    reasoning_summary: str = ""

class RLCDDecisionResponse(BaseModel):
    decision_id: str
    project_id: str
    decision: Any  # ChoiceDecision | ScoreDecision | NoulDecision
    state_context: str
    timestamp: str
    agent: str = "rlcd_engine"

class CalibrationMetrics(BaseModel):
    expected_calibration_error: float
    brier_score: float
    accuracy: float
    total_samples: int
    confidence_buckets: List[Dict[str, Any]]
    reliability_data: List[Dict[str, float]]
    temperature: float = 1.0

class RewardConfig(BaseModel):
    successful_task: float = 1.0
    passing_tests: float = 0.8
    correct_implementation: float = 1.0
    verified_source: float = 0.5
    user_approval: float = 0.7
    efficient_execution: float = 0.3
    successful_integration: float = 1.0
    
    failed_implementation: float = -1.0
    hallucinated_info: float = -1.5
    fabricated_sources: float = -2.0
    failed_tests: float = -0.8
    unnecessary_retries: float = -0.2
    excessive_cost: float = -0.3
    excessive_latency: float = -0.2
    wrong_agent_routing: float = -0.5
    unverified_claims: float = -0.7

class PolicyVersion(BaseModel):
    version: str
    created_at: str
    accuracy: float
    calibration_error: float
    is_production: bool = False
    trajectory_count: int = 0
    notes: str = ""
