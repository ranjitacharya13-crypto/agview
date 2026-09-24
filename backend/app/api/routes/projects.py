from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from ...services.project_manager import project_manager
from ...services.event_bus import event_bus
from ...models.project_state import ProjectStage
from ...models.events import EventType
from ...agents.master_agent import MasterAgent
from ...agents.research_agent import ResearchAgent
from ...agents.abstract_agent import AbstractAgent, AbstractCritic
from ...agents.solution_architect import SolutionArchitectAgent
from ...agents.frontend_agent import FrontendEngineeringAgent
from ...agents.backend_agent import BackendEngineeringAgent
from ...agents.testing_agent import TestingAgent, DebuggingAgent
from ...agents.presentation_agent import PresentationAgent

router = APIRouter()
master_agent = MasterAgent()

class CreateProjectRequest(BaseModel):
    name: str
    problem_statement: str = ""

class ProblemRequest(BaseModel):
    problem_statement: str

class TaskRequest(BaseModel):
    action: str = "auto"
    query: str = ""
    max_iterations: int = 10
    auto_revise: bool = True
    type: str = "all"

@router.post("/")
async def create_project(req: CreateProjectRequest):
    project = project_manager.create_project(req.name, req.problem_statement)
    return {
        "success": True,
        "project": project.model_dump(mode='json'),
        "project_id": project.project_id
    }

@router.get("/")
async def list_projects():
    projects = project_manager.list_projects()
    return {"success": True, "projects": projects}

@router.get("/{project_id}")
async def get_project(project_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True, "project": project.model_dump(mode='json')}

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    success = project_manager.delete_project(project_id)
    return {"success": success}

