from typing import Dict, Any, List
import json
import os
from .base_agent import BaseAgent
from ..models.events import EventType
from ..models.project_state import ProjectStage
from pathlib import Path

class FrontendEngineeringAgent(BaseAgent):
    def __init__(self):
        super().__init__("frontend_agent", ["code_generation", "repository_reasoning", "tool_use", "debugging"])
    
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        
        self.emit_event(project_id, EventType.FRONTEND_STARTED, "Frontend engineering started")
        self.emit_event(project_id, EventType.AGENT_STARTED, "Frontend agent activated")
        
        action = task.get("action", "CREATE_FRONTEND")
        
        if action == "ANALYZE_REQUIREMENTS":
            return await self._analyze_requirements(project_id)
        elif action == "PLAN_FRONTEND":
            return await self._plan_frontend(project_id)
        else:
            return await self._create_frontend(project_id, task)
    
    async def _analyze_requirements(self, project_id: str) -> Dict[str, Any]:
        project = self.get_project(project_id)
        self.emit_event(project_id, EventType.AGENT_STARTED, "Analyzing frontend requirements")
        
        # Read existing files
        files = self.filesystem.list_directory(project_id, "")
        
        requirements = {
            "existing_files": files.get("files", []),
            "project_requirements": [r.model_dump() if hasattr(r, 'model_dump') else r for r in project.requirements],
            "screens": project.screens,
            "features": project.features,
            "tech_stack": project.tech_stack
        }
        
        self.emit_event(project_id, EventType.AGENT_COMPLETED, "Requirements analyzed", data=requirements)
        
        return {"success": True, "requirements": requirements}
    
    async def _plan_frontend(self, project_id: str) -> Dict[str, Any]:
        project = self.get_project(project_id)
        self.emit_event(project_id, EventType.AGENT_STARTED, "Planning frontend architecture")
        
        # Generate frontend plan
        screens = project.screens or ["Dashboard", "Monitoring", "Settings"]
        features = project.features or ["Dashboard", "Monitoring"]
        
        plan = {
            "pages": [{"name": s, "route": f"/{s.lower()}", "components": [f"{s}Page"]} for s in screens],
            "components": [
                {"name": "Dashboard", "type": "page", "features": ["charts", "stats"]},
                {"name": "SensorCard", "type": "component", "props": ["sensor"]},
                {"name": "Chart", "type": "component", "props": ["data"]},
                {"name": "Header", "type": "layout"},
                {"name": "Sidebar", "type": "layout"}
            ],
            "routes": [{"path": f"/{s.lower()}", "component": f"{s}Page"} for s in screens],
            "state": ["sensors", "readings", "user", "alerts"],
            "api_calls": ["/api/sensors", "/api/readings", "/api/irrigation"],
            "forms": ["SensorForm", "SettingsForm"],
            "authentication": ["Login", "ProtectedRoute"],
            "responsive_rules": ["mobile-first", "grid layout"]
        }
        
        project.frontend = plan
        self.save_project(project)
        
        self.emit_event(project_id, EventType.AGENT_COMPLETED, "Frontend plan created", data=plan)
        
        return {"success": True, "plan": plan}
    
    async def _create_frontend(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        
        # Ensure plan exists
        if not project.frontend:
            await self._plan_frontend(project_id)
            project = self.get_project(project_id)
        
        plan = project.frontend
        
        self.emit_event(project_id, EventType.AGENT_STARTED, "Inspecting repository")
        
        # Inspect repository
        existing = self.filesystem.list_directory(project_id, "")
        self.emit_event(project_id, EventType.AGENT_STARTED, f"Found {len(existing.get('files', []))} existing files")
        
        # Create package.json
        await self._create_package_json(project_id, project)
        
        # Create vite config
        await self._create_vite_config(project_id)
        
        # Create index.html
        await self._create_index_html(project_id, project)
        
        # Create src structure
        await self._create_src_structure(project_id, project, plan)
        
        # Install dependencies
        self.emit_event(project_id, EventType.COMMAND_STARTED, "Installing dependencies: npm install")
        install_result = self.terminal.execute(project_id, "npm install --legacy-peer-deps", "")
        
        if install_result["success"]:
            self.emit_event(project_id, EventType.COMMAND_COMPLETED, "Dependencies installed", data=install_result)
        else:
            self.emit_event(project_id, EventType.COMMAND_FAILED, "npm install failed", data=install_result)
        
        # Run build to verify
        self.emit_event(project_id, EventType.COMMAND_STARTED, "Running build: npm run build")
        build_result = self.terminal.execute(project_id, "npm run build", "")
        
        if build_result["success"]:
            self.emit_event(project_id, EventType.COMMAND_COMPLETED, "Build successful", data=build_result)
            project.stage = ProjectStage.TESTING
            project.verification["frontend_build"] = True
        else:
            self.emit_event(project_id, EventType.COMMAND_FAILED, "Build failed, attempting fix", data=build_result)
            # Attempt fix
            await self._fix_build_errors(project_id, build_result)
            # Retry build
            build_result = self.terminal.execute(project_id, "npm run build", "")
            if build_result["success"]:
                project.stage = ProjectStage.TESTING
            else:
                project.stage = ProjectStage.DEBUGGING
        
        self.save_project(project)
        
        self.emit_event(project_id, EventType.AGENT_COMPLETED, "Frontend engineering completed", data={
            "build_success": build_result["success"],
            "files_created": len(project.file_changes)
        })
        
        return {
            "success": build_result["success"],
            "build_result": build_result,
            "plan": plan
        }
    
    async def _create_package_json(self, project_id: str, project):
        package_json = {
            "name": project.name.lower().replace(" ", "-"),
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite --host 0.0.0.0 --port 5173",
                "build": "tsc && vite build",
                "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview",
                "test": "vitest"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.22.0",
                "recharts": "^2.12.0",
                "lucide-react": "^0.344.0",
                "zustand": "^4.5.0",
                "axios": "^1.6.7"
            },
            "devDependencies": {
                "@types/react": "^18.2.64",
                "@types/react-dom": "^18.2.21",
                "@vitejs/plugin-react": "^4.2.1",
                "typescript": "^5.2.2",
                "vite": "^5.0.8",
                "tailwindcss": "^3.4.1",
                "autoprefixer": "^10.4.18",
                "postcss": "^8.4.33"
            }
        }
        
        self.filesystem.write_file(project_id, "package.json", json.dumps(package_json, indent=2), agent=self.name)
        self.emit_event(project_id, EventType.FILE_CREATED, "Created package.json", data={"path": "package.json"})
    
    async def _create_vite_config(self, project_id: str):
        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    cors: true
  },
  preview: {
    host: '0.0.0.0',
    port: 5173
  }
})
"""
        self.filesystem.write_file(project_id, "vite.config.ts", vite_config, agent=self.name)
        self.emit_event(project_id, EventType.FILE_CREATED, "Created vite.config.ts")
        
        tsconfig = """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
