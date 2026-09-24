from typing import Dict, Any
from .base_agent import BaseAgent
from ..models.events import EventType
from ..models.project_state import ProjectStage
import json

class SolutionArchitectAgent(BaseAgent):
    def __init__(self):
        super().__init__("solution_architect", ["long_context", "repository_reasoning", "technical_writing"])
    
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        
        self.emit_event(project_id, EventType.AGENT_STARTED, "Solution architect generating architecture")
        
        # Build context
        problem = project.problem_statement
        abstract = project.abstract
        def get_field(obj, field, default=""):
            if isinstance(obj, dict):
                return obj.get(field, default)
            return getattr(obj, field, default)
        
        requirements = [f"{get_field(r, 'title')}: {get_field(r, 'description')}" for r in project.requirements]
        research = [f"{get_field(r, 'title')}: {get_field(r, 'claim')}" for r in project.research[:3]]
        
        prompt = f"""
        Design solution architecture for:

        PROBLEM: {problem}

        ABSTRACT: {abstract[:1000]}

        REQUIREMENTS:
        {chr(10).join(requirements[:10])}

        RESEARCH:
        {chr(10).join(research)}

        Generate architecture JSON with:
        - requirements (functional, non_functional)
        - architecture (frontend, backend, database, deployment)
        - technology_stack (frontend, backend, tools)
        - data_flow
        - api_requirements (list of endpoints)
        - database_requirements (tables, relationships)
        - security_requirements
        - deployment_requirements

        Be specific and technical. Choose modern stack.
        """
        
        system = "You are a solution architect. Design scalable, modern architectures. Prefer React + FastAPI or similar modern stacks."
        
        try:
            arch_text = await self.model_provider.generate(prompt, system=system)
            # Try to extract JSON
            if "```json" in arch_text:
                arch_text = arch_text.split("```json")[1].split("```")[0]
            elif "```" in arch_text:
                arch_text = arch_text.split("```")[1].split("```")[0]
            
            architecture = json.loads(arch_text)
        except Exception as e:
            print(f"Architecture parsing error: {e}, using fallback")
            # Fallback architecture based on problem type
            is_greenhouse = "greenhouse" in problem.lower() or "temperature" in problem.lower() or "humidity" in problem.lower()
            is_healthcare = "health" in problem.lower() or "appointment" in problem.lower()
            
            if is_greenhouse:
                architecture = {
                    "requirements": {
                        "functional": [
                            "Real-time temperature monitoring",
                            "Humidity tracking",
                            "Soil moisture monitoring",
                            "Automated irrigation control",
                            "Alert system",
                            "Analytics dashboard"
                        ],
                        "non_functional": ["Responsive UI", "Real-time updates", "Secure", "Scalable"]
                    },
                    "architecture": {
                        "frontend": "React SPA with Recharts for visualization, WebSocket for live data",
                        "backend": "FastAPI with WebSocket support, background tasks for sensor polling",
                        "database": "PostgreSQL with TimescaleDB extension for time-series",
                        "deployment": "Docker Compose with Nginx"
                    },
                    "technology_stack": {
                        "frontend": ["React 18", "TypeScript", "Vite", "Tailwind CSS", "Recharts", "Lucide Icons", "Zustand"],
                        "backend": ["FastAPI", "PostgreSQL", "SQLAlchemy", "Pydantic", "WebSockets", "MQTT"],
                        "tools": ["Vite", "Playwright", "Pytest", "Docker"]
                    },
                    "data_flow": "Sensors -> MQTT Broker -> FastAPI -> WebSocket -> React Frontend -> User",
                    "api_requirements": [
                        "GET /api/sensors - list sensors",
                        "GET /api/sensors/{id}/readings - sensor data",
                        "POST /api/irrigation/control - control irrigation",
                        "GET /api/analytics - analytics data",
                        "WebSocket /ws/realtime - real-time updates"
                    ],
                    "database_requirements": {
                        "tables": ["users", "sensors", "readings", "irrigation_logs", "alerts"],
                        "relationships": "sensors 1-N readings, users 1-N alerts"
                    },
                    "security_requirements": ["JWT Authentication", "Input validation", "Rate limiting", "CORS"],
                    "deployment_requirements": ["Docker", "Nginx reverse proxy", "Environment variables"]
                }
            elif is_healthcare:
                architecture = {
                    "requirements": {
                        "functional": [
                            "Patient registration",
                            "Doctor management",
                            "Appointment scheduling",
                            "Real-time availability",
                            "Notifications",
                            "Medical records"
                        ],
                        "non_functional": ["HIPAA compliant", "Responsive", "Secure", "Scalable"]
                    },
                    "architecture": {
                        "frontend": "React with calendar components, role-based UI",
                        "backend": "FastAPI with appointment logic, notification service",
                        "database": "PostgreSQL with appointment scheduling",
                        "deployment": "Docker with HTTPS"
                    },
                    "technology_stack": {
                        "frontend": ["React", "TypeScript", "Tailwind", "React Big Calendar"],
                        "backend": ["FastAPI", "PostgreSQL", "SQLAlchemy"],
                        "tools": ["Vite", "Docker"]
                    },
                    "data_flow": "User -> React -> FastAPI -> PostgreSQL -> Notification Service",
                    "api_requirements": [
                        "POST /api/appointments",
                        "GET /api/doctors/availability",
                        "GET /api/patients",
                        "WebSocket /ws/notifications"
                    ],
                    "database_requirements": {
                        "tables": ["users", "doctors", "patients", "appointments", "medical_records"],
                        "relationships": "doctors 1-N appointments, patients 1-N appointments"
                    },
                    "security_requirements": ["JWT", "Role-based access", "Data encryption"],
                    "deployment_requirements": ["Docker", "HTTPS", "Backup"]
                }
            else:
                architecture = {
                    "requirements": {
                        "functional": ["Dashboard", "Data management", "User authentication", "Analytics"],
                        "non_functional": ["Responsive", "Secure", "Fast"]
                    },
                    "architecture": {
                        "frontend": "React SPA",
                        "backend": "FastAPI REST API",
                        "database": "PostgreSQL",
                        "deployment": "Docker"
                    },
                    "technology_stack": {
                        "frontend": ["React", "TypeScript", "Tailwind"],
                        "backend": ["FastAPI", "PostgreSQL"],
                        "tools": ["Vite"]
                    },
                    "data_flow": "Frontend -> Backend API -> Database",
                    "api_requirements": ["/api/data", "/api/users", "/api/analytics"],
                    "database_requirements": {
                        "tables": ["users", "data", "logs"],
                        "relationships": "users 1-N data"
                    },
                    "security_requirements": ["JWT", "Validation"],
                    "deployment_requirements": ["Docker"]
                }
        
        # Save to project
        project.solution = architecture
        project.tech_stack = architecture.get("technology_stack", {})
        project.stage = ProjectStage.ARCHITECTURE
        self.save_project(project)
        
        self.project_manager.add_memory(project_id, "ARCHITECTURE", {
            "architecture": architecture,
            "agent": self.name
        })
        
        self.emit_event(
            project_id,
            EventType.AGENT_COMPLETED,
            "Solution architecture generated",
            data={"architecture": architecture}
        )
        
        return {
            "success": True,
            "architecture": architecture
        }
