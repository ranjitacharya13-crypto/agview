# RLCD Agentic Engineering IDE

A complete AI-powered agentic software engineering IDE that behaves like a combination of:
- VS Code-style development environment
- Autonomous coding agent
- Professional AI writing system
- Research agent
- Calibrated decision engine (RLCD-inspired)
- Agent orchestration system
- Automated testing/debugging system
- Presentation-generation system

**NOT a simple chatbot** - operates on REAL PROJECT FILES with real execution.

## Architecture

```
                         USER
                           |
                           v
                  PROJECT WORKSPACE
                           |
                           v
                  MASTER AGENT
                           |
                           v
              RLCD DECISION ENGINE
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
         RESEARCH       WRITING       ENGINEERING
           AGENT          AGENT          AGENTS
             |             |             |
             |             |       +-----+-----+
             |             |       |           |
             |             |       v           v
             |             |   FRONTEND     BACKEND
             |             |   ENGINEER     ENGINEER
             |             |       |           |
             |             |       +-----+-----+
             |             |             |
             |             |             v
             |             |           TEST
             |             |             |
             |             |             v
             |             |           DEBUG
             |             |             |
             |             |             v
             +-------------+----------VERIFY
                                       |
                                       v
                                    REWARD
                                       |
                                       v
                               EXPERIENCE STORE
                                       |
                                       v
                               CALIBRATION DATA
```

## Features

### VS Code-Style IDE
- Activity bar (Explorer, Search, Source Control, Debug, Extensions, Agents, Abstract, RLCD)
- File explorer with real filesystem
- Monaco editor with syntax highlighting, tabs, minimap, breadcrumbs
- Integrated terminal with real command execution
- Status bar, command palette, diff viewer
- Dark theme, VS Code-inspired design

### Real File Operations
- create, read, edit, delete files with permission
- create folders, move, rename
- search files
- All operations return structured results
- File change history with rollback

### Security / Sandbox
- Workspace isolation
- Command allowlists
- Dangerous-command detection (rm -rf /, etc)
- Filesystem permission checks
- Secret detection (API keys, tokens)
- Process timeout, memory limits
- Environment variable protection

### RLCD Decision Engine (Jev-inspired, NOT proprietary reproduction)
- **CHOICE**: Selects action from finite action space with probabilities
- **SCORE**: Bounded value (0-1) for quality metrics
- **NOUL**: Calibrated binary decisions (YES/NO with confidence)
- Calibration: ECE, Brier Score, reliability diagrams, temperature scaling
- Raw vs Calibrated confidence tracking
- Development policy marked, trainable architecture ready

### Agents
- **MasterAgent**: Orchestrates, understands project state, calls RLCD, selects agents
- **ResearchAgent**: Web search, source collection (mock + real interface)
- **AbstractAgent**: Professional abstract generation (150-300 words) with pipeline: UNDERSTAND->RESEARCH->PLAN->DRAFT->CRITIQUE->REVISE->VERIFY
- **AbstractCritic**: Evaluates clarity, correctness, coherence
- **SolutionArchitectAgent**: Requirements, architecture, tech stack, data flow, API, DB, security
- **FrontendEngineeringAgent**: Full autonomous loop: UNDERSTAND->INSPECT->PLAN->EDIT->RUN->TEST->FIX->VERIFY. Creates real React+TS+Tailwind+Recharts apps
- **BackendEngineeringAgent**: FastAPI with real endpoints, WebSocket, database models
- **TestingAgent**: Build tests, backend compile checks, integration
- **DebuggingAgent**: ERROR->COLLECT LOGS->ROOT CAUSE->FIX->TEST->VERIFY
- **PresentationAgent**: Generates PPTX from actual project artifacts with speaker notes (17 slides)
- **VisualReviewAgent**: Heuristic UI checks

### Project State
Persistent ProjectState with:
- project_id, name, root, dates, branch, stage
- problem_statement, requirements, research, abstract
- solution, frontend, backend, database, tests, verification, presentation
- decisions, trajectories, file_changes, approvals
- Memory categories: PROJECT, RESEARCH, ABSTRACT, ARCHITECTURE, DECISIONS, FILES, ERRORS, FIXES, TESTS, etc.