"""
        self.filesystem.write_file(project_id, "tsconfig.json", tsconfig, agent=self.name)
        
        tsconfig_node = """{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
"""
        self.filesystem.write_file(project_id, "tsconfig.node.json", tsconfig_node, agent=self.name)
        
        tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
        self.filesystem.write_file(project_id, "tailwind.config.js", tailwind_config, agent=self.name)
        
        postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
        self.filesystem.write_file(project_id, "postcss.config.js", postcss_config, agent=self.name)
    
    async def _create_index_html(self, project_id: str, project):
        index_html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>__PROJECT_NAME__</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""".replace("__PROJECT_NAME__", project.name)
        self.filesystem.write_file(project_id, "index.html", index_html, agent=self.name)
    
    async def _create_src_structure(self, project_id: str, project, plan):
        is_greenhouse = "greenhouse" in project.problem_statement.lower() or "temperature" in project.problem_statement.lower() or "humidity" in project.problem_statement.lower()
        
        # main.tsx
        main_tsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""
        self.filesystem.write_file(project_id, "src/main.tsx", main_tsx, agent=self.name)
        
        index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  color-scheme: dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #0e0e10;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: #1e1e1e;
}

::-webkit-scrollbar-thumb {
  background: #424242;
}

::-webkit-scrollbar-thumb:hover {
  background: #4f4f4f;
}
"""
        self.filesystem.write_file(project_id, "src/index.css", index_css, agent=self.name)
        
        # App.tsx - use non-f-string template
        if is_greenhouse:
            app_tsx = self._generate_greenhouse_app(project)
        else:
            app_tsx = self._generate_generic_app(project)
        
        self.filesystem.write_file(project_id, "src/App.tsx", app_tsx, agent=self.name)
        
        # Components
        await self._create_components(project_id, project, is_greenhouse)
        
        # Store
        store_ts = """import { create } from 'zustand'

