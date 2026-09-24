from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from ...services.rlcd_engine import rlcd_engine
from ...services.project_manager import project_manager
from ...services.reward import reward_service

router = APIRouter()

class DecisionRequest(BaseModel):
    project_id: str
    decision_type: str = "choice"  # choice, score, noul
    action_space: Optional[List[str]] = None
    score_name: str = "project_completion"
    question: str = "Is the abstract ready?"

@router.post("/decision")
async def make_decision(req: DecisionRequest):
    project = project_manager.get_project(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if req.decision_type == "choice":
        decision = rlcd_engine.decide_choice(project, custom_action_space=req.action_space)
        return {
            "success": True,
            "decision": decision.model_dump(),
            "type": "choice",
            "project_stage": project.stage.value
        }
    
    elif req.decision_type == "score":
        decision = rlcd_engine.decide_score(project, req.score_name)
        return {
            "success": True,
            "decision": decision.model_dump(),
            "type": "score"
        }
    
    elif req.decision_type == "noul":
        decision = rlcd_engine.decide_noul(project, req.question)
        return {
            "success": True,
            "decision": decision.model_dump(),
            "type": "noul"
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid decision type")

@router.get("/calibration")
async def get_calibration():
    metrics = rlcd_engine.get_calibration_metrics()
    return {
        "success": True,
        "calibration": metrics,
        "policy_versions": rlcd_engine.policy_versions,
        "development_policy": rlcd_engine.development_policy
    }

@router.post("/calibration/temperature")
async def set_temperature(temperature: float):
    rlcd_engine.calibration.update_temperature(temperature)
    return {
        "success": True,
        "temperature": temperature
    }

@router.get("/trajectories")
async def get_all_trajectories():
    trajs = reward_service.get_all_trajectories()
    stats = reward_service.compute_stats()
    return {
        "success": True,
        "trajectories": trajs[-100:],
        "stats": stats
    }

@router.get("/evaluation")
async def get_evaluation():
    calibration = rlcd_engine.get_calibration_metrics()
    reward_stats = reward_service.compute_stats()
    
    return {
        "success": True,
        "evaluation": {
            "decision_accuracy": calibration["accuracy"],
            "calibration_error": calibration["expected_calibration_error"],
            "brier_score": calibration["brier_score"],
            "success_rate": reward_stats["success_rate"],
            "avg_reward": reward_stats["avg_reward"],
            "avg_latency": reward_stats["avg_latency"],
            "total_decisions": calibration["total_samples"],
            "total_trajectories": reward_stats["total"],
            "confidence_buckets": calibration["confidence_buckets"],
            "reliability_data": calibration["reliability_data"],
            "recent_rewards": reward_stats.get("recent_rewards", [])
        }
    }

@router.get("/action-space")
async def get_action_space():
    from ...models.rlcd import ActionSpace
    return {
        "success": True,
        "action_space": [a.value for a in ActionSpace]
    }
