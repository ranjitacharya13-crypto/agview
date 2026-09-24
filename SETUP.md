# Setup Instructions

## Prerequisites
- Python 3.11+
- Node.js 22+ (or 18+)
- npm 10+
- Git

## Backend Setup

```bash
# Clone
git clone <repo>
cd agview

# Python venv
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Environment variables (optional)
# Create .env in root or backend/
echo "OPENAI_API_KEY=sk-..." > .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Run backend (serves frontend if built)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Or
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be at:
- API: http://localhost:8000/api
- Docs: http://localhost:8000/docs (Swagger)
- Health: http://localhost:8000/api/health
- Frontend (if built): http://localhost:8000/

## Frontend Setup (Development)

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server at http://localhost:3000 with proxy to backend at :8000

## Frontend Production Build

```bash
cd frontend
npm install
npm run build
# Creates dist/ which backend serves automatically
```

Then run backend as above, visit http://localhost:8000

## Environment Variables

### Backend (.env)
```
OPENAI_API_KEY=sk-...  # Optional, falls back to mock
ANTHROPIC_API_KEY=sk-ant-...  # Optional
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL=mock
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

All secrets are protected:
- Never exposed to frontend
- Redacted in logs
- Detected by security validator
- Blocked env vars: AWS_SECRET, OPENAI_API_KEY, ANTHROPIC_API_KEY, GITHUB_TOKEN, SECRET, PASSWORD, PRIVATE_KEY

### Frontend (.env - optional)
```
VITE_API_BASE=/api
VITE_WS_BASE=/ws
```

## Testing Acceptance Criteria

```bash
# Ensure backend running
curl http://localhost:8000/api/health

# Create project
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Smart Greenhouse", "problem_statement": "Create a web application for a smart greenhouse that monitors temperature, humidity, soil moisture and automatically controls irrigation."}'

# Get project ID
PID=$(curl -s http://localhost:8000/api/projects/ | python -c "import json,sys; print(json.load(sys.stdin)['projects'][0]['project_id'])")

# Full pipeline
curl -X POST http://localhost:8000/api/projects/$PID/research -H "Content-Type: application/json" -d '{"query": "smart greenhouse"}'
curl -X POST http://localhost:8000/api/projects/$PID/abstract -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:8000/api/projects/$PID/abstract/approve -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:8000/api/projects/$PID/solution -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:8000/api/projects/$PID/frontend -H "Content-Type: application/json" -d '{}'  # Takes ~10s, builds real React app
curl -X POST http://localhost:8000/api/projects/$PID/backend -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:8000/api/projects/$PID/test -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:8000/api/projects/$PID/verify -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:8000/api/projects/$PID/presentation -H "Content-Type: application/json" -d '{}'

# Check results
curl http://localhost:8000/api/projects/$PID | python -m json.tool
curl http://localhost:8000/api/filesystem/$PID/list | python -m json.tool
ls workspace/$PID/dist/
ls workspace/$PID/backend/
ls workspace/$PID/presentations/
```

Expected:
- Frontend build SUCCESS (dist/ with index.html, assets)
- Backend compile SUCCESS (backend/main.py)
- Verification 7/7 PASSED
- Presentation 16 slides
- Files tracked: 17+
- Requirements: 7
- Actors, features, screens extracted

## Running Tests

```bash
# Backend tests (if pytest installed)
cd backend
pytest tests/ -v

# Frontend build test
cd frontend
npm run build

# Project-specific tests
cd workspace/{project_id}
npm run build  # Should succeed
cd backend && python -m py_compile main.py
```

## Packaging

```bash
# Via API
curl http://localhost:8000/api/export/{project_id}/package -o project.zip

# Or via backend directly
# Package includes source, README, docs, abstract, architecture, tests, presentation
```

## Docker (Optional)

```bash
# Backend
docker build -t agview-backend -f backend/Dockerfile backend/
docker run -p 8000:8000 -v $(pwd)/workspace:/app/workspace -v $(pwd)/backend/data:/app/backend/data agview-backend

# Frontend (if separate)
docker build -t agview-frontend -f frontend/Dockerfile frontend/
```