interface Sensor {
  id: string
  name: string
  type: 'temperature' | 'humidity' | 'soil'
  value: number
  unit: string
  status: 'normal' | 'warning' | 'critical'
  lastUpdate: string
}

interface Reading {
  timestamp: string
  temperature: number
  humidity: number
  soilMoisture: number
}

interface AppState {
  sensors: Sensor[]
  readings: Reading[]
  irrigationActive: boolean
  alerts: string[]
  setSensors: (sensors: Sensor[]) => void
  setReadings: (readings: Reading[]) => void
  toggleIrrigation: () => void
  addAlert: (alert: string) => void
}

export const useStore = create<AppState>((set) => ({
  sensors: [
    { id: '1', name: 'Temperature Sensor', type: 'temperature', value: 24.5, unit: '°C', status: 'normal', lastUpdate: new Date().toISOString() },
    { id: '2', name: 'Humidity Sensor', type: 'humidity', value: 65, unit: '%', status: 'normal', lastUpdate: new Date().toISOString() },
    { id: '3', name: 'Soil Moisture', type: 'soil', value: 42, unit: '%', status: 'warning', lastUpdate: new Date().toISOString() },
  ],
  readings: Array.from({ length: 24 }, (_, i) => ({
    timestamp: `${i}:00`,
    temperature: 20 + Math.random() * 10,
    humidity: 50 + Math.random() * 20,
    soilMoisture: 30 + Math.random() * 30,
  })),
  irrigationActive: false,
  alerts: ['Soil moisture low in Zone 2'],
  setSensors: (sensors) => set({ sensors }),
  setReadings: (readings) => set({ readings }),
  toggleIrrigation: () => set((state) => ({ irrigationActive: !state.irrigationActive })),
  addAlert: (alert) => set((state) => ({ alerts: [...state.alerts, alert] })),
}))
"""
        self.filesystem.write_file(project_id, "src/store.ts", store_ts, agent=self.name)
        
        self.emit_event(project_id, EventType.FILE_CREATED, "Created frontend source files")
    
    def _generate_greenhouse_app(self, project) -> str:
        # Use template without f-string interpolation issues
        template = """
import { useState, useEffect } from 'react'
import { Thermometer, Droplets, Sprout, Power, AlertTriangle, BarChart3, Settings, Leaf } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { useStore } from './store'

