from fastapi import APIRouter
from ...services.model_provider import model_registry

router = APIRouter()

@router.get("/")
async def list_agents():
    agents = [
        {
            "id": "master_agent",
            "name": "Master Agent",
            "description": "Orchestrates all other agents, understands project state, calls RLCD engine",
            "capabilities": ["orchestration", "decision_making", "project_memory"],
            "status": "active"
        },
        {
            "id": "research_agent",
            "name": "Research Agent",
            "description": "Web search, source collection, technical research, technology discovery",
            "capabilities": ["web_search", "source_collection", "technical_research"],
            "status": "active"
        },
        {
            "id": "abstract_agent",
            "name": "Abstract Agent",
            "description": "Professional abstract generation with critique and revision loop",
            "capabilities": ["technical_writing", "long_context", "critique"],
            "status": "active"
        },
        {
            "id": "solution_architect",
            "name": "Solution Architect",
            "description": "Requirements, architecture, technology stack, data flow, API design",
            "capabilities": ["architecture", "requirements", "system_design"],
            "status": "active"
        },
        {
            "id": "frontend_agent",
            "name": "Frontend Engineering Agent",
            "description": "Autonomous frontend development with real file operations, build, test, fix loop",
            "capabilities": ["code_generation", "repository_reasoning", "tool_use", "debugging", "browser_verification"],
            "status": "active"
        },
        {
            "id": "backend_agent",
            "name": "Backend Engineering Agent",
            "description": "API design, database, authentication, business logic, testing",
            "capabilities": ["api_design", "database_design", "authentication", "business_logic"],
            "status": "active"
        },
        {
            "id": "testing_agent",
            "name": "Testing Agent",
            "description": "Unit, integration, API, frontend, browser, database testing",
            "capabilities": ["unit_testing", "integration_testing", "browser_testing"],
            "status": "active"
        },
        {
            "id": "debugging_agent",
            "name": "Debugging Agent",
            "description": "Error collection, root cause analysis, patch, test, verify",
            "capabilities": ["debugging", "error_analysis", "patch_generation"],
            "status": "active"
        },
        {
            "id": "presentation_agent",
            "name": "Presentation Agent",
            "description": "Generates presentations from actual project artifacts with speaker notes",
            "capabilities": ["presentation", "documentation", "technical_writing"],
            "status": "active"
        },
        {
            "id": "visual_review_agent",
            "name": "Visual Review Agent",
            "description": "Inspects screenshots for layout, spacing, visual defects",
            "capabilities": ["visual_review", "ui_testing"],
            "status": "active"
        }
    ]
    
    return {"success": True, "agents": agents}

@router.get("/models")
async def list_models():
    providers = model_registry.list_providers()
    return {"success": True, "providers": providers}

@router.get("/capabilities")
async def list_capabilities():
    capabilities = [
        "long_context",
        "code_generation",
        "repository_reasoning",
        "tool_use",
        "debugging",
        "technical_writing",
        "web_search",
        "orchestration",
        "architecture",
        "presentation"
    ]
    return {"success": True, "capabilities": capabilities}