@router.post("/{project_id}/problem")
async def set_problem(project_id: str, req: ProblemRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = project_manager.update_problem(project_id, req.problem_statement)
    
    event_bus.emit(
        project_id=project_id,
        event_type=EventType.PROJECT_CREATED,
        message=f"Problem set: {req.problem_statement[:100]}",
        data={"problem": req.problem_statement}
    )
    
    return {"success": True, "project": project.model_dump(mode='json')}

@router.post("/{project_id}/research")
async def research_project(project_id: str, req: TaskRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agent = ResearchAgent()
    result = await agent.execute(project_id, req.model_dump())
    
    return {"success": result["success"], "result": result}

@router.post("/{project_id}/abstract")
async def create_abstract(project_id: str, req: TaskRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agent = AbstractAgent()
    result = await agent.execute(project_id, req.model_dump())
    
    return {"success": result["success"], "result": result}

@router.post("/{project_id}/abstract/critique")
async def critique_abstract(project_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agent = AbstractCritic()
    result = await agent.execute(project_id, {})
    
    return {"success": result["success"], "result": result}

@router.post("/{project_id}/abstract/approve")
async def approve_abstract(project_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.abstract_approved = True
    project.stage = ProjectStage.ABSTRACT_APPROVED
    project_manager.save_project(project)
    
    event_bus.emit(
        project_id=project_id,
        event_type=EventType.ABSTRACT_APPROVED,
        message="Abstract approved by user",
        data={"abstract": project.abstract[:200]}
    )
    
    return {"success": True, "project": project.model_dump(mode='json')}

@router.post("/{project_id}/solution")
async def create_solution(project_id: str, req: TaskRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agent = SolutionArchitectAgent()
    result = await agent.execute(project_id, req.model_dump())
    
    return {"success": result["success"], "result": result}

@router.post("/{project_id}/frontend")
async def create_frontend(project_id: str, req: TaskRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agent = FrontendEngineeringAgent()
    result = await agent.execute(project_id, req.model_dump())
    
    return {"success": result["success"], "result": result}

@router.post("/{project_id}/backend")
async def create_backend(project_id: str, req: TaskRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agent = BackendEngineeringAgent()
    result = await agent.execute(project_id, req.model_dump())
    
    return {"success": result["success"], "result": result}

@router.post("/{project_id}/test")
async def test_project(project_id: str, req: TaskRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agent = TestingAgent()
    result = await agent.execute(project_id, req.model_dump())
    
    return {"success": result["success"], "result": result}

@router.post("/{project_id}/debug")
async def debug_project(project_id: str, req: TaskRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agent = DebuggingAgent()
    result = await agent.execute(project_id, req.model_dump())
    
    return {"success": result["success"], "result": result}

@router.post("/{project_id}/verify")
async def verify_project(project_id: str):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = await master_agent._verify_project(project_id)
    
    return {"success": result["success"], "result": result}

@router.post("/{project_id}/presentation")
async def create_presentation(project_id: str, req: TaskRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agent = PresentationAgent()
    result = await agent.execute(project_id, req.model_dump())
    
    return {"success": result["success"], "result": result}

@router.post("/{project_id}/master")
async def master_execute(project_id: str, req: TaskRequest):
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = await master_agent.execute(project_id, req.model_dump())
    
    return {"success": result.get("success", False), "result": result}

@router.get("/{project_id}/events")
async def get_events(project_id: str, limit: int = 100):
    events = event_bus.get_history(project_id, limit)
    return {
        "success": True,
        "events": [e.to_ws_message() for e in events]
    }

@router.get("/{project_id}/trajectories")
async def get_trajectories(project_id: str):
    from ...services.reward import reward_service
    trajs = reward_service.get_trajectories(project_id)
    stats = reward_service.compute_stats(project_id)
    return {
        "success": True,
        "trajectories": trajs,
        "stats": stats
    }

@router.post("/{project_id}/chat")
async def chat_command(project_id: str, req: TaskRequest):
    """
    Chat + IDE - understands commands like:
    "Create the frontend."
    "Fix this error."
    etc.
    """
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = req.query.lower()
    
    # Intent detection
    if "abstract" in query:
        if "create" in query:
            agent = AbstractAgent()
            result = await agent.execute(project_id, {})
            return {"success": True, "action": "CREATE_ABSTRACT", "result": result}
        elif "approve" in query:
            project.abstract_approved = True
            project.stage = ProjectStage.ABSTRACT_APPROVED
            project_manager.save_project(project)
            return {"success": True, "action": "APPROVE_ABSTRACT"}
    
    elif "research" in query:
        agent = ResearchAgent()
        result = await agent.execute(project_id, {"query": req.query})
        return {"success": True, "action": "RESEARCH", "result": result}
    
    elif "frontend" in query:
        agent = FrontendEngineeringAgent()
        result = await agent.execute(project_id, {})
        return {"success": True, "action": "CREATE_FRONTEND", "result": result}
    
    elif "backend" in query:
        agent = BackendEngineeringAgent()
        result = await agent.execute(project_id, {})
        return {"success": True, "action": "CREATE_BACKEND", "result": result}
    
    elif "test" in query:
        agent = TestingAgent()
        result = await agent.execute(project_id, {})
        return {"success": True, "action": "RUN_TESTS", "result": result}
    
    elif "fix" in query or "error" in query:
        agent = DebuggingAgent()
        result = await agent.execute(project_id, {"error": {"stderr": req.query}})
        return {"success": True, "action": "DEBUG", "result": result}
    
    elif "presentation" in query:
        agent = PresentationAgent()
        result = await agent.execute(project_id, {})
        return {"success": True, "action": "CREATE_PRESENTATION", "result": result}
    
    elif "verify" in query:
        result = await master_agent._verify_project(project_id)
        return {"success": True, "action": "VERIFY", "result": result}
    
    elif "run" in query and "app" in query:
        from ...services.terminal import terminal_service
        result = terminal_service.execute(project_id, "npm run dev", "")
        return {"success": True, "action": "RUN_APP", "result": result}
    
    else:
        # Default to master agent auto
        result = await master_agent.execute(project_id, {"action": "auto", "max_iterations": 3})
        return {"success": True, "action": "AUTO", "result": result, "query": req.query}
