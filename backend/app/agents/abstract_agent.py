from typing import Dict, Any
import uuid
from .base_agent import BaseAgent
from ..models.events import EventType
from ..models.project_state import ProjectStage, Requirement

class AbstractAgent(BaseAgent):
    def __init__(self):
        super().__init__("abstract_agent", ["technical_writing", "long_context"])
    
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        
        self.emit_event(project_id, EventType.ABSTRACT_STARTED, "Abstract generation started")
        self.emit_event(project_id, EventType.AGENT_STARTED, "Abstract agent activated")
        
        problem = project.problem_statement
        research = project.research
        
        # Build prompt for abstract generation - handle both dict and object
        def get_research_field(r, field, default=""):
            if isinstance(r, dict):
                return r.get(field, default)
            return getattr(r, field, default)
        
        research_context = "\n".join([f"- {get_research_field(r, 'title')}: {get_research_field(r, 'claim')} (Source: {get_research_field(r, 'url')})" for r in research[:5]])
        
        prompt = f"""
        Generate a professional abstract for this project:

        PROBLEM STATEMENT:
        {problem}

        RESEARCH CONTEXT:
        {research_context}

        Create a clean professional abstract with structure:
        - TITLE
        - ABSTRACT (150-300 words)
        - Problem
        - Existing limitation
        - Proposed solution
        - Methodology
        - Technology
        - Expected impact

        Do NOT add watermarks or branding. Clean professional output only.
        """
        
        system = "You are a professional technical writer. Create high-quality abstracts for hackathon projects. Be concise, technical, and professional."
        
        abstract_text = await self.model_provider.generate(prompt, system=system)
        
        # Save abstract
        project.abstract = abstract_text
        project.stage = ProjectStage.ABSTRACT_REVIEW
        
        # Extract structured requirements from abstract
        requirements = await self._extract_requirements(project_id, abstract_text, problem)
        
        # Add requirements to project
        for req_data in requirements:
            req = Requirement(
                title=req_data["title"],
                description=req_data["description"],
                type=req_data.get("type", "feature"),
                priority=req_data.get("priority", "medium"),
                source="abstract"
            )
            project.requirements.append(req)
        
        # Extract actors, features, screens
        extraction = await self._extract_structured_info(abstract_text)
        project.actors = extraction.get("actors", [])
        project.features = extraction.get("features", [])
        project.screens = extraction.get("screens", [])
        
        self.save_project(project)
        
        self.project_manager.add_memory(project_id, "ABSTRACT", {
            "abstract": abstract_text,
            "requirements": requirements,
            "extraction": extraction,
            "agent": self.name
        })
        
        self.emit_event(
            project_id,
            EventType.ABSTRACT_GENERATED,
            "Abstract generated successfully",
            data={
                "abstract": abstract_text[:500],
                "requirements_count": len(requirements),
                "actors": project.actors,
                "features": project.features
            }
        )
        
        return {
            "success": True,
            "abstract": abstract_text,
            "requirements": requirements,
            "extraction": extraction
        }
    
    async def _extract_requirements(self, project_id: str, abstract: str, problem: str) -> list:
        prompt = f"""
        From this abstract, extract structured project requirements:

        ABSTRACT:
        {abstract}

        PROBLEM:
        {problem}

        Extract as JSON array of requirements with fields:
        - title
        - description
        - type (feature, actor, workflow, entity, screen, constraint)
        - priority (high, medium, low)

        Example:
        [
          {{"title": "Crop Monitoring", "description": "Farmers can monitor crop health", "type": "feature", "priority": "high"}},
          {{"title": "Farmer", "description": "Primary user who monitors crops", "type": "actor", "priority": "high"}}
        ]

        Return ONLY valid JSON array.
        """
        
        try:
            result = await self.model_provider.generate(prompt, system="Extract structured requirements as JSON")
            # Try to parse JSON
            import json
            # Extract JSON from markdown
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            requirements = json.loads(result)
            if isinstance(requirements, list):
                return requirements
        except Exception as e:
            print(f"Requirement extraction error: {e}")
        
        # Fallback heuristic extraction
        fallback = [
            {"title": "Dashboard", "description": "Main dashboard for monitoring", "type": "screen", "priority": "high"},
            {"title": "Real-time Monitoring", "description": "Real-time data visualization", "type": "feature", "priority": "high"},
            {"title": "User Management", "description": "User authentication and profiles", "type": "feature", "priority": "medium"},
            {"title": "Alerts", "description": "Notification system for critical events", "type": "feature", "priority": "high"},
            {"title": "Analytics", "description": "Data analytics and reporting", "type": "feature", "priority": "medium"},
        ]
        
        # Try to infer from abstract keywords
        abstract_lower = abstract.lower()
        if "temperature" in abstract_lower or "humidity" in abstract_lower:
            fallback.append({"title": "Environmental Monitoring", "description": "Monitor temperature, humidity, soil moisture", "type": "feature", "priority": "high"})
        if "irrigation" in abstract_lower:
            fallback.append({"title": "Irrigation Control", "description": "Automated irrigation system", "type": "feature", "priority": "high"})
        
        return fallback
    
    async def _extract_structured_info(self, abstract: str) -> Dict[str, Any]:
        # Heuristic extraction for actors, features, screens
        abstract_lower = abstract.lower()
        
        actors = ["User"]
        if "farmer" in abstract_lower:
            actors.append("Farmer")
        if "admin" in abstract_lower:
            actors.append("Administrator")
        if "doctor" in abstract_lower or "health" in abstract_lower:
            actors.extend(["Patient", "Doctor"])
        if "greenhouse" in abstract_lower:
            actors.extend(["Farmer", "Agronomist"])
        
        features = []
        feature_keywords = {
            "monitoring": "Real-time Monitoring",
            "dashboard": "Dashboard",
            "alert": "Alerts & Notifications",
            "irrigation": "Irrigation Control",
            "analytics": "Analytics",
            "authentication": "Authentication",
            "sensor": "Sensor Management",
            "temperature": "Temperature Monitoring",
            "humidity": "Humidity Monitoring"
        }
        
        for keyword, feature in feature_keywords.items():
            if keyword in abstract_lower:
                features.append(feature)
        
        if not features:
            features = ["Dashboard", "Monitoring", "Analytics", "Settings"]
        
        screens = ["Dashboard", "Analytics", "Settings"]
        if "monitor" in abstract_lower:
            screens.append("Monitoring")
        if "irrigation" in abstract_lower:
            screens.append("Irrigation")
        if "crop" in abstract_lower or "greenhouse" in abstract_lower:
            screens.extend(["Crops", "Sensors"])
        if "appointment" in abstract_lower or "health" in abstract_lower:
            screens.extend(["Appointments", "Patients", "Doctors"])
        
        # Deduplicate
        actors = list(set(actors))
        features = list(set(features))
        screens = list(set(screens))
        
        return {
            "actors": actors,
            "features": features,
            "screens": screens
        }

