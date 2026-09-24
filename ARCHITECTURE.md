# RLCD Agentic Engineering IDE - Architecture

## Overview
Model-agnostic, tool-centric, stateful, verifiable, calibrated, human-controlled, reproducible agentic IDE.

## Components

### 1. VS Code-Style Shell (Frontend)
- **ActivityBar**: 48px vertical bar with icons, active indicator, tooltips
- **Sidebar**: 260-320px, switchable views (Explorer, Search, Git, Debug, Extensions, Agents, Abstract, RLCD)
- **Editor**: Monaco editor, multi-tab, dirty indicator, breadcrumbs, minimap, autosave
- **Terminal**: Integrated terminal with real command execution, stdout/stderr, exit codes, history
- **AgentPanel**: Right panel with current agent, task, RLCD decision, confidence, evidence, timeline, calibration
- **ChatPanel**: AI chat integrated, context-aware (current file, terminal, project state)
- **StatusBar**: Branch, language, encoding, agent status, backend connection, model status, calibration
- **CommandPalette**: Ctrl+P, quick actions

Technologies: React 18, TypeScript, Vite, Monaco Editor, Tailwind CSS, Lucide Icons, Zustand, Axios, Xterm

### 2. Project Workspace
```
/workspace/{project_id}/
  /src (React frontend)
  /public
  /backend (FastAPI)
  /docs
  /tests
  /presentations (PPTX)
  package.json
  README.md
  .env.example
```
Real filesystem, not mocked. WorkspaceManager handles isolation, path traversal prevention.

### 3. Project State
Pydantic model, persisted as JSON per project:
- Identification, timestamps, branch, stage (INITIAL→COMPLETED)
- Problem, requirements (extracted from abstract), research (with sources), abstract, approved flag
- Solution (architecture, tech stack, data flow, API, DB, security)
- Frontend plan (pages, components, routes, state, api_calls)
- Backend, database, tests, verification, presentation
- Decisions (CHOICE/SCORE/NOUL with raw/calibrated confidence, risk, evidence)
- Trajectories (STATE→ACTION→RESULT→REWARD→NEXT_STATE)
- FileChanges (agent, timestamp, path, operation, old/new content, reason)
- Memory (categorized: PROJECT, RESEARCH, ABSTRACT, ARCHITECTURE, DECISIONS, FILES, ERRORS, FIXES, TESTS, USER_PREFERENCES, APPROVALS, TRAJECTORIES)
- Actors, features, screens (extracted from abstract)

Shared between agents via ProjectManager (cache + JSON persistence).

### 4. Master Agent
Not generating all code, but:
- Understand project state
- Determine current stage
- Evaluate available information
- Call RLCD decision engine
- Select appropriate agent
- Execute workflow
- Monitor results
- Trigger verification
- Request human approval
- Update project memory

Autonomous loop: observe → decide → act → observe result → verify → repair → continue, with max iterations, cost, runtime, tool calls. If exceeded → ASK_USER.

### 5. RLCD Decision Engine
Inspired by publicly described concepts, NOT proprietary reproduction.

**State Encoder**: Project stage, requirements count, research count, has abstract, approved, solution size, frontend/backend size, decisions count, file changes, problem length, tech stack presence → 128-dim vector.

**Choice Head**: Valid actions based on stage, heuristic probabilities for development policy, normalized, selected max prob. Development policy marked.

**Score Head**: Bounded 0-1 for metrics: abstract_quality, frontend_readiness, backend_readiness, research_quality, project_completion, risk, test_quality, verification_quality. Heuristic based on artifacts.

**Noul Head**: Binary YES/NO with yes_prob, no_prob, calibrated via temperature scaling. Questions like "Is abstract ready?", "Should frontend be activated?".

**Calibration**: Store records raw, calibrated, outcome, type. Metrics: ECE (10 buckets), Brier Score, accuracy, confidence buckets, reliability data. Temperature scaling: logit/T → sigmoid. Update temperature method.

**Policy Versions**: v1 production (DEVELOPMENT POLICY, 72% accuracy), v2 candidate. Offline RL pipeline with human approval gate, rollback support.

### 6. Agents

#### ResearchAgent
- Capabilities: web_search, source collection, technical research
- Tools: web_search (mock interface, ready for Tavily)
- Output: ResearchItem with source, URL, title, claim, confidence, date
- Every factual result retains source, URL, title, date, claim, confidence
- No fabricated sources

#### AbstractAgent
Pipeline: PROBLEM → UNDERSTAND → RESEARCH → PLAN → DRAFT → CRITIQUE → REVISE → VERIFY → FINAL
- Uses model provider (mock or OpenAI)
- Structure: TITLE, ABSTRACT, Problem, Existing limitation, Proposed solution, Methodology, Technology, Expected impact
- 150-300 words
- No watermark, clean professional
- Extracts requirements, actors, features, screens → project memory
- Stores in PROJECT, ABSTRACT memory

