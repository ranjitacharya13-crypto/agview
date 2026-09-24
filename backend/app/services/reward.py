from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime
import uuid
from ..models.rlcd import RewardConfig
from ..models.project_state import Trajectory
from ..config import settings

class RewardService:
    def __init__(self):
        self.config = RewardConfig()
        self.trajectory_path = settings.data_root / "trajectories"
        self.trajectory_path.mkdir(parents=True, exist_ok=True)
    
    def calculate_reward(self, action: str, result: str, context: Dict[str, Any]) -> float:
        """Calculate reward based on outcome"""
        reward = 0.0
        
        # Positive rewards
        if result == "success":
            reward += self.config.successful_task
            
            if context.get("tests_passed"):
                reward += self.config.passing_tests
            
            if context.get("correct_implementation"):
                reward += self.config.correct_implementation
            
            if context.get("verified_source"):
                reward += self.config.verified_source
            
            if context.get("user_approval"):
                reward += self.config.user_approval
            
            if context.get("successful_integration"):
                reward += self.config.successful_integration
            
            # Efficiency bonus
            tool_calls = context.get("tool_calls", 0)
            if tool_calls < 5:
                reward += self.config.efficient_execution
        
        # Negative rewards
        else:
            reward += self.config.failed_implementation
            
            if context.get("hallucinated_info"):
                reward += self.config.hallucinated_info
            
            if context.get("fabricated_sources"):
                reward += self.config.fabricated_sources
            
            if context.get("failed_tests"):
                reward += self.config.failed_tests
            
            if context.get("wrong_agent_routing"):
                reward += self.config.wrong_agent_routing
            
            if context.get("unverified_claims"):
                reward += self.config.unverified_claims
            
            # Cost penalties
            if context.get("excessive_retries"):
                reward += self.config.unnecessary_retries
            
            if context.get("excessive_cost"):
                reward += self.config.excessive_cost
            
            if context.get("excessive_latency"):
                reward += self.config.excessive_latency
        
        return max(-3.0, min(3.0, reward))
    
    def create_trajectory(self, state: Dict[str, Any], action: str, result: str,
                         reward: float, next_state: Dict[str, Any],
                         decision_id: str = None, agent: str = "master",
                         raw_probability: float = 0.8,
                         tool_calls: int = 0, latency_ms: int = 0, cost: float = 0.0) -> Trajectory:
        
        trajectory = Trajectory(
            state=state,
            action=action,
            raw_probability=raw_probability,
            result=result,
            reward=reward,
            next_state=next_state,
            decision_id=decision_id,
            agent=agent,
            tool_calls=tool_calls,
            latency_ms=latency_ms,
            cost=cost
        )
        
        self.save_trajectory(trajectory)
        return trajectory
    
    def save_trajectory(self, trajectory: Trajectory):
        # Save to file
        project_id = trajectory.state.get("project_id", "unknown")
        file_path = self.trajectory_path / f"{project_id}.jsonl"
        
        with open(file_path, "a") as f:
            f.write(trajectory.model_dump_json() + "\n")
    
    def get_trajectories(self, project_id: str) -> List[Dict[str, Any]]:
        file_path = self.trajectory_path / f"{project_id}.jsonl"
        if not file_path.exists():
            return []
        
        trajectories = []
        try:
            for line in file_path.read_text().splitlines():
                if line.strip():
                    trajectories.append(json.loads(line))
        except Exception as e:
            print(f"Error reading trajectories: {e}")
        
        return trajectories[-100:]  # Last 100
    
    def get_all_trajectories(self) -> List[Dict[str, Any]]:
        all_trajs = []
        for file_path in self.trajectory_path.glob("*.jsonl"):
            try:
                for line in file_path.read_text().splitlines()[-20:]:  # Last 20 per project
                    if line.strip():
                        all_trajs.append(json.loads(line))
            except:
                continue
        return all_trajs
    
    def compute_stats(self, project_id: str = None) -> Dict[str, Any]:
        if project_id:
            trajs = self.get_trajectories(project_id)
        else:
            trajs = self.get_all_trajectories()
        
        if not trajs:
            return {
                "total": 0,
                "success_rate": 0,
                "avg_reward": 0,
                "avg_latency": 0,
                "avg_cost": 0
            }
        
        total = len(trajs)
        successes = sum(1 for t in trajs if t.get("result") == "success")
        avg_reward = sum(t.get("reward", 0) for t in trajs) / total
        avg_latency = sum(t.get("latency_ms", 0) for t in trajs) / total
        avg_cost = sum(t.get("cost", 0) for t in trajs) / total
        
        return {
            "total": total,
            "success_rate": successes / total if total > 0 else 0,
            "avg_reward": avg_reward,
            "avg_latency": avg_latency,
            "avg_cost": avg_cost,
            "recent_rewards": [t.get("reward", 0) for t in trajs[-20:]]
        }

reward_service = RewardService()
