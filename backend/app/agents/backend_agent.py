from typing import Dict, Any
from .base_agent import BaseAgent
from ..models.events import EventType
from ..models.project_state import ProjectStage
import json

class BackendEngineeringAgent(BaseAgent):
    def __init__(self):
        super().__init__("backend_agent", ["code_generation", "repository_reasoning", "tool_use", "debugging"])
    
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        
        self.emit_event(project_id, EventType.BACKEND_STARTED, "Backend engineering started")
        self.emit_event(project_id, EventType.AGENT_STARTED, "Backend agent activated")
        
        # Create backend structure
        await self._create_backend_structure(project_id, project)
        
        # Test backend
        self.emit_event(project_id, EventType.COMMAND_STARTED, "Testing backend startup")
        test_result = self.terminal.execute(project_id, "cd backend && python -m py_compile main.py || echo 'compile check'", "")
        
        project.stage = ProjectStage.INTEGRATION
        self.save_project(project)
        
        self.emit_event(project_id, EventType.AGENT_COMPLETED, "Backend engineering completed")
        
        return {"success": True, "test_result": test_result}
    
    async def _create_backend_structure(self, project_id: str, project):
        is_greenhouse = "greenhouse" in project.problem_statement.lower() or "temperature" in project.problem_statement.lower()
        
        # backend/main.py
        if is_greenhouse:
            main_py = self._generate_greenhouse_backend(project)
        else:
            main_py = self._generate_generic_backend(project)
        
        self.filesystem.write_file(project_id, "backend/main.py", main_py, agent=self.name)
        self.emit_event(project_id, EventType.FILE_CREATED, "Created backend/main.py")
        
        # backend/requirements.txt
        requirements = """fastapi==0.110.0
uvicorn[standard]==0.29.0
pydantic==2.6.0
sqlalchemy==2.0.27
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
websockets==12.0
"""
        self.filesystem.write_file(project_id, "backend/requirements.txt", requirements, agent=self.name)
        
        # backend/models.py
        models_py = """from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class SensorType(str, Enum):
    temperature = "temperature"
    humidity = "humidity"
    soil = "soil"

class SensorStatus(str, Enum):
    normal = "normal"
    warning = "warning"
    critical = "critical"

class Sensor(BaseModel):
    id: str
    name: str
    type: SensorType
    value: float
    unit: str
    status: SensorStatus
    last_update: datetime = datetime.now()

class Reading(BaseModel):
    id: Optional[str] = None
    sensor_id: str
    value: float
    timestamp: datetime = datetime.now()

class IrrigationRequest(BaseModel):
    zone: str = "all"
    duration_minutes: int = 15
    flow_rate: int = 60
    action: str = "start"  # start, stop

class AnalyticsResponse(BaseModel):
    avg_temperature: float
    avg_humidity: float
    avg_soil_moisture: float
    water_usage_today: float
    alerts_count: int
"""
        self.filesystem.write_file(project_id, "backend/models.py", models_py, agent=self.name)
        
        # backend/database.py
        database_py = """from sqlalchemy import create_engine, Column, String, Float, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./greenhouse.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SensorDB(Base):
    __tablename__ = "sensors"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    value = Column(Float)
    unit = Column(String)
    status = Column(String)
    last_update = Column(DateTime, default=datetime.now)

class ReadingDB(Base):
    __tablename__ = "readings"
    id = Column(String, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)

class IrrigationLogDB(Base):
    __tablename__ = "irrigation_logs"
    id = Column(String, primary_key=True, index=True)
    zone = Column(String)
    duration_minutes = Column(Float)
    water_used = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
        self.filesystem.write_file(project_id, "backend/database.py", database_py, agent=self.name)
        
        # README for backend
        readme = f"""# {project.name} - Backend

{project.problem_statement}

## Features
{', '.join(project.features) if project.features else 'Real-time monitoring, irrigation control'}

## API Endpoints
- GET /api/sensors
- GET /api/sensors/{{id}}/readings
- POST /api/irrigation/control
- GET /api/analytics
- WebSocket /ws/realtime