## Troubleshooting

### Backend fails to start
- Check Python version (3.11+)
- Check venv activated
- Check port 8000 not in use: `lsof -i :8000` or `netstat -tulpn | grep 8000`
- Check logs: `cat /tmp/uvicorn.log`

### Frontend build fails
- Check Node version: `node --version` (should be 18+)
- Clear node_modules: `rm -rf node_modules package-lock.json && npm install`
- Check for TypeScript errors: `npx tsc --noEmit`

### Project creation fails
- Check workspace permissions: `ls -la workspace/`
- Check backend data dir: `ls -la backend/data/projects/`

### WebSocket fails
- Check backend running
- Check CORS settings in backend/app/config.py
- For preview (e2b.app), ensure host 0.0.0.0 and port handling

### npm install fails in project workspace
- Use --legacy-peer-deps: `npm install --legacy-peer-deps`
- Check network
- Check disk space

## Development Order (As per spec)

The system was built in exact order:
1. ✓ VS Code-style shell (ActivityBar, Editor, StatusBar)
2. ✓ Real filesystem integration (WorkspaceManager, FilesystemService)
3. ✓ Monaco editor (EditorArea with tabs, dirty state, autosave)
4. ✓ Integrated terminal (TerminalService with security, real execution)
5. ✓ Project state (ProjectState Pydantic, ProjectManager persistence)
6. ✓ Agent event system (EventBus, WebSocket)
7. ✓ Model provider abstraction (Mock, OpenAI-compatible, capability routing)
8. ✓ Abstract Agent (pipeline, extraction, no watermark)
9. ✓ Research Agent (web_search interface, source tracking)
10. ✓ Frontend Engineering Agent (full autonomous loop, real files, build, fix)
11. ✓ Backend Agent (FastAPI, real endpoints, WebSocket)
12. ✓ Testing/Debugging (TestingAgent, DebuggingAgent, VisualReviewAgent)
13. ✓ RLCD decision service (CHOICE, SCORE, NOUL, state encoder)
14. ✓ Calibration (ECE, Brier, temperature scaling, buckets)
15. ✓ Trajectory/reward system (reward calculation, JSONL storage, stats)
16. ✓ Presentation Agent (PPTX from actual project, 17 slides, speaker notes)
17. ✓ Full autonomous workflow (MasterAgent with observe-decide-act loop)
18. ✓ Security hardening (workspace isolation, secret detection, dangerous command blocking)
19. ✓ Evaluation (dashboard, metrics, reliability curve)

## Commands to Run

```bash
# Development (both backend and frontend dev servers)
# Terminal 1: Backend
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Production (backend serves built frontend)
cd frontend && npm run build && cd ..
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Or single command
./start.sh  # If created
```

## Commands to Build

```bash
# Backend (no build needed, Python)
# Frontend
cd frontend
npm install
npm run build  # Creates dist/

# Project workspace (example greenhouse)
cd workspace/{project_id}
npm install
npm run build  # Should succeed, creates dist/

# Presentation (requires python-pptx)
pip install python-pptx
# Generated via API: POST /api/projects/{id}/presentation
```

## Commands to Package

```bash
# Via API
curl http://localhost:8000/api/export/{project_id}/package -o project.zip

# Manual
cd workspace/{project_id}
zip -r ../../project.zip . -x "node_modules/*" ".git/*" "__pycache__/*"
cd ../..
zip -r project_full.zip backend/ frontend/dist/ workspace/ -x "*/node_modules/*" "*/__pycache__/*" "*.pyc"

# With README
# README auto-generated in zip via export API
```

## Known Limitations

- Research uses mock (interface ready for Tavily/Serper)
- Mock model provider by default (OpenAI when key provided)
- Visual review heuristic (Playwright planned)
- Single workspace, no multi-user
- No real-time collaboration
- Presentation requires python-pptx (fallback MD)

## Support

- Check /docs for API documentation
- Check /api/health for backend status
- Check browser console for frontend errors
- Check /tmp/uvicorn.log for backend logs
- Check workspace/{id}/ for real files
