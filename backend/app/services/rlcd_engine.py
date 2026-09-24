import random
import math
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import numpy as np
from pathlib import Path

from ..models.rlcd import ChoiceDecision, ScoreDecision, NoulDecision, DecisionType, ActionSpace
from ..models.project_state import ProjectState, ProjectStage
from ..config import settings

# Try to import torch, fallback to numpy if not available
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

class CalibrationStore:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.temperature: float = 1.0
        self.data_path = settings.data_root / "calibration" / "calibration.json"
        self.load()
    
    def add_record(self, raw_conf: float, calibrated_conf: float, outcome: bool, decision_type: str):
        self.records.append({
            "raw_confidence": raw_conf,
            "calibrated_confidence": calibrated_conf,
            "outcome": outcome,
            "decision_type": decision_type,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.records) > 1000:
            self.records = self.records[-1000:]
        self.save()
    
    def save(self):
        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            self.data_path.write_text(json.dumps({
                "records": self.records,
                "temperature": self.temperature
            }, indent=2))
        except Exception as e:
            print(f"Calibration save error: {e}")
    
    def load(self):
        try:
            if self.data_path.exists():
                data = json.loads(self.data_path.read_text())
                self.records = data.get("records", [])
                self.temperature = data.get("temperature", 1.0)
        except:
            self.records = []
    
    def compute_metrics(self) -> Dict[str, Any]:
        if not self.records:
            return {
                "expected_calibration_error": 0.0,
                "brier_score": 0.0,
                "accuracy": 0.0,
                "total_samples": 0,
                "confidence_buckets": [],
                "reliability_data": [],
                "temperature": self.temperature
            }
        
        # Brier score
        brier = np.mean([(r["calibrated_confidence"] - (1.0 if r["outcome"] else 0.0))**2 for r in self.records])
        
        # ECE with 10 buckets
        buckets = [[] for _ in range(10)]
        for r in self.records:
            bucket_idx = min(int(r["calibrated_confidence"] * 10), 9)
            buckets[bucket_idx].append(r)
        
        ece = 0.0
        confidence_buckets = []
        reliability_data = []
        
        total = len(self.records)
        for i, bucket in enumerate(buckets):
            if not bucket:
                confidence_buckets.append({
                    "bucket": f"{i/10:.1f}-{(i+1)/10:.1f}",
                    "count": 0,
                    "accuracy": 0,
                    "avg_confidence": 0
                })
                reliability_data.append({
                    "confidence": (i+0.5)/10,
                    "accuracy": 0,
                    "count": 0
                })
                continue
            
            acc = sum(1 for r in bucket if r["outcome"]) / len(bucket)
            avg_conf = sum(r["calibrated_confidence"] for r in bucket) / len(bucket)
            ece += abs(acc - avg_conf) * len(bucket) / total
            
            confidence_buckets.append({
                "bucket": f"{i/10:.1f}-{(i+1)/10:.1f}",
                "count": len(bucket),
                "accuracy": acc,
                "avg_confidence": avg_conf
            })
            reliability_data.append({
                "confidence": avg_conf,
                "accuracy": acc,
                "count": len(bucket)
            })
        
        accuracy = sum(1 for r in self.records if r["outcome"]) / total
        
        return {
            "expected_calibration_error": float(ece),
            "brier_score": float(brier),
            "accuracy": float(accuracy),
            "total_samples": total,
            "confidence_buckets": confidence_buckets,
            "reliability_data": reliability_data,
            "temperature": self.temperature
        }
    
    def calibrate_confidence(self, raw_conf: float) -> float:
        # Temperature scaling
        # For binary: calibrated = sigmoid(logit / T)
        # Simplified: apply temperature scaling
        try:
            # Convert to logit
            eps = 1e-7
            raw_conf = max(eps, min(1-eps, raw_conf))
            logit = math.log(raw_conf / (1 - raw_conf))
            calibrated_logit = logit / self.temperature
            calibrated = 1 / (1 + math.exp(-calibrated_logit))
            return max(0.01, min(0.99, calibrated))
        except:
            return raw_conf
    
    def update_temperature(self, new_temp: float):
        self.temperature = max(0.1, min(5.0, new_temp))
        self.save()

calibration_store = CalibrationStore()

if TORCH_AVAILABLE:
    class CalibratedDecisionModel(nn.Module):
        """PyTorch module for RLCD decision making"""
        def __init__(self, state_dim=128, action_dim=15):
            super().__init__()
            self.state_encoder = nn.Sequential(
                nn.Linear(state_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 64),
                nn.ReLU()
            )
            self.choice_head = nn.Linear(64, action_dim)
            self.score_head = nn.Linear(64, 1)
            self.noul_head = nn.Linear(64, 1)
            self.confidence_head = nn.Linear(64, 1)
        
        def encode_state(self, state_vector):
            return self.state_encoder(state_vector)
        
        def choice(self, encoded):
            logits = self.choice_head(encoded)
            probs = torch.softmax(logits, dim=-1)
            return probs
        
        def score(self, encoded):
            return torch.sigmoid(self.score_head(encoded))
        
        def noul(self, encoded):
            return torch.sigmoid(self.noul_head(encoded))
        
        def calibrate(self, confidence, temperature=1.0):
            # Temperature scaling
            logit = torch.log(confidence / (1 - confidence + 1e-7) + 1e-7)
            return torch.sigmoid(logit / temperature)
else:
    class CalibratedDecisionModel:
        """Numpy fallback for decision model"""
        def __init__(self, state_dim=128, action_dim=15):
            self.state_dim = state_dim
            self.action_dim = action_dim
            # Random weights for development
            self.weights = np.random.randn(state_dim, 64) * 0.1
        
        def encode_state(self, state_vector):
            if isinstance(state_vector, list):
                state_vector = np.array(state_vector)
            return np.tanh(state_vector @ self.weights)
        
        def choice(self, encoded):
            logits = np.random.randn(self.action_dim)
            exp_logits = np.exp(logits - np.max(logits))
            return exp_logits / exp_logits.sum()
        
        def score(self, encoded):
            return random.uniform(0, 1)
        
        def noul(self, encoded):
            return random.uniform(0, 1)
        
        def calibrate(self, confidence, temperature=1.0):
            return calibration_store.calibrate_confidence(confidence)

class RLCDDecisionEngine:
    """
    RLCD-inspired decision engine with bounded decision architecture
    Inspired by publicly described concepts, not proprietary reproduction
    """
    def __init__(self):
        self.action_space = [a.value for a in ActionSpace]
        self.model = CalibratedDecisionModel()
        self.calibration = calibration_store
        self.development_policy = True  # Mark as development policy
        
        # Policy versions
        self.policy_versions = {
            "v1": {"accuracy": 0.72, "is_production": True, "notes": "DEVELOPMENT POLICY - deterministic fallback"},
            "v2": {"accuracy": 0.0, "is_production": False, "notes": "Trainable policy candidate"}
        }
    
    def _encode_project_state(self, project_state: ProjectState) -> List[float]:
        """Encode project state into vector"""
        # Simple feature encoding
        stage_map = {s.value: i for i, s in enumerate(ProjectStage)}
        stage_idx = stage_map.get(project_state.stage.value, 0)
        
        features = [
            stage_idx / len(ProjectStage),
            len(project_state.requirements) / 20.0,
            len(project_state.research) / 10.0,
            1.0 if project_state.abstract else 0.0,
            1.0 if project_state.abstract_approved else 0.0,
            len(project_state.solution) / 10.0,
            len(project_state.frontend) / 10.0,
            len(project_state.backend) / 10.0,
            len(project_state.decisions) / 50.0,
            len(project_state.file_changes) / 100.0,
            len(project_state.problem_statement) / 1000.0,
            1.0 if project_state.tech_stack else 0.0,
        ]
        
        # Pad to 128 dim
        while len(features) < 128:
            features.append(0.0)
        
        return features[:128]
    
    def _get_valid_actions(self, project_state: ProjectState) -> List[str]:
        """Get valid actions based on current stage"""
        stage = project_state.stage
        
        if stage == ProjectStage.INITIAL:
            return [ActionSpace.ANALYZE_PROBLEM.value, ActionSpace.RESEARCH.value, ActionSpace.CREATE_ABSTRACT.value]
        elif stage == ProjectStage.ANALYZING:
            return [ActionSpace.RESEARCH.value, ActionSpace.CREATE_ABSTRACT.value, ActionSpace.ASK_USER.value]
        elif stage == ProjectStage.RESEARCHING:
            return [ActionSpace.CREATE_ABSTRACT.value, ActionSpace.ANALYZE_PROBLEM.value]
        elif stage == ProjectStage.ABSTRACT_GENERATION:
            return [ActionSpace.CREATE_ABSTRACT.value, ActionSpace.REVISE_ABSTRACT.value]
        elif stage == ProjectStage.ABSTRACT_REVIEW:
            return [ActionSpace.REVISE_ABSTRACT.value, ActionSpace.CREATE_SOLUTION.value, ActionSpace.ASK_USER.value]
        elif stage == ProjectStage.ABSTRACT_APPROVED:
            return [ActionSpace.CREATE_SOLUTION.value, ActionSpace.CREATE_FRONTEND.value, ActionSpace.CREATE_BACKEND.value]
        elif stage == ProjectStage.ARCHITECTURE:
            return [ActionSpace.CREATE_FRONTEND.value, ActionSpace.CREATE_BACKEND.value, ActionSpace.CREATE_DATABASE.value]
        elif stage == ProjectStage.FRONTEND:
            return [ActionSpace.CREATE_FRONTEND.value, ActionSpace.CREATE_BACKEND.value, ActionSpace.INTEGRATE.value, ActionSpace.RUN_TESTS.value, ActionSpace.VERIFY.value]
        elif stage == ProjectStage.BACKEND:
            return [ActionSpace.CREATE_BACKEND.value, ActionSpace.CREATE_DATABASE.value, ActionSpace.INTEGRATE.value, ActionSpace.RUN_TESTS.value]
        elif stage == ProjectStage.INTEGRATION:
            return [ActionSpace.INTEGRATE.value, ActionSpace.RUN_TESTS.value, ActionSpace.VERIFY.value]
        elif stage == ProjectStage.TESTING:
            return [ActionSpace.RUN_TESTS.value, ActionSpace.DEBUG.value, ActionSpace.VERIFY.value]
        elif stage == ProjectStage.DEBUGGING:
            return [ActionSpace.DEBUG.value, ActionSpace.RUN_TESTS.value, ActionSpace.VERIFY.value]
        elif stage == ProjectStage.VERIFICATION:
            return [ActionSpace.VERIFY.value, ActionSpace.CREATE_PRESENTATION.value, ActionSpace.STOP.value]
        elif stage == ProjectStage.PRESENTATION:
            return [ActionSpace.CREATE_PRESENTATION.value, ActionSpace.STOP.value, ActionSpace.VERIFY.value]
        else:
            return [ActionSpace.ANALYZE_PROBLEM.value, ActionSpace.ASK_USER.value, ActionSpace.STOP.value]
    
    def decide_choice(self, project_state: ProjectState, custom_action_space: List[str] = None) -> ChoiceDecision:
        """CHOICE decision - selects one action from finite space"""
        valid_actions = custom_action_space or self._get_valid_actions(project_state)
        
        # Development policy: deterministic but with probabilities
        # Based on stage progression
        probabilities = {}
        
        # Heuristic for development policy
        stage = project_state.stage
        if stage == ProjectStage.INITIAL:
            probabilities = {
                ActionSpace.ANALYZE_PROBLEM.value: 0.1,
                ActionSpace.RESEARCH.value: 0.2,
                ActionSpace.CREATE_ABSTRACT.value: 0.7
            }
        elif stage == ProjectStage.ABSTRACT_APPROVED:
            probabilities = {
                ActionSpace.CREATE_SOLUTION.value: 0.6,
                ActionSpace.CREATE_FRONTEND.value: 0.3,
                ActionSpace.CREATE_BACKEND.value: 0.1
            }
        elif stage == ProjectStage.ARCHITECTURE:
            probabilities = {
                ActionSpace.CREATE_FRONTEND.value: 0.5,
                ActionSpace.CREATE_BACKEND.value: 0.4,
                ActionSpace.CREATE_DATABASE.value: 0.1
            }
        elif stage == ProjectStage.FRONTEND:
            # If frontend files exist, suggest backend
            has_frontend = len(project_state.frontend) > 0 or len([f for f in project_state.file_changes if 'src' in f.path]) > 0
            if has_frontend:
                probabilities = {
                    ActionSpace.CREATE_BACKEND.value: 0.4,
                    ActionSpace.RUN_TESTS.value: 0.3,
                    ActionSpace.VERIFY.value: 0.2,
                    ActionSpace.CREATE_FRONTEND.value: 0.1
                }
            else:
                probabilities = {
                    ActionSpace.CREATE_FRONTEND.value: 0.7,
                    ActionSpace.CREATE_BACKEND.value: 0.1,
                    ActionSpace.RUN_TESTS.value: 0.1,
                    ActionSpace.VERIFY.value: 0.1
                }
        else:
            # Default uniform with bias to valid actions
            for action in valid_actions:
                probabilities[action] = 1.0 / len(valid_actions)
            
            # Boost based on stage
            if stage == ProjectStage.BACKEND:
                if ActionSpace.CREATE_BACKEND.value in probabilities:
                    probabilities[ActionSpace.CREATE_BACKEND.value] = 0.6
            elif stage == ProjectStage.TESTING:
                if ActionSpace.RUN_TESTS.value in probabilities:
                    probabilities[ActionSpace.RUN_TESTS.value] = 0.5
        
        # Ensure all valid actions have probability
        for action in valid_actions:
            if action not in probabilities:
                probabilities[action] = 0.05
        
        # Normalize
        total = sum(probabilities.values())
        for k in probabilities:
            probabilities[k] /= total
        
        # Select action with highest prob
        selected = max(probabilities.items(), key=lambda x: x[1])[0]
        raw_conf = probabilities[selected]
        calibrated_conf = self.calibration.calibrate_confidence(raw_conf)
        
        # Evidence
        evidence = [
            f"Current stage: {project_state.stage.value}",
            f"Valid actions: {', '.join(valid_actions[:3])}",
            f"Project has abstract: {bool(project_state.abstract)}",
            f"Requirements count: {len(project_state.requirements)}"
        ]
        
        if project_state.abstract_approved:
            evidence.append("Abstract approved by user")
        
        # Risk calculation
        risk = 0.1
        if selected in [ActionSpace.CREATE_FRONTEND.value, ActionSpace.CREATE_BACKEND.value]:
            risk = 0.2
        elif selected == ActionSpace.DEBUG.value:
            risk = 0.3
        elif selected == ActionSpace.ASK_USER.value:
            risk = 0.05
        
        return ChoiceDecision(
            selected_action=selected,
            probabilities=probabilities,
            raw_confidence=raw_conf,
            calibrated_confidence=calibrated_conf,
            risk=risk,
            evidence=evidence,
            reasoning_summary=f"Selected {selected} based on stage {stage.value} and available information. Development policy active.",
            requires_verification=selected not in [ActionSpace.ASK_USER.value, ActionSpace.STOP.value],
            requires_approval=selected in [ActionSpace.CREATE_PRESENTATION.value, ActionSpace.STOP.value]
        )
    
    def decide_score(self, project_state: ProjectState, score_name: str) -> ScoreDecision:
        """SCORE decision - bounded value"""
        # Heuristic scoring based on project state
        raw_value = 0.5
        
        if score_name == "abstract_quality":
            if project_state.abstract:
                raw_value = min(0.9, 0.5 + len(project_state.abstract) / 1000)
                if project_state.abstract_approved:
                    raw_value = min(0.95, raw_value + 0.2)
            else:
                raw_value = 0.1
        
        elif score_name == "frontend_readiness":
            if project_state.frontend:
                raw_value = 0.8
            elif project_state.stage in [ProjectStage.FRONTEND, ProjectStage.INTEGRATION, ProjectStage.VERIFICATION]:
                raw_value = 0.6
            else:
                raw_value = 0.3
        
        elif score_name == "backend_readiness":
            if project_state.backend:
                raw_value = 0.8
            elif project_state.stage in [ProjectStage.BACKEND, ProjectStage.INTEGRATION]:
                raw_value = 0.5
            else:
                raw_value = 0.2
        
        elif score_name == "research_quality":
            raw_value = min(0.9, len(project_state.research) / 5.0)
        
        elif score_name == "project_completion":
            stage_progress = {
                ProjectStage.INITIAL: 0.0,
                ProjectStage.ANALYZING: 0.1,
                ProjectStage.RESEARCHING: 0.2,
                ProjectStage.ABSTRACT_GENERATION: 0.3,
                ProjectStage.ABSTRACT_REVIEW: 0.35,
                ProjectStage.ABSTRACT_APPROVED: 0.4,
                ProjectStage.ARCHITECTURE: 0.5,
                ProjectStage.FRONTEND: 0.6,
                ProjectStage.BACKEND: 0.7,
                ProjectStage.INTEGRATION: 0.8,
                ProjectStage.TESTING: 0.85,
                ProjectStage.VERIFICATION: 0.9,
                ProjectStage.PRESENTATION: 0.95,
                ProjectStage.COMPLETED: 1.0
            }
            raw_value = stage_progress.get(project_state.stage, 0.0)
        
        elif score_name == "risk":
            raw_value = 0.2
            if project_state.stage == ProjectStage.DEBUGGING:
                raw_value = 0.6
            elif project_state.stage == ProjectStage.BLOCKED:
                raw_value = 0.9
        
        elif score_name == "test_quality":
            raw_value = min(0.9, len(project_state.tests) / 5.0) if project_state.tests else 0.2
        
        else:
            raw_value = random.uniform(0.3, 0.8)
        
        calibrated = self.calibration.calibrate_confidence(raw_value)
        
        evidence = [
            f"Stage: {project_state.stage.value}",
            f"Metric: {score_name}",
            f"Based on project artifacts"
        ]
        
        return ScoreDecision(
            name=score_name,
            value=calibrated,
            raw_value=raw_value,
            calibrated_value=calibrated,
            confidence=calibrated,
            evidence=evidence
        )
    
    def decide_noul(self, project_state: ProjectState, question: str) -> NoulDecision:
        """NOUL - calibrated binary decision"""
        question_lower = question.lower()
        
        # Heuristic YES probability
        yes_prob = 0.5
        
        if "abstract ready" in question_lower:
            if project_state.abstract and len(project_state.abstract) > 100:
                yes_prob = 0.85
                if project_state.abstract_approved:
                    yes_prob = 0.95
            else:
                yes_prob = 0.15
        
        elif "frontend" in question_lower and "activate" in question_lower:
            if project_state.stage in [ProjectStage.ABSTRACT_APPROVED, ProjectStage.ARCHITECTURE, ProjectStage.FRONTEND]:
                yes_prob = 0.82
            else:
                yes_prob = 0.2
        
        elif "backend" in question_lower:
            if project_state.frontend or project_state.stage in [ProjectStage.FRONTEND, ProjectStage.BACKEND]:
                yes_prob = 0.75
            else:
                yes_prob = 0.3
        
        elif "research" in question_lower:
            if len(project_state.research) > 0:
                yes_prob = 0.8
            else:
                yes_prob = 0.6 if project_state.stage == ProjectStage.ANALYZING else 0.2
        
        elif "verify" in question_lower:
            if project_state.stage in [ProjectStage.TESTING, ProjectStage.VERIFICATION]:
                yes_prob = 0.9
            else:
                yes_prob = 0.3
        
        elif "approved" in question_lower:
            yes_prob = 0.9 if project_state.abstract_approved else 0.3
        
        else:
            yes_prob = random.uniform(0.4, 0.8)
        
        no_prob = 1 - yes_prob
        raw_conf = max(yes_prob, no_prob)
        calibrated_conf = self.calibration.calibrate_confidence(raw_conf)
        
        # Recalibrate yes/no with calibrated confidence
        if yes_prob > no_prob:
            calibrated_yes = calibrated_conf
            calibrated_no = 1 - calibrated_conf
        else:
            calibrated_no = calibrated_conf
            calibrated_yes = 1 - calibrated_conf
        
        evidence = [
            f"Question: {question}",
            f"Stage: {project_state.stage.value}",
            f"Project state analysis"
        ]
        
        return NoulDecision(
            question=question,
            yes_prob=calibrated_yes,
            no_prob=calibrated_no,
            decision=calibrated_yes > 0.5,
            raw_confidence=raw_conf,
            calibrated_confidence=calibrated_conf,
            evidence=evidence,
            reasoning_summary=f"Evaluated '{question}' -> {'YES' if calibrated_yes > 0.5 else 'NO'} with {calibrated_conf:.2f} confidence"
        )
    
    def get_calibration_metrics(self):
        return self.calibration.compute_metrics()
    
    def record_outcome(self, decision_id: str, raw_conf: float, calibrated_conf: float, outcome: bool, decision_type: str):
        self.calibration.add_record(raw_conf, calibrated_conf, outcome, decision_type)

rlcd_engine = RLCDDecisionEngine()