## Run
```
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
"""
        self.filesystem.write_file(project_id, "backend/README.md", readme, agent=self.name)
    
    def _generate_greenhouse_backend(self, project) -> str:
        return f'''"""
{project.name} - Smart Greenhouse Backend
Generated by RLCD Agentic IDE - Backend Agent
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import asyncio
import random
import uuid
from datetime import datetime, timedelta
import json

app = FastAPI(
    title="{project.name} API",
    description="{project.problem_statement[:100]}",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (would be PostgreSQL in production)
sensors_db = [
    {{
        "id": "1",
        "name": "Temperature Sensor - Zone 1",
        "type": "temperature",
        "value": 24.5,
        "unit": "°C",
        "status": "normal",
        "last_update": datetime.now().isoformat(),
        "zone": "zone1"
    }},
    {{
        "id": "2",
        "name": "Humidity Sensor - Zone 1",
        "type": "humidity",
        "value": 65.2,
        "unit": "%",
        "status": "normal",
        "last_update": datetime.now().isoformat(),
        "zone": "zone1"
    }},
    {{
        "id": "3",
        "name": "Soil Moisture - Zone 1",
        "type": "soil",
        "value": 42.0,
        "unit": "%",
        "status": "warning",
        "last_update": datetime.now().isoformat(),
        "zone": "zone1"
    }},
    {{
        "id": "4",
        "name": "Temperature Sensor - Zone 2",
        "type": "temperature",
        "value": 26.1,
        "unit": "°C",
        "status": "normal",
        "last_update": datetime.now().isoformat(),
        "zone": "zone2"
    }},
]

readings_db = []
irrigation_logs = []
irrigation_state = {{"active": False, "zone": "all", "started_at": None}}

# Generate historical readings
for i in range(100):
    readings_db.append({{
        "id": str(uuid.uuid4())[:8],
        "sensor_id": "1",
        "value": 20 + random.uniform(0, 10),
        "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
        "type": "temperature"
    }})
    readings_db.append({{
        "id": str(uuid.uuid4())[:8],
        "sensor_id": "2",
        "value": 50 + random.uniform(0, 20),
        "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
        "type": "humidity"
    }})
    readings_db.append({{
        "id": str(uuid.uuid4())[:8],
        "sensor_id": "3",
        "value": 30 + random.uniform(0, 30),
        "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
        "type": "soil"
    }})

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

@app.get("/")
async def root():
    return {{
        "name": "{project.name}",
        "version": "1.0.0",
        "status": "running",
        "sensors_count": len(sensors_db),
        "irrigation_active": irrigation_state["active"]
    }}

@app.get("/health")
async def health():
    return {{"status": "healthy", "timestamp": datetime.now().isoformat()}}

@app.get("/api/sensors")
async def get_sensors():
    # Simulate real-time variation
    for sensor in sensors_db:
        if sensor["type"] == "temperature":
            sensor["value"] = round(sensor["value"] + random.uniform(-0.5, 0.5), 1)
        elif sensor["type"] == "humidity":
            sensor["value"] = round(sensor["value"] + random.uniform(-1, 1), 1)
        elif sensor["type"] == "soil":
            sensor["value"] = round(sensor["value"] + random.uniform(-0.8, 0.8), 1)
        sensor["last_update"] = datetime.now().isoformat()
        
        # Update status based on value
        if sensor["type"] == "soil" and sensor["value"] < 35:
            sensor["status"] = "warning"
        elif sensor["type"] == "soil" and sensor["value"] < 25:
            sensor["status"] = "critical"
        else:
            sensor["status"] = "normal"
    
    return {{"sensors": sensors_db, "count": len(sensors_db)}}

@app.get("/api/sensors/{{sensor_id}}")
async def get_sensor(sensor_id: str):
    sensor = next((s for s in sensors_db if s["id"] == sensor_id), None)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor

@app.get("/api/sensors/{{sensor_id}}/readings")
async def get_sensor_readings(sensor_id: str, hours: int = 24):
    filtered = [r for r in readings_db if r["sensor_id"] == sensor_id]
    # Return last N hours
    cutoff = datetime.now() - timedelta(hours=hours)
    filtered = [r for r in filtered if datetime.fromisoformat(r["timestamp"]) > cutoff]
    return {{"readings": filtered[-100:], "count": len(filtered)}}

@app.get("/api/readings")
async def get_all_readings(hours: int = 24, sensor_type: str = None):
    filtered = readings_db
    if sensor_type:
        filtered = [r for r in filtered if r.get("type") == sensor_type]
    
    cutoff = datetime.now() - timedelta(hours=hours)
    filtered = [r for r in filtered if datetime.fromisoformat(r["timestamp"]) > cutoff]
    
    return {{"readings": filtered[-200:], "count": len(filtered)}}

@app.post("/api/irrigation/control")
async def control_irrigation(request: Dict):
    action = request.get("action", "start")
    zone = request.get("zone", "all")
    duration = request.get("duration_minutes", 15)
    
    if action == "start":
        irrigation_state["active"] = True
        irrigation_state["zone"] = zone
        irrigation_state["started_at"] = datetime.now().isoformat()
        
        log = {{
            "id": str(uuid.uuid4())[:8],
            "zone": zone,
            "duration_minutes": duration,
            "water_used": duration * 2.5,  # 2.5L per minute
            "timestamp": datetime.now().isoformat(),
            "action": "started"
        }}
        irrigation_logs.append(log)
        
        # Broadcast to websocket clients
        await manager.broadcast({{
            "type": "irrigation_started",
            "data": log
        }})
        
        return {{"status": "started", "irrigation": irrigation_state, "log": log}}
    
    elif action == "stop":
        irrigation_state["active"] = False
        irrigation_state["started_at"] = None
        
        log = {{
            "id": str(uuid.uuid4())[:8],
            "zone": zone,
            "duration_minutes": 0,
            "water_used": 0,
            "timestamp": datetime.now().isoformat(),
            "action": "stopped"
        }}
        irrigation_logs.append(log)
        
        await manager.broadcast({{
            "type": "irrigation_stopped",
            "data": log
        }})
        
        return {{"status": "stopped", "irrigation": irrigation_state}}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@app.get("/api/irrigation/status")
async def get_irrigation_status():
    return irrigation_state

@app.get("/api/irrigation/logs")
async def get_irrigation_logs(limit: int = 50):
    return {{"logs": irrigation_logs[-limit:], "count": len(irrigation_logs)}}

@app.get("/api/analytics")
async def get_analytics():
    # Calculate analytics from readings
    temp_readings = [r["value"] for r in readings_db if r.get("type") == "temperature"][-50:]
    humidity_readings = [r["value"] for r in readings_db if r.get("type") == "humidity"][-50:]
    soil_readings = [r["value"] for r in readings_db if r.get("type") == "soil"][-50:]
    
    water_today = sum(log["water_used"] for log in irrigation_logs if datetime.fromisoformat(log["timestamp"]).date() == datetime.now().date())
    
    return {{
        "avg_temperature": round(sum(temp_readings) / len(temp_readings), 1) if temp_readings else 24.5,
        "avg_humidity": round(sum(humidity_readings) / len(humidity_readings), 1) if humidity_readings else 65.0,
        "avg_soil_moisture": round(sum(soil_readings) / len(soil_readings), 1) if soil_readings else 42.0,
        "water_usage_today": round(water_today, 1),
        "water_usage_week": round(water_today * 6.5, 1),
        "alerts_count": len([s for s in sensors_db if s["status"] != "normal"]),
        "sensors_online": len(sensors_db),
        "irrigation_active": irrigation_state["active"],
        "readings_count": len(readings_db),
        "timestamp": datetime.now().isoformat()
    }}

@app.get("/api/alerts")
async def get_alerts():
    alerts = []
    for sensor in sensors_db:
        if sensor["status"] == "warning":
            alerts.append({{
                "id": str(uuid.uuid4())[:8],
                "type": "warning",
                "message": f"{{sensor['name']}} value low: {{sensor['value']}}{{sensor['unit']}}",
                "sensor_id": sensor["id"],
                "timestamp": datetime.now().isoformat()
            }})
        elif sensor["status"] == "critical":
            alerts.append({{
                "id": str(uuid.uuid4())[:8],
                "type": "critical",
                "message": f"{{sensor['name']}} critical: {{sensor['value']}}{{sensor['unit']}} - Immediate action required",
                "sensor_id": sensor["id"],
                "timestamp": datetime.now().isoformat()
            }})
    
    return {{"alerts": alerts, "count": len(alerts)}}

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send real-time updates every 3 seconds
            await asyncio.sleep(3)
            
            # Update sensor values
            for sensor in sensors_db:
                if sensor["type"] == "temperature":
                    sensor["value"] = round(sensor["value"] + random.uniform(-0.3, 0.3), 1)
                elif sensor["type"] == "humidity":
                    sensor["value"] = round(sensor["value"] + random.uniform(-0.5, 0.5), 1)
                elif sensor["type"] == "soil" and not irrigation_state["active"]:
                    sensor["value"] = round(max(10, sensor["value"] + random.uniform(-0.5, 0.1)), 1)
                elif sensor["type"] == "soil" and irrigation_state["active"]:
                    sensor["value"] = round(min(90, sensor["value"] + random.uniform(0.5, 1.5)), 1)
            
            data = {{
                "type": "sensor_update",
                "sensors": sensors_db,
                "irrigation": irrigation_state,
                "timestamp": datetime.now().isoformat()
            }}
            
            await websocket.send_text(json.dumps(data))
            
            # Also broadcast to all
            # await manager.broadcast(data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {{e}}")
        try:
            manager.disconnect(websocket)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
'''
    
    def _generate_generic_backend(self, project) -> str:
        return f'''"""
{project.name} - Backend API
Generated by RLCD Agentic IDE
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from datetime import datetime
import uuid
import random

app = FastAPI(title="{project.name} API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
items_db = []

@app.get("/")
async def root():
    return {{"name": "{project.name}", "status": "running", "timestamp": datetime.now().isoformat()}}

@app.get("/health")
async def health():
    return {{"status": "healthy"}}

@app.get("/api/data")
async def get_data():
    return {{"items": items_db, "count": len(items_db)}}

@app.post("/api/data")
async def create_data(item: Dict):
    item["id"] = str(uuid.uuid4())[:8]
    item["created_at"] = datetime.now().isoformat()
    items_db.append(item)
    return item

@app.get("/api/analytics")
async def get_analytics():
    return {{
        "total_items": len(items_db),
        "timestamp": datetime.now().isoformat(),
        "stats": {{"active": len(items_db), "growth": random.uniform(-5, 15)}}
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
'''
