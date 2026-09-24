from typing import Dict, Any, List
import uuid
from .base_agent import BaseAgent
from ..models.events import EventType
from ..models.project_state import ProjectStage
import random
from datetime import datetime

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("research_agent", ["long_context", "technical_writing", "tool_use"])
    
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        
        self.emit_event(project_id, EventType.RESEARCH_STARTED, f"Research started for: {project.problem_statement[:50]}")
        self.emit_event(project_id, EventType.AGENT_STARTED, "Research agent activated", data={"task": task})
        
        query = task.get("query", project.problem_statement)
        
        # Simulate research - in real implementation would use web_search
        # For development, generate mock research with sources
        
        research_results = await self._perform_research(project_id, query)
        
        # Save to project - convert to ResearchItem
        from ..models.project_state import ResearchItem
        for item in research_results:
            try:
                research_item = ResearchItem(**item)
                project.research.append(research_item)
            except Exception as e:
                print(f"Failed to create ResearchItem: {e}, using dict")
                project.research.append(item)  # fallback
            
            self.project_manager.add_memory(project_id, "RESEARCH", {
                "query": query,
                "result": item,
                "agent": self.name
            })
        
        project.stage = ProjectStage.ABSTRACT_GENERATION
        self.save_project(project)
        
        self.emit_event(
            project_id, 
            EventType.RESEARCH_COMPLETED, 
            f"Research completed with {len(research_results)} sources",
            data={"count": len(research_results), "results": research_results[:3]}
        )
        
        return {
            "success": True,
            "research": research_results,
            "count": len(research_results)
        }
    
    async def _perform_research(self, project_id: str, query: str) -> List[Dict[str, Any]]:
        # Mock research that would normally use web_search tool
        # Generate realistic research items
        
        base_topics = [
            "smart greenhouse technology",
            "IoT agriculture monitoring",
            "automated irrigation systems",
            "precision farming",
            "environmental sensors"
        ]
        
        results = []
        for i, topic in enumerate(base_topics[:3]):
            # Simulate web search result
            prompt = f"Research {topic} for query: {query}. Provide sources and claims."
            content = await self.model_provider.generate(prompt, system="You are a research assistant. Provide factual research with sources.")
            
            result = {
                "id": str(uuid.uuid4())[:8],
                "query": query,
                "source": "web_search",
                "url": f"https://example.com/research/{topic.replace(' ', '-')}-{i}",
                "title": f"{topic.title()} - State of the Art 2024",
                "claim": f"{topic} enables efficient monitoring and automation in agricultural systems",
                "confidence": round(random.uniform(0.7, 0.95), 2),
                "date": datetime.now().isoformat(),
                "content": content[:500]
            }
            results.append(result)
            
            self.emit_event(
                project_id,
                EventType.RESEARCH_COMPLETED,
                f"Found source: {result['title']}",
                data={"source": result}
            )
        
        return results

class WebSearchTool:
    """Tool for web search - would integrate with real search API"""
    
    @staticmethod
    async def search(query: str, count: int = 5) -> List[Dict[str, Any]]:
        # Mock implementation - in production would use Tavily, Serper, etc.
        # For now return mock results
        return [
            {
                "url": f"https://example.com/{i}",
                "title": f"Result {i} for {query}",
                "snippet": f"Information about {query}...",
                "date": "2024-01-01"
            }
            for i in range(count)
        ]