### Model Provider Abstraction
- Interface: generate(), structured_output(), capabilities
- Providers: Mock (development), OpenAI-compatible, Anthropic-compatible
- Capability registry, routing by required capabilities
- No hard-coded vendor dependencies

### Event System
Real-time events via WebSocket:
- PROJECT_CREATED, RESEARCH_STARTED/COMPLETED, ABSTRACT_STARTED/GENERATED/APPROVED
- FRONTEND_STARTED, FILE_CREATED/EDITED, COMMAND_STARTED/COMPLETED/FAILED
- TEST_STARTED/PASSED/FAILED, DEBUG_STARTED, FIX_APPLIED, VERIFICATION_COMPLETED
- RLCD_DECISION, REWARD_RECORDED, AGENT_STARTED/COMPLETED

### Evaluation Dashboard
- Decision accuracy, calibration error, Brier score
- Success rate, agent routing accuracy
- Average reward, latency, cost
- Confidence histogram, reliability curve, reward history

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend serves frontend at http://localhost:8000 and API at /api, docs at /docs

### Frontend (Development)
```bash
cd frontend
npm install
npm run dev  # http://localhost:3000 proxies to backend
```

### Frontend (Production Build)
```bash
cd frontend
npm run build
# Backend will serve dist/ automatically
```

## Environment Variables
Create `.env` in root or backend/:
```
OPENAI_API_KEY=sk-... (optional, falls back to mock)
ANTHROPIC_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL=mock
```

All secrets are redacted from frontend, protected by security validator.

## API Endpoints

```
POST /api/projects
GET /api/projects/{id}
POST /api/projects/{id}/problem
POST /api/projects/{id}/research
POST /api/projects/{id}/abstract
POST /api/projects/{id}/abstract/approve
POST /api/projects/{id}/solution
POST /api/projects/{id}/frontend
POST /api/projects/{id}/backend
POST /api/projects/{id}/test
POST /api/projects/{id}/debug
POST /api/projects/{id}/verify
POST /api/projects/{id}/presentation
POST /api/projects/{id}/master
POST /api/projects/{id}/chat
GET /api/projects/{id}/events
GET /api/projects/{id}/trajectories

POST /api/rlcd/decision
GET /api/rlcd/calibration
GET /api/rlcd/evaluation
GET /api/rlcd/action-space

GET /api/filesystem/{id}/list
GET /api/filesystem/{id}/tree
POST /api/filesystem/{id}/read
POST /api/filesystem/{id}/write
POST /api/filesystem/{id}/delete
POST /api/filesystem/{id}/search

POST /api/terminal/{id}/execute
GET /api/terminal/{id}/processes

GET /api/agents/
GET /api/git/{id}/status
GET /api/export/{id}/package
GET /api/export/{id}/readme

WebSocket: /ws/projects/{id}
```

## Acceptance Test

The system passes the complete hackathon pipeline:

```
USER: "Create a web application for a smart greenhouse that monitors temperature, humidity, soil moisture and automatically controls irrigation."

SYSTEM:
1. ✓ create project
2. ✓ store problem
3. ✓ research (3 sources with URLs, claims, confidence)
4. ✓ generate abstract (1429 chars, professional)
5. ✓ critique abstract
6. ✓ show abstract in IDE
7. ✓ allow user approval
8. ✓ create structured requirements (7 requirements)
9. ✓ create architecture (React+FastAPI+PostgreSQL)
10. ✓ RLCD selects CREATE_FRONTEND
11. ✓ frontend agent inspects workspace
12. ✓ creates frontend plan
13. ✓ creates files (package.json, vite.config, App.tsx, store.ts, etc)
14. ✓ installs dependencies (real npm install)
15. ✓ runs application (vite build)
16. ✓ tests application (build test)
17. ✓ detects errors & fixes
18. ✓ runs again
19. ✓ browser verification (heuristic)
20. ✓ updates project memory
21. ✓ records reward & trajectory
22. ✓ displays changes in VS Code-style interface
23. ✓ allows diff inspection
24. ✓ backend creation (FastAPI with 5 endpoints + WebSocket)
25. ✓ frontend/backend integration tested
26. ✓ presentation with 16 slides + speaker notes
27. ✓ final verification (7 checks)
28. ✓ project can be exported as zip
```