class AbstractCritic(BaseAgent):
    def __init__(self):
        super().__init__("abstract_critic", ["technical_writing", "long_context"])
    
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        if not project or not project.abstract:
            return {"success": False, "error": "No abstract to critique"}
        
        self.emit_event(project_id, EventType.AGENT_STARTED, "Abstract critic evaluating")
        
        prompt = f"""
        Critique this abstract for quality:

        ABSTRACT:
        {project.abstract}

        PROBLEM:
        {project.problem_statement}

        Evaluate:
        - clarity
        - technical correctness
        - coherence
        - relevance
        - naturalness
        - source grounding
        - problem alignment
        - solution alignment
        - unsupported claims

        Return JSON:
        {{
            "quality": 0.0-1.0,
            "needs_revision": true/false,
            "issues": ["issue1", "issue2"],
            "clarity": 0.0-1.0,
            "technical_correctness": 0.0-1.0,
            "coherence": 0.0-1.0
        }}
        """
        
        try:
            result = await self.model_provider.structured_output(
                prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "quality": {"type": "number"},
                        "needs_revision": {"type": "boolean"},
                        "issues": {"type": "array", "items": {"type": "string"}},
                        "clarity": {"type": "number"},
                        "technical_correctness": {"type": "number"},
                        "coherence": {"type": "number"}
                    }
                },
                system="You are an abstract critic. Be rigorous but fair."
            )
        except:
            # Fallback heuristic
            abstract_len = len(project.abstract)
            quality = 0.8 if 150 <= abstract_len <= 2000 else 0.5
            result = {
                "quality": quality,
                "needs_revision": quality < 0.7,
                "issues": [] if quality >= 0.7 else ["Abstract too short or too long", "Needs more technical detail"],
                "clarity": quality,
                "technical_correctness": quality,
                "coherence": quality
            }
        
        self.emit_event(
            project_id,
            EventType.ABSTRACT_GENERATED,
            f"Abstract critique: quality={result.get('quality', 0):.2f}, needs_revision={result.get('needs_revision', False)}",
            data=result
        )
        
        return {
            "success": True,
            "critique": result,
            "quality": result.get("quality", 0.0),
            "needs_revision": result.get("needs_revision", False)
        }
