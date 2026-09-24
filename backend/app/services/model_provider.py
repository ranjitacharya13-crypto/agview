from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
import json
import os
import httpx
from ..config import settings

class ModelProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        pass
    
    @abstractmethod
    async def structured_output(self, prompt: str, schema: Dict[str, Any], system: str = "") -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        pass

class MockProvider(ModelProvider):
    """Development mock provider that generates deterministic outputs"""
    
    def get_capabilities(self) -> List[str]:
        return ["long_context", "code_generation", "repository_reasoning", "tool_use", "debugging", "technical_writing"]
    
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        # Simple mock that returns based on prompt keywords
        prompt_lower = prompt.lower()
        
        if "abstract" in prompt_lower:
            return """# Smart Greenhouse Monitoring System

## Abstract
This project presents an intelligent greenhouse monitoring and automation system that addresses critical challenges in modern agriculture. Traditional greenhouse management relies on manual monitoring, leading to inefficiencies and crop losses.

**Problem:** Farmers struggle with maintaining optimal growing conditions due to lack of real-time monitoring of temperature, humidity, soil moisture, and automated irrigation control.

**Existing Limitations:** Current solutions are expensive, lack integration, require technical expertise, and don't provide predictive insights.

**Proposed Solution:** A comprehensive IoT-enabled web platform that monitors environmental parameters in real-time, provides automated irrigation control, and delivers actionable insights through an intuitive dashboard.

**Methodology:** The system employs sensor networks for data collection, a cloud-based backend for processing, machine learning for predictive analytics, and a responsive frontend for visualization and control.

**Technology:** React frontend with real-time charts, FastAPI backend, PostgreSQL for data storage, WebSocket for live updates, and MQTT for sensor communication.

**Expected Impact:** 30% reduction in water usage, 25% increase in crop yield, and significant reduction in manual monitoring effort, making precision agriculture accessible to small and medium farmers.
"""
        
        if "architecture" in prompt_lower or "solution" in prompt_lower:
            return json.dumps({
                "requirements": {
                    "functional": ["Real-time monitoring", "Automated irrigation", "Alerts", "Analytics dashboard"],
                    "non_functional": ["Responsive", "Secure", "Scalable"]
                },
                "architecture": {
                    "frontend": "React + TypeScript + Tailwind + Recharts",
                    "backend": "FastAPI + PostgreSQL + WebSockets",
                    "deployment": "Docker + Nginx"
                },
                "technology_stack": {
                    "frontend": ["React", "TypeScript", "Tailwind CSS", "Recharts", "Lucide Icons"],
                    "backend": ["FastAPI", "PostgreSQL", "SQLAlchemy", "WebSockets"],
                    "tools": ["Vite", "Playwright", "Pytest"]
                },
                "data_flow": "Sensors -> MQTT -> Backend -> WebSocket -> Frontend",
                "api_requirements": ["/api/sensors", "/api/irrigation", "/api/analytics"],
                "database": {"tables": ["sensors", "readings", "irrigation_logs", "users"]},
                "security": ["JWT Auth", "Input validation", "Rate limiting"]
            }, indent=2)
        
        if "frontend" in prompt_lower:
            return "Frontend code generation request acknowledged - will create components"
        
        return f"Mock response for: {prompt[:100]}..."
    
    async def structured_output(self, prompt: str, schema: Dict[str, Any], system: str = "") -> Dict[str, Any]:
        # Return mock structured data based on schema keys
        result = {}
        for key in schema.get("properties", {}).keys():
            if "title" in key.lower():
                result[key] = "Smart Greenhouse Monitoring System"
            elif "abstract" in key.lower():
                result[key] = await self.generate("abstract " + prompt)
            elif "quality" in key.lower():
                result[key] = 0.85
            elif "needs_revision" in key.lower():
                result[key] = False
            elif "issues" in key.lower():
                result[key] = []
            else:
                result[key] = "mock_value"
        return result

class OpenAICompatibleProvider(ModelProvider):
    def __init__(self, api_key: str = "", base_url: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    def get_capabilities(self) -> List[str]:
        return ["long_context", "code_generation", "technical_writing", "tool_use"]
    
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        if not self.api_key:
            # Fallback to mock
            mock = MockProvider()
            return await mock.generate(prompt, system, **kwargs)
        
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2000)
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI provider error: {e}, falling back to mock")
            mock = MockProvider()
            return await mock.generate(prompt, system, **kwargs)
    
    async def structured_output(self, prompt: str, schema: Dict[str, Any], system: str = "") -> Dict[str, Any]:
        content = await self.generate(
            f"{prompt}\n\nReturn JSON matching this schema: {json.dumps(schema)}",
            system
        )
        try:
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
        except:
            mock = MockProvider()
            return await mock.structured_output(prompt, schema, system)

class ModelRegistry:
    def __init__(self):
        self.providers: Dict[str, ModelProvider] = {
            "mock": MockProvider(),
            "openai": OpenAICompatibleProvider(),
        }
        self.capability_map: Dict[str, List[str]] = {}
        self._build_capability_map()
    
    def _build_capability_map(self):
        for name, provider in self.providers.items():
            caps = provider.get_capabilities()
            for cap in caps:
                if cap not in self.capability_map:
                    self.capability_map[cap] = []
                self.capability_map[cap].append(name)
    
    def get_provider(self, name: str = None) -> ModelProvider:
        if not name or name not in self.providers:
            # Check env
            if settings.openai_api_key:
                return self.providers["openai"]
            return self.providers["mock"]
        return self.providers[name]
    
    def route_by_capability(self, required_capabilities: List[str]) -> ModelProvider:
        # Find provider that matches most capabilities
        best_provider = None
        best_score = -1
        
        for name, provider in self.providers.items():
            caps = provider.get_capabilities()
            score = sum(1 for rc in required_capabilities if rc in caps)
            if score > best_score:
                best_score = score
                best_provider = provider
        
        return best_provider or self.providers["mock"]
    
    def list_providers(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": name,
                "capabilities": provider.get_capabilities(),
                "available": True
            }
            for name, provider in self.providers.items()
        ]

model_registry = ModelRegistry()