Test Results (latest run):
- Stage: PRESENTATION → VERIFICATION PASSED
- Files: 17 tracked
- Requirements: 7
- Actors: Farmer, Agronomist, User
- Features: 7 (Dashboard, Monitoring, Irrigation, etc)
- Screens: 7 (Dashboard, Sensors, Irrigation, Crops, etc)
- Build: SUCCESS (558KB JS, 12KB CSS)
- Backend: 5 files, compile OK
- Presentation: 16 slides, 68KB PPTX
- Verification: 7/7 checks PASSED

## Project Structure

```
agview/
├── backend/
│   ├── app/
│   │   ├── main.py (FastAPI + WebSocket + static serving)
│   │   ├── config.py
│   │   ├── core/ (security, workspace)
│   │   ├── models/ (project_state, rlcd, events)
│   │   ├── services/ (filesystem, terminal, project_manager, event_bus, rlcd_engine, reward, model_provider)
│   │   ├── agents/ (master, research, abstract, solution, frontend, backend, testing, debugging, presentation, visual_review)
│   │   └── api/routes/ (projects, rlcd, filesystem, terminal, agents, git, export)
│   ├── data/
│   │   ├── projects/ (JSON per project)
│   │   ├── trajectories/ (JSONL per project)
│   │   └── calibration/ (calibration.json)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/ (ActivityBar, Explorer, Editor, Terminal, AgentPanel, StatusBar, Chat, etc)
│   │   ├── services/ (api, websocket)
│   │   ├── stores/ (projectStore, editorStore, agentStore, terminalStore, rlcdStore)
│   │   ├── types/
│   │   ├── App.tsx (VS Code-style shell)
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── workspace/ (real project files, per-project ID)
│   └── {project_id}/
│       ├── src/ (React app)
│       ├── backend/ (FastAPI)
│       ├── dist/ (built frontend)
│       ├── presentations/ (PPTX)
│       └── package.json
├── ARCHITECTURE.md
├── SETUP.md
└── README.md
```

## RLCD Details

### Action Space
```
ANALYZE_PROBLEM, RESEARCH, CREATE_ABSTRACT, REVISE_ABSTRACT,
CREATE_SOLUTION, CREATE_FRONTEND, CREATE_BACKEND, CREATE_DATABASE,
INTEGRATE, RUN_TESTS, DEBUG, VERIFY, CREATE_PRESENTATION, ASK_USER, STOP
```

### Calibration
- Raw confidence → Calibrated via temperature scaling
- ECE, Brier Score, reliability diagram
- Records: raw, calibrated, outcome, decision_type
- Development policy clearly marked

### Reward Function
Positive: successful task, passing tests, correct implementation, verified source, user approval, efficient execution, integration
Negative: failed implementation, hallucinated info, fabricated sources, failed tests, unnecessary retries, excessive cost/latency, wrong routing, unverified claims
Configurable weights.

### Offline RL
```
trajectory dataset → offline training → evaluation → calibration → policy candidate → human approval → production policy
```
Supports policy_v1, v2, v3 with rollback. Never auto-replaces production.

## Security
- All terminal commands run in workspace sandbox
- Path traversal prevention
- Secret detection (OpenAI keys, GitHub PAT, AWS keys, private keys, hardcoded passwords)
- Dangerous pattern blocking (rm -rf /, fork bomb, mkfs, etc)
- Approval required for destructive commands
- Env var protection, redaction

## Known Limitations
- Research uses mock web_search (interface ready for Tavily/Serper)
- Model provider defaults to mock (OpenAI compatible when key provided)
- Browser verification heuristic (Playwright integration planned)
- Single workspace, no multi-user yet
- No real-time collaboration
- Presentation PPTX requires python-pptx (fallback to MD)

## Future
- IoT hardware integration
- ML predictive analytics
- Mobile app
- Multi-tenant, RBAC
- Playwright browser automation
- Trainable RLCD with PyTorch
- Multi-agent RL

## License
MIT - Built for hackathon demonstration
