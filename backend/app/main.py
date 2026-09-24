from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import asyncio
import json
from typing import Dict, List

from .config import settings
from .api.routes import projects, rlcd, filesystem, terminal, agents, git, export
from .services.event_bus import event_bus
from .models.events import ProjectEvent

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="RLCD Agentic Engineering IDE - AI-native VS Code-style development environment"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(rlcd.router, prefix="/api/rlcd", tags=["rlcd"])
app.include_router(filesystem.router, prefix="/api/filesystem", tags=["filesystem"])
app.include_router(terminal.router, prefix="/api/terminal", tags=["terminal"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(git.router, prefix="/api/git", tags=["git"])
app.include_router(export.router, prefix="/api/export", tags=["export"])

# WebSocket manager
class WSManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        if project_id not in self.connections:
            self.connections[project_id] = []
        self.connections[project_id].append(websocket)
        
        # Subscribe to event bus
        def event_callback(event: ProjectEvent):
            # Schedule broadcast
            asyncio.create_task(self.broadcast(project_id, event.to_ws_message()))
        
        event_bus.subscribe(project_id, event_callback)
    
    def disconnect(self, project_id: str, websocket: WebSocket):
        if project_id in self.connections:
            if websocket in self.connections[project_id]:
                self.connections[project_id].remove(websocket)
    
    async def broadcast(self, project_id: str, message: Dict):
        if project_id in self.connections:
            for ws in self.connections[project_id][:]:
                try:
                    await ws.send_text(json.dumps(message))
                except:
                    # Remove dead connections
                    if ws in self.connections[project_id]:
                        self.connections[project_id].remove(ws)

ws_manager = WSManager()

@app.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await ws_manager.connect(project_id, websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # Echo or handle commands
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(project_id, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(project_id, websocket)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.version,
        "app": settings.app_name,
        "workspace_root": str(settings.workspace_root),
        "projects_count": len(list(settings.projects_root.glob("*.json")))
    }

@app.get("/api/stats")
async def get_stats():
    from .services.reward import reward_service
    from .services.rlcd_engine import rlcd_engine
    
    projects_list = list(settings.projects_root.glob("*.json"))
    
    return {
        "projects_count": len(projects_list),
        "trajectories": reward_service.compute_stats(),
        "calibration": rlcd_engine.get_calibration_metrics(),
        "workspace": str(settings.workspace_root)
    }

# Serve frontend static files if built
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

@app.get("/")
async def root():
    # Check if frontend exists
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    
    return {
        "name": settings.app_name,
        "version": settings.version,
        "message": "RLCD Agentic Engineering IDE Backend",
        "docs": "/docs",
        "health": "/api/health",
        "frontend": "Frontend not built yet - run 'npm run build' in frontend/",
        "endpoints": {
            "projects": "/api/projects",
            "rlcd": "/api/rlcd",
            "filesystem": "/api/filesystem",
            "terminal": "/api/terminal",
            "agents": "/api/agents"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port, reload=True)