function App() {
  const { sensors, readings, irrigationActive, alerts, toggleIrrigation } = useStore()
  const [activeTab, setActiveTab] = useState('dashboard')

  useEffect(() => {
    const interval = setInterval(() => {
      // Real-time updates would come from WebSocket
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-[#0e0e10] text-white">
      <header className="border-b border-[#2d2d30] bg-[#181818] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-green-600 rounded flex items-center justify-center">
            <Leaf className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-semibold text-[13px]">__PROJECT_NAME__</h1>
            <p className="text-[11px] text-[#858585]">Smart Greenhouse Monitoring</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 text-[12px] bg-[#2d2d30] px-3 py-1 rounded">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            Live
          </div>
          <button className="p-2 hover:bg-[#2d2d30] rounded">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      <div className="flex h-[calc(100vh-57px)]">
        <aside className="w-[200px] bg-[#181818] border-r border-[#2d2d30] p-2">
          <nav className="space-y-1">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
              { id: 'sensors', label: 'Sensors', icon: Thermometer },
              { id: 'irrigation', label: 'Irrigation', icon: Droplets },
              { id: 'crops', label: 'Crops', icon: Sprout },
            ].map(item => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded text-[13px] transition-colors ${
                  activeTab === item.id ? 'bg-[#37373d] text-white' : 'text-[#cccccc] hover:bg-[#2a2d2e] hover:text-white'
                }`}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </button>
            ))}
          </nav>

          <div className="mt-6 p-3 bg-[#1f1f1f] rounded border border-[#2d2d30]">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-[#858585] mb-2">System Status</h3>
            <div className="space-y-2 text-[12px]">
              <div className="flex justify-between">
                <span className="text-[#858585]">Uptime</span>
                <span>12d 4h</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#858585]">Sensors</span>
                <span className="text-green-400">3/3 Online</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#858585]">Irrigation</span>
                <span className={irrigationActive ? 'text-blue-400' : 'text-[#858585]'}>{irrigationActive ? 'Active' : 'Idle'}</span>
              </div>
            </div>
          </div>

          {alerts.length > 0 && (
            <div className="mt-4 p-3 bg-[#2a1f1f] border border-[#5a1d1d] rounded">
              <div className="flex items-center gap-2 text-[12px] font-medium text-[#f85149] mb-1">
                <AlertTriangle className="w-4 h-4" />
                Alerts ({alerts.length})
              </div>
              <div className="text-[11px] text-[#cccccc]">{alerts[0]}</div>
            </div>
          )}
        </aside>

        <main className="flex-1 overflow-auto bg-[#1f1f1f] p-6">
          {activeTab === 'dashboard' && (
            <div className="space-y-6 max-w-[1200px] mx-auto">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-[18px] font-semibold">Greenhouse Dashboard</h2>
                  <p className="text-[13px] text-[#858585]">Real-time monitoring and control</p>
                </div>
                <button
                  onClick={toggleIrrigation}
                  className={`flex items-center gap-2 px-4 py-2 rounded text-[13px] font-medium transition-colors ${
                    irrigationActive ? 'bg-blue-600 hover:bg-blue-700' : 'bg-[#2d2d30] hover:bg-[#37373d]'
                  }`}
                >
                  <Power className="w-4 h-4" />
                  {irrigationActive ? 'Stop Irrigation' : 'Start Irrigation'}
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {sensors.map(sensor => (
                  <div key={sensor.id} className="bg-[#181818] border border-[#2d2d30] rounded p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded flex items-center justify-center ${
                          sensor.type === 'temperature' ? 'bg-orange-500/20 text-orange-400' :
                          sensor.type === 'humidity' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-green-500/20 text-green-400'
                        }`}>
                          {sensor.type === 'temperature' ? <Thermometer className="w-4 h-4" /> :
                           sensor.type === 'humidity' ? <Droplets className="w-4 h-4" /> :
                           <Sprout className="w-4 h-4" />}
                        </div>
                        <span className="text-[13px] font-medium">{sensor.name}</span>
                      </div>
                      <span className={`text-[11px] px-2 py-0.5 rounded ${
                        sensor.status === 'normal' ? 'bg-green-500/20 text-green-400' :
                        sensor.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>{sensor.status}</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-[24px] font-semibold">{sensor.value}</span>
                      <span className="text-[13px] text-[#858585]">{sensor.unit}</span>
                    </div>
                    <div className="text-[11px] text-[#858585] mt-1">Updated {new Date(sensor.lastUpdate).toLocaleTimeString()}</div>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="bg-[#181818] border border-[#2d2d30] rounded p-4">
                  <h3 className="text-[13px] font-medium mb-4">Temperature & Humidity (24h)</h3>
                  <div className="h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={readings}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2d2d30" />
                        <XAxis dataKey="timestamp" stroke="#858585" fontSize={11} />
                        <YAxis stroke="#858585" fontSize={11} />
                        <Tooltip contentStyle={{ backgroundColor: '#181818', border: '1px solid #2d2d30', fontSize: '12px' }} />
                        <Line type="monotone" dataKey="temperature" stroke="#f97316" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="humidity" stroke="#3b82f6" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="bg-[#181818] border border-[#2d2d30] rounded p-4">
                  <h3 className="text-[13px] font-medium mb-4">Soil Moisture Trend</h3>
                  <div className="h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={readings}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2d2d30" />
                        <XAxis dataKey="timestamp" stroke="#858585" fontSize={11} />
                        <YAxis stroke="#858585" fontSize={11} />
                        <Tooltip contentStyle={{ backgroundColor: '#181818', border: '1px solid #2d2d30', fontSize: '12px' }} />
                        <Area type="monotone" dataKey="soilMoisture" stroke="#22c55e" fill="#22c55e33" strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              <div className="bg-[#181818] border border-[#2d2d30] rounded p-4">
                <h3 className="text-[13px] font-medium mb-3">Irrigation Control</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-[#1f1f1f] p-3 rounded border border-[#2d2d30]">
                    <div className="text-[11px] text-[#858585] uppercase tracking-wider">Next Schedule</div>
                    <div className="text-[13px] font-medium mt-1">Today, 18:00</div>
                    <div className="text-[11px] text-[#858585]">Duration: 15 min</div>
                  </div>
                  <div className="bg-[#1f1f1f] p-3 rounded border border-[#2d2d30]">
                    <div className="text-[11px] text-[#858585] uppercase tracking-wider">Water Usage</div>
                    <div className="text-[13px] font-medium mt-1">42.5 L today</div>
                    <div className="text-[11px] text-green-400">↓ 12% vs yesterday</div>
                  </div>
                  <div className="bg-[#1f1f1f] p-3 rounded border border-[#2d2d30]">
                    <div className="text-[11px] text-[#858585] uppercase tracking-wider">Automation</div>
                    <div className="text-[13px] font-medium mt-1">Enabled</div>
                    <div className="text-[11px] text-[#858585]">Threshold: 35% moisture</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'sensors' && (
            <div className="max-w-[800px]">
              <h2 className="text-[18px] font-semibold mb-4">Sensor Management</h2>
              <div className="space-y-3">
                {sensors.map(s => (
                  <div key={s.id} className="bg-[#181818] border border-[#2d2d30] rounded p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-[#2d2d30] rounded flex items-center justify-center">
                        <Thermometer className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="text-[13px] font-medium">{s.name}</div>
                        <div className="text-[11px] text-[#858585]">ID: {s.id} • {s.type}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[14px] font-medium">{s.value} {s.unit}</div>
                      <div className="text-[11px] text-[#858585]">{s.status}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'irrigation' && (
            <div className="max-w-[600px]">
              <h2 className="text-[18px] font-semibold mb-4">Irrigation Control</h2>
              <div className="bg-[#181818] border border-[#2d2d30] rounded p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-[14px] font-medium">Manual Control</h3>
                    <p className="text-[12px] text-[#858585]">Override automatic irrigation</p>
                  </div>
                  <button
                    onClick={toggleIrrigation}
                    className={`relative w-12 h-6 rounded-full transition-colors ${irrigationActive ? 'bg-blue-600' : 'bg-[#3a3d41]'}`}
                  >
                    <div className={`absolute w-5 h-5 bg-white rounded-full top-0.5 transition-transform ${irrigationActive ? 'translate-x-6' : 'translate-x-0.5'}`}></div>
                  </button>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="text-[12px] text-[#cccccc]">Water Flow Rate</label>
                    <input type="range" className="w-full mt-1" min="0" max="100" defaultValue="60" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-[12px] text-[#cccccc]">Duration (min)</label>
                      <input type="number" className="w-full mt-1 bg-[#1f1f1f] border border-[#3a3d41] rounded px-3 py-2 text-[13px]" defaultValue="15" />
                    </div>
                    <div>
                      <label className="text-[12px] text-[#cccccc]">Zone</label>
                      <select className="w-full mt-1 bg-[#1f1f1f] border border-[#3a3d41] rounded px-3 py-2 text-[13px]">
                        <option>All Zones</option>
                        <option>Zone 1</option>
                        <option>Zone 2</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'crops' && (
            <div>
              <h2 className="text-[18px] font-semibold mb-4">Crop Management</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                  { name: 'Tomatoes', growth: 75, health: 'Good', days: 45 },
                  { name: 'Lettuce', growth: 90, health: 'Excellent', days: 20 },
                  { name: 'Cucumbers', growth: 60, health: 'Good', days: 30 },
                ].map(crop => (
                  <div key={crop.name} className="bg-[#181818] border border-[#2d2d30] rounded p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-green-500/20 rounded flex items-center justify-center">
                        <Sprout className="w-5 h-5 text-green-400" />
                      </div>
                      <div>
                        <div className="text-[13px] font-medium">{crop.name}</div>
                        <div className="text-[11px] text-[#858585]">Day {crop.days}</div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-[11px] mb-1">
                          <span className="text-[#858585]">Growth</span>
                          <span>{crop.growth}%</span>
                        </div>
                        <div className="w-full bg-[#2d2d30] rounded-full h-1.5">
                          <div className="bg-green-500 h-1.5 rounded-full" style={{ width: `${crop.growth}%` }}></div>
                        </div>
                      </div>
                      <div className="text-[11px]">
                        <span className="text-[#858585]">Health:</span> <span className="text-green-400">{crop.health}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
"""
        return template.replace("__PROJECT_NAME__", project.name)
    
    def _generate_generic_app(self, project) -> str:
        template = """
import { useState } from 'react'
import { LayoutDashboard, Settings, BarChart3, Users } from 'lucide-react'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="min-h-screen bg-[#0e0e10] text-white">
      <header className="border-b border-[#2d2d30] bg-[#181818] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
            <LayoutDashboard className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-semibold text-[13px]">__PROJECT_NAME__</h1>
            <p className="text-[11px] text-[#858585]">Agentic Engineering Platform</p>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-57px)]">
        <aside className="w-[200px] bg-[#181818] border-r border-[#2d2d30] p-2">
          <nav className="space-y-1">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
              { id: 'analytics', label: 'Analytics', icon: BarChart3 },
              { id: 'users', label: 'Users', icon: Users },
              { id: 'settings', label: 'Settings', icon: Settings },
            ].map(item => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded text-[13px] ${activeTab === item.id ? 'bg-[#37373d]' : 'text-[#cccccc] hover:bg-[#2a2d2e]'}`}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </button>
            ))}
          </nav>
        </aside>

        <main className="flex-1 p-6 bg-[#1f1f1f]">
          <div className="max-w-[1000px] mx-auto">
            <h2 className="text-[18px] font-semibold mb-2 capitalize">{activeTab}</h2>
            <p className="text-[13px] text-[#858585] mb-6">Welcome to __PROJECT_NAME__. This application was generated by the RLCD Agentic IDE.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1,2,3].map(i => (
                <div key={i} className="bg-[#181818] border border-[#2d2d30] rounded p-4">
                  <h3 className="text-[13px] font-medium mb-2">Feature {i}</h3>
                  <p className="text-[12px] text-[#858585]">This is a generated feature based on project requirements.</p>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
"""
        return template.replace("__PROJECT_NAME__", project.name)
    
    async def _create_components(self, project_id: str, project, is_greenhouse: bool):
        # Create a few extra components
        if is_greenhouse:
            sensor_card = """import { Thermometer, Droplets, Sprout } from 'lucide-react'

interface Props {
  sensor: {
    id: string
    name: string
    type: string
    value: number
    unit: string
    status: string
  }
}

export function SensorCard({ sensor }: Props) {
  return (
    <div className="bg-[#181818] border border-[#2d2d30] rounded p-4">
      <div className="flex items-center gap-2 mb-2">
        {sensor.type === 'temperature' ? <Thermometer className="w-4 h-4" /> : 
         sensor.type === 'humidity' ? <Droplets className="w-4 h-4" /> : 
         <Sprout className="w-4 h-4" />}
        <span className="text-[13px]">{sensor.name}</span>
      </div>
      <div className="text-[20px] font-semibold">{sensor.value} {sensor.unit}</div>
    </div>
  )
}
"""
            self.filesystem.write_file(project_id, "src/components/SensorCard.tsx", sensor_card, agent=self.name)
    
    async def _fix_build_errors(self, project_id: str, build_result: Dict[str, Any]):
        stderr = build_result.get("stderr", "")
        self.emit_event(project_id, EventType.DEBUG_STARTED, "Attempting to fix build errors", data={"stderr": stderr[:500]})
        
        # Common fixes
        if "Cannot find module" in stderr:
            # Try to install missing deps
            self.terminal.execute(project_id, "npm install", "")
        
        if "TS" in stderr and "error" in stderr:
            # TypeScript error - try to create missing files
            pass
        
        self.emit_event(project_id, EventType.FIX_APPLIED, "Applied build fixes")