#### AbstractCritic
Evaluates: clarity, technical correctness, coherence, relevance, naturalness, source grounding, problem alignment, solution alignment, unsupported claims
Output: {quality, needs_revision, issues, clarity, technical_correctness, coherence}
If needs_revision → RLCD REVISE_ABSTRACT → AbstractAgent → Critic (max iterations)

#### SolutionArchitectAgent
Input: problem, research, approved abstract
Output: requirements (functional, non-functional), architecture (frontend, backend, database, deployment), tech stack, data flow, API requirements, database requirements (tables, relationships), security, deployment
Fallback heuristics for greenhouse, healthcare, generic.

#### FrontendEngineeringAgent
Capabilities: read repo, list files, search, read, create, modify, rename, mkdir, install deps, run commands, start/stop server, build, test, browser test, inspect errors, fix, review UI, verify
Action Space: ANALYZE_REQUIREMENTS, INSPECT_REPOSITORY, SEARCH_CODE, READ_FILE, PLAN_FRONTEND, CREATE_FILE, EDIT_FILE, MOVE_FILE, DELETE_FILE, INSTALL_DEPENDENCY, RUN_COMMAND, START_SERVER, STOP_SERVER, RUN_BUILD, RUN_TEST, RUN_BROWSER_TEST, INSPECT_ERROR, FIX_ERROR, REVIEW_UI, VERIFY, ASK_USER
Workflow: UNDERSTAND → INSPECT → PLAN (pages, components, routes, state, api_calls, forms, auth, responsive) → EDIT → RUN → TEST → INSPECT ERROR → FIX → RUN AGAIN → VERIFY
Real file creation via filesystem service, real npm install, real build, error fixing.

#### BackendEngineeringAgent
Capabilities: API design, database design, auth, validation, business logic, logging, error handling, testing, documentation
Stacks: FastAPI (chosen based on requirements) or Node/Express
Creates: main.py with real endpoints (sensors, readings, irrigation, analytics, alerts, health, WebSocket), models.py, database.py, requirements.txt, README
Features: CORS, WebSocket manager, in-memory DB with real logic, sensor simulation, irrigation control, analytics aggregation.

#### DatabaseAgent
Part of backend, responsibilities: schema, models, relationships, indexes, migrations, seed, queries, validation. Supports PostgreSQL, MongoDB (configurable). Currently SQLite for dev, PostgreSQL ready.

#### TestingAgent
Responsibilities: unit, integration, API, frontend, browser, database testing
Never marks complete merely because LLM says "Done" - requires actual verification (build exit code 0, etc)

#### DebuggingAgent
Workflow: ERROR → COLLECT LOGS → IDENTIFY ROOT CAUSE → RLCD DECISION → SELECT FIX → PATCH → TEST → VERIFY
Stores successful fixes as experience.
Fixes: missing_dependency → npm install, typescript_error → config check, missing_file → recreation, generic → legacy-peer-deps.

#### PresentationAgent
Reads: problem, research, abstract, solution, actual files, architecture, test results, screenshots, verification
Generates 17 slides: Title, Problem, Existing System, Limitations, Proposed Solution, Objectives, Architecture, Technology Stack, RLCD Decision Architecture, Agentic Workflow, Frontend, Backend, Database, Testing, Results, Future Scope, Conclusion
Reflects actual project (files count, build status, etc), never invents.
Speaker notes for every slide.
Uses python-pptx if available, fallback to markdown + JSON.

#### VisualReviewAgent
Inspects screenshots (heuristic currently) for layout, spacing, responsive, missing components, broken elements, text overflow, accessibility, visual defects.
If fails → RLCD FIX_FRONTEND → FrontendAgent edits.

### 7. Model Provider Abstraction
Interface: generate(), stream(), embed(), classify(), score(), structured_output()
Providers: OpenAI-compatible (with fallback to mock), Anthropic-compatible, Google-compatible, custom HTTP, local model
Registry with capability map, routing by required capabilities.
User can configure providers, system not permanently dependent on one vendor.
Development fallback: MockProvider with deterministic outputs based on prompt keywords.

### 8. Tool System
Tools: read_file, write_file, edit_file, create_file, delete_file, list_directory, search_files, run_terminal, install_dependency, start_process, stop_process, run_tests, run_build, browser_open/click/type/screenshot (planned), web_search, save_memory, read_memory
Every tool returns structured result: {success, path, operation, timestamp, agent, decision_id, error, stdout, stderr, exit_code, duration}
Never silently fail.

### 9. Terminal Service
Integrated terminal, supports bash (Linux/macOS) and PowerShell (Windows where available).
AI agent executes through same controlled system.
Security: allowlist, dangerous pattern detection, path traversal prevention, secret detection, approval required for destructive commands.
Features: process tracking, timeout (120s default), output limit (1MB), logs, cancellation, duration.
Shows command, stdout, stderr, exit code, duration.

### 10. Event System
Every important operation emits event with id, project_id, type, timestamp, agent, decision_id, data, message.
Types: PROJECT_CREATED, RESEARCH_STARTED/COMPLETED, ABSTRACT_STARTED/GENERATED/REVISED/APPROVED, FRONTEND_STARTED, FILE_CREATED/EDITED/DELETED, COMMAND_STARTED/COMPLETED/FAILED, TEST_STARTED/PASSED/FAILED, DEBUG_STARTED, FIX_APPLIED, VERIFICATION_STARTED/COMPLETED, RLCD_DECISION, REWARD_RECORDED, AGENT_STARTED/COMPLETED, PRESENTATION_STARTED/COMPLETED, ERROR
Frontend receives via WebSocket /ws/projects/{id}, also via polling /api/projects/{id}/events.

### 11. Reward & Trajectory
RewardConfig with weights for positive (successful task, passing tests, correct implementation, verified source, user approval, efficient execution, integration) and negative (failed implementation, hallucinated info, fabricated sources, failed tests, unnecessary retries, excessive cost/latency, wrong routing, unverified claims).
Calculate reward from actual outcome.
Trajectory: STATE, ACTION, RESULT, REWARD, NEXT_STATE with decision_id, agent, tool_calls, latency, cost.
Stored as JSONL per project, used for offline RL.
Stats: success rate, avg reward, latency, cost.

### 12. Calibration & Evaluation
CalibrationStore with records, temperature, metrics: ECE, Brier Score, accuracy, confidence buckets, reliability data.
Evaluation dashboard shows decision accuracy, calibration error, Brier, success rate, routing accuracy, avg reward/latency/cost, human override rate, confidence histogram, reliability curve, reward history.
No hidden chain-of-thought, only decision metadata, reason codes, evidence.

### 13. Security Hardening
Workspace isolation per project, command allowlists, dangerous detection (rm -rf /, fork bomb, mkfs, dd, shutdown, etc), filesystem permission checks (resolve and startswith), env var protection (blocked list, redaction), secret detection (regex for OpenAI keys, GitHub PAT, AWS keys, private keys, hardcoded passwords), API-key protection (never expose to frontend), process timeout, memory limits, command cancellation, process logs.

### 14. Git Integration
Supports git status, diff, add, commit, branch, checkout, log via GitPython and subprocess. Displays in Source Control panel. File change history tracked separately with agent, timestamp, file, operation, old/new version, reason, decision ID, rollback support. Does not auto-push without permission.

### 15. Export & Packaging
Export project (zip with source, README, docs, abstract, architecture, tests, presentation, config, no secrets), export abstract, architecture, agent logs, trajectories, presentation, report.
Package generates project.zip with all artifacts.

### 16. Offline Mode
Optional offline mode where local filesystem, editor, terminal, project memory, local models, local RLCD decision model, tests, presentation generation work. Web research and cloud models unavailable, shows OFFLINE MODE, does not pretend web research succeeded.

## Data Flow

1. User creates project with problem statement
2. MasterAgent observes state (INITIAL)
3. RLCD decides RESEARCH or CREATE_ABSTRACT
4. ResearchAgent searches (mock or real), stores with sources
5. RLCD decides CREATE_ABSTRACT
6. AbstractAgent generates abstract, extracts requirements/actors/features/screens
7. AbstractCritic evaluates quality
8. RLCD decides APPROVE or REVISE (user approval gate)
9. User approves → store in memory, extract structured requirements
10. SolutionArchitect generates architecture
11. User says "Create frontend" → RLCD CREATE_FRONTEND → FrontendAgent inspects, plans, creates files, installs deps, builds, tests, fixes, verifies
12. User says "Create backend" → RLCD CREATE_BACKEND → BackendAgent creates API, DB, etc
13. Integration → Testing → Debugging → Verification (7 checks)
14. User says "Create presentation" → PresentationAgent reads actual project, generates PPTX with speaker notes
15. Final verification → COMPLETED
16. Export package

## Deployment

Backend: FastAPI + Uvicorn, serves frontend dist/, WebSocket, REST API
Frontend: Vite build to dist/, served by backend, also dev server with proxy to backend
Workspace: Local filesystem, per-project isolation
Data: JSON files for projects, JSONL for trajectories, JSON for calibration

## Model-Agnostic
No hard-coded vendor, capability-based routing, mock fallback, environment variable config for API keys.

## Verifiable
Never fake execution results. Build success means actual npm run build exit 0. Tests passing means actual test command exit 0. Files exist means real filesystem. All tracked with logs.

## Human-Controlled
Approval gates: abstract, architecture, frontend, backend, deployment, external submission. Buttons: APPROVE, REJECT, REQUEST REVISION, EDIT. User overrides recorded. Ask user when max iterations exceeded.

## Reproducible
ProjectState JSON, trajectory dataset, calibration data, file change history, decision logs, all persisted. Can export and replay.
