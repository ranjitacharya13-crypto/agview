import { useState, useEffect } from 'react'
import { ActivityBar } from './components/ActivityBar/ActivityBar'
import { Explorer } from './components/Explorer/Explorer'
import { EditorArea } from './components/Editor/Editor'
import { TerminalPanel } from './components/Terminal/Terminal'
import { AgentPanel } from './components/AgentPanel/AgentPanel'
import { StatusBar } from './components/StatusBar/StatusBar'
import { ChatPanel } from './components/Chat/Chat'
import { useProjectStore } from './stores/projectStore'
import { useEditorStore } from './stores/editorStore'
import { useAgentStore } from './stores/agentStore'
import { projectApi, rlcdApi } from './services/api'
import { useRLCDStore } from './stores/rlcdStore'
import { ProjectWebSocket } from './services/websocket'
import { 
  Search, GitBranch, Bug, Puzzle, FileText, BarChart3, 
  Plus, FolderOpen, Settings, Command, Zap
} from 'lucide-react'

function App() {
  const [activeView, setActiveView] = useState('explorer')
  const [showCommandPalette, setShowCommandPalette] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [problemStatement, setProblemStatement] = useState('')
  const [showNewProject, setShowNewProject] = useState(false)
  
  const { currentProject, setCurrentProject, setProjects, events, addEvent, setEvents } = useProjectStore()
  const { fileTree } = useEditorStore()
  const { setCurrentAgent, setCurrentTask, setDecision, setRunning, addLog } = useAgentStore()
  const { setCalibration, setEvaluation, setActionSpace } = useRLCDStore()

  const [ws, setWs] = useState<ProjectWebSocket | null>(null)

  // Load projects on mount
  useEffect(() => {
    loadProjects()
    loadRLCDData()
    
    // Keyboard shortcut for command palette
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault()
        setShowCommandPalette(!showCommandPalette)
      }
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'P') {
        e.preventDefault()
        setShowCommandPalette(true)
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // WebSocket connection when project changes
  useEffect(() => {
    if (!currentProject) {
      if (ws) {
        ws.disconnect()
        setWs(null)
      }
      return
    }

    const websocket = new ProjectWebSocket(currentProject.project_id)
    websocket.connect()
    
    const unsubscribe = websocket.onEvent((event) => {
      addEvent(event)
      addLog(event.message)
      
      if (event.type === 'RLCD_DECISION' && event.data?.decision) {
        setDecision(event.data.decision)
      }
      
      if (event.agent) {
        setCurrentAgent(event.agent)
      }
      
      if (event.type === 'AGENT_STARTED') {
        setRunning(true)
        setCurrentTask(event.message)
      }
      
      if (event.type === 'AGENT_COMPLETED' || event.type === 'VERIFICATION_COMPLETED') {
        setRunning(false)
        // Reload project
        loadProject(currentProject.project_id)
      }
    })

    setWs(websocket)

    // Load events history
    projectApi.events(currentProject.project_id, 100).then(data => {
      if (data.success) {
        setEvents(data.events)
      }
    }).catch(() => {})

    return () => {
      unsubscribe()
      websocket.disconnect()
    }
  }, [currentProject?.project_id])

  const loadProjects = async () => {
    try {
      const data = await projectApi.list()
      if (data.success) {
        setProjects(data.projects)
        if (data.projects.length > 0 && !currentProject) {
          loadProject(data.projects[0].project_id)
        }
      }
    } catch (e) {
      console.error('Failed to load projects', e)
    }
  }

  const loadProject = async (id: string) => {
    try {
      const data = await projectApi.get(id)
      if (data.success) {
        setCurrentProject(data.project)
      }
    } catch (e) {
      console.error('Failed to load project', e)
    }
  }

  const loadRLCDData = async () => {
    try {
      const cal = await rlcdApi.calibration()
      if (cal.success) setCalibration(cal.calibration)
      
      const evalData = await rlcdApi.evaluation()
      if (evalData.success) setEvaluation(evalData.evaluation)
      
      const actions = await rlcdApi.actionSpace()
      if (actions.success) setActionSpace(actions.action_space)
    } catch (e) {
      console.error('Failed to load RLCD data', e)
    }
  }

  const handleCreateProject = async () => {
    if (!projectName.trim()) return
    
    try {
      const data = await projectApi.create(projectName, problemStatement)
      if (data.success) {
        setCurrentProject(data.project)
        setProjects([data.project, ...useProjectStore.getState().projects])
        setShowNewProject(false)
        setProjectName('')
        setProblemStatement('')
        addLog(`Project created: ${data.project.name}`)
      }
    } catch (e) {
      console.error('Failed to create project', e)
    }
  }

  const handleQuickAction = async (action: string) => {
    if (!currentProject) return
    
    setRunning(true)
    addLog(`Executing: ${action}`)
    
    try {
      let result
      switch (action) {
        case 'research':
          result = await projectApi.research(currentProject.project_id, currentProject.problem_statement)
          break
        case 'abstract':
          result = await projectApi.createAbstract(currentProject.project_id)
          break
        case 'solution':
          result = await projectApi.createSolution(currentProject.project_id)
          break
        case 'frontend':
          setCurrentAgent('frontend_agent')
          result = await projectApi.createFrontend(currentProject.project_id)
          break
        case 'backend':
          setCurrentAgent('backend_agent')
          result = await projectApi.createBackend(currentProject.project_id)
          break
        case 'test':
          result = await projectApi.test(currentProject.project_id)
          break
        case 'presentation':
          result = await projectApi.presentation(currentProject.project_id)
          break
        case 'verify':
          result = await projectApi.verify(currentProject.project_id)
          break
        default:
          result = await projectApi.master(currentProject.project_id, 'auto')
      }
      
      addLog(`Completed: ${action} - ${result.success ? 'Success' : 'Failed'}`)
      loadProject(currentProject.project_id)
      loadRLCDData()
    } catch (e: any) {
      addLog(`Error: ${action} - ${e.message}`)
    } finally {
      setRunning(false)
    }
  }

  const renderSidebar = () => {
    switch (activeView) {
      case 'explorer':
        return <Explorer projectId={currentProject?.project_id || ''} />
      case 'search':
        return (
          <div className="w-[260px] bg-[#181818] border-r border-[#2d2d30] p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wider mb-3">Search</div>
            <input 
              placeholder="Search files..." 
              className="w-full bg-[#1f1f1f] border border-[#3a3d41] rounded px-2 py-1 text-[13px] text-white"
            />
            <div className="mt-4 text-[12px] text-[#858585]">Search across real project files</div>
          </div>
        )
      case 'git':
        return (
          <div className="w-[260px] bg-[#181818] border-r border-[#2d2d30] p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wider mb-3 flex items-center gap-2">
              <GitBranch className="w-4 h-4" />
              Source Control
            </div>
            <div className="text-[12px] text-[#858585]">
              <div>Branch: main</div>
              <div className="mt-2">Changes: {currentProject?.file_changes?.length || 0}</div>
              <div className="mt-2 text-[11px] bg-[#1f1f1f] p-2 rounded border border-[#2d2d30]">
                {currentProject?.file_changes?.slice(-5).map((c, i) => (
                  <div key={i} className="truncate">{c.operation}: {c.path}</div>
                )) || 'No changes'}
              </div>
            </div>
          </div>
        )
      case 'debug':
        return (
          <div className="w-[260px] bg-[#181818] border-r border-[#2d2d30] p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wider mb-3 flex items-center gap-2">
              <Bug className="w-4 h-4" />
              Run and Debug
            </div>
            <button 
              onClick={() => handleQuickAction('test')}
              className="w-full bg-[#007acc] hover:bg-[#005a9e] text-white py-1.5 rounded text-[13px]"
            >
              Run Tests
            </button>
            <div className="mt-3 text-[12px] text-[#858585]">
              Debug real application with breakpoints
            </div>
          </div>
        )
      case 'extensions':
        return (
          <div className="w-[260px] bg-[#181818] border-r border-[#2d2d30] p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wider mb-3 flex items-center gap-2">
              <Puzzle className="w-4 h-4" />
              Extensions
            </div>
            <div className="text-[12px] text-[#858585]">Model providers, tools, agents</div>
          </div>
        )
      case 'agents':
        return null // Agent panel is on right
      case 'abstract':
        return (
          <div className="w-[320px] bg-[#181818] border-r border-[#2d2d30] flex flex-col">
            <div className="h-[35px] px-3 flex items-center border-b border-[#2d2d30]">
              <FileText className="w-4 h-4 mr-2" />
              <span className="text-[11px] font-semibold uppercase tracking-wider">Abstract</span>
            </div>
            <div className="flex-1 overflow-auto p-3">
              {currentProject?.abstract ? (
                <div className="space-y-3">
                  <div className="text-[13px] whitespace-pre-wrap text-[#cccccc] bg-[#1f1f1f] p-3 rounded border border-[#2d2d30]">
                    {currentProject.abstract}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => projectApi.approveAbstract(currentProject.project_id).then(() => loadProject(currentProject.project_id))}
                      className="px-3 py-1.5 bg-[#89d185] text-black rounded text-[12px] font-medium hover:bg-[#7bc67a]"
                    >
                      Approve
                    </button>
                    <button className="px-3 py-1.5 bg-[#2d2d30] text-white rounded text-[12px] hover:bg-[#37373d]">
                      Request Revision
                    </button>
                  </div>
                  <div className="text-[11px] text-[#858585]">
                    <div>Actors: {currentProject.actors?.join(', ') || 'N/A'}</div>
                    <div>Features: {currentProject.features?.join(', ') || 'N/A'}</div>
                    <div>Screens: {currentProject.screens?.join(', ') || 'N/A'}</div>
                  </div>
                </div>
              ) : (
                <div className="text-[12px] text-[#858585]">
                  No abstract yet. Create one from problem statement.
                  <button
                    onClick={() => handleQuickAction('abstract')}
                    className="mt-2 w-full bg-[#007acc] text-white py-1.5 rounded text-[12px]"
                  >
                    Generate Abstract
                  </button>
                </div>
              )}
            </div>
          </div>
        )
      case 'rlcd':
        return (
          <div className="w-[320px] bg-[#181818] border-r border-[#2d2d30] p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wider mb-3 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              RLCD Evaluation
            </div>
            <div className="space-y-3 text-[11px]">
              <div className="bg-[#1f1f1f] p-2 rounded border border-[#2d2d30]">
                <div className="font-semibold mb-1">Development Policy Active</div>
                <div className="text-[#858585]">Deterministic fallback with trainable architecture ready. Trajectories collected for offline RL.</div>
              </div>
              <button
                onClick={loadRLCDData}
                className="w-full bg-[#2d2d30] hover:bg-[#37373d] text-white py-1.5 rounded text-[12px]"
              >
                Refresh Metrics
              </button>
            </div>
          </div>
        )
      default:
        return <Explorer projectId={currentProject?.project_id || ''} />
    }
  }

  return (
    <div className="h-screen w-screen bg-[#0e0e10] text-[#cccccc] flex flex-col overflow-hidden">
      {/* Title Bar */}
      <div className="h-[30px] bg-[#181818] flex items-center px-3 text-[12px] border-b border-[#2d2d30] select-none">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#ff5f56]"></div>
          <div className="w-3 h-3 rounded-full bg-[#ffbd2e]"></div>
          <div className="w-3 h-3 rounded-full bg-[#27c93f]"></div>
        </div>
        <div className="flex-1 flex items-center justify-center gap-4">
          <span className="text-[#cccccc]">RLCD Agentic Engineering IDE</span>
          <span className="text-[#858585]">—</span>
          <span className="text-[#858585]">{currentProject?.name || 'No Project'}</span>
          {currentProject && (
            <>
              <span className="text-[#858585]">—</span>
              <span className="text-[#858585] bg-[#2d2d30] px-2 py-0.5 rounded text-[11px]">{currentProject.stage}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowNewProject(true)}
            className="px-2 py-0.5 bg-[#007acc] hover:bg-[#005a9e] text-white rounded text-[11px] flex items-center gap-1"
          >
            <Plus className="w-3 h-3" />
            New Project
          </button>
        </div>
      </div>

      {/* Menu Bar */}
      <div className="h-[30px] bg-[#181818] flex items-center px-2 text-[12px] gap-1 border-b border-[#2d2d30]">
        {['File', 'Edit', 'View', 'Run', 'Terminal', 'Help'].map(item => (
          <span key={item} className="px-2 py-1 hover:bg-[#2a2d2e] rounded cursor-pointer text-[#cccccc]">{item}</span>
        ))}
        <div className="flex-1"></div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <input
              placeholder="Search or run command (Ctrl+P)"
              className="w-[300px] bg-[#1f1f1f] border border-[#3a3d41] rounded px-3 py-1 text-[12px] text-[#cccccc] placeholder:text-[#858585] focus:border-[#007acc] outline-none"
              onFocus={() => setShowCommandPalette(true)}
            />
            <Command className="w-3 h-3 absolute right-2 top-1/2 -translate-y-1/2 text-[#858585]" />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        <ActivityBar activeView={activeView} onViewChange={setActiveView} />
        
        {renderSidebar()}

        <div className="flex-1 flex flex-col min-w-0">
          {/* Quick Actions Bar */}
          {currentProject && (
            <div className="h-[35px] bg-[#181818] border-b border-[#2d2d30] flex items-center px-3 gap-2 overflow-x-auto">
              <span className="text-[11px] text-[#858585] uppercase tracking-wider mr-2">Quick Actions:</span>
              {[
                { id: 'research', label: 'Research' },
                { id: 'abstract', label: 'Abstract' },
                { id: 'solution', label: 'Architecture' },
                { id: 'frontend', label: 'Frontend' },
                { id: 'backend', label: 'Backend' },
                { id: 'test', label: 'Test' },
                { id: 'verify', label: 'Verify' },
                { id: 'presentation', label: 'Presentation' }
              ].map(action => (
                <button
                  key={action.id}
                  onClick={() => handleQuickAction(action.id)}
                  className="px-2.5 py-1 bg-[#2d2d30] hover:bg-[#37373d] text-[#cccccc] rounded text-[11px] whitespace-nowrap flex items-center gap-1"
                >
                  <Zap className="w-3 h-3" />
                  {action.label}
                </button>
              ))}
              <div className="flex-1"></div>
              <span className="text-[10px] text-[#858585]">Problem: {currentProject.problem_statement.slice(0, 50)}...</span>
            </div>
          )}

          <div className="flex-1 flex min-h-0">
            <EditorArea projectId={currentProject?.project_id || ''} />
            
            {(activeView === 'agents' || activeView === 'explorer') && (
              <AgentPanel projectId={currentProject?.project_id || ''} />
            )}
          </div>

          <TerminalPanel projectId={currentProject?.project_id || ''} />
        </div>

        {/* Chat Panel - shown when agents view active */}
        {activeView === 'agents' && (
          <ChatPanel projectId={currentProject?.project_id || ''} onProjectUpdate={() => currentProject && loadProject(currentProject.project_id)} />
        )}
      </div>

      <StatusBar 
        project={currentProject} 
        branch="main" 
        language={fileTree ? 'TypeScript' : 'No File'}
        agentStatus={useAgentStore.getState().currentAgent || 'Idle'}
        backendConnected={true}
      />

      {/* New Project Modal */}
      {showNewProject && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#252526] border border-[#454545] rounded shadow-xl w-[500px] p-4">
            <h2 className="text-[14px] font-semibold mb-4">Create New Project</h2>
            
            <div className="space-y-3">
              <div>
                <label className="text-[12px] text-[#cccccc] block mb-1">Project Name</label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Smart Greenhouse Monitoring"
                  className="w-full bg-[#1f1f1f] border border-[#3a3d41] rounded px-3 py-2 text-[13px] text-white focus:border-[#007acc] outline-none"
                />
              </div>
              
              <div>
                <label className="text-[12px] text-[#cccccc] block mb-1">Problem Statement</label>
                <textarea
                  value={problemStatement}
                  onChange={(e) => setProblemStatement(e.target.value)}
                  placeholder="Create a web application for a smart greenhouse that monitors temperature, humidity, soil moisture and automatically controls irrigation."
                  className="w-full bg-[#1f1f1f] border border-[#3a3d41] rounded px-3 py-2 text-[13px] text-white focus:border-[#007acc] outline-none h-[100px] resize-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => setShowNewProject(false)}
                className="px-4 py-1.5 bg-[#2d2d30] hover:bg-[#37373d] text-white rounded text-[13px]"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateProject}
                disabled={!projectName.trim()}
                className="px-4 py-1.5 bg-[#007acc] hover:bg-[#005a9e] disabled:bg-[#2d2d30] disabled:text-[#858585] text-white rounded text-[13px]"
              >
                Create Project
              </button>
            </div>

            <div className="mt-4 p-2 bg-[#1f1f1f] rounded border border-[#2d2d30] text-[11px] text-[#858585]">
              <div className="font-semibold text-[#cccccc] mb-1">Acceptance Test Example:</div>
              "Create a web application for a smart greenhouse that monitors temperature, humidity, soil moisture and automatically controls irrigation."
            </div>
          </div>
        </div>
      )}

      {/* Command Palette */}
      {showCommandPalette && (
        <div className="fixed inset-0 bg-black/30 flex items-start justify-center pt-[20vh] z-50">
          <div className="bg-[#252526] border border-[#454545] rounded shadow-2xl w-[600px] overflow-hidden">
            <div className="flex items-center px-3 py-2 border-b border-[#454545]">
              <Search className="w-4 h-4 text-[#858585] mr-2" />
              <input
                autoFocus
                placeholder="Type a command or search..."
                className="flex-1 bg-transparent outline-none text-[14px] text-white placeholder:text-[#858585]"
              />
              <button
                onClick={() => setShowCommandPalette(false)}
                className="ml-2 text-[#858585] hover:text-white"
              >
                ESC
              </button>
            </div>
            <div className="max-h-[300px] overflow-auto p-2">
              {[
                { label: 'Create New Project', action: () => { setShowNewProject(true); setShowCommandPalette(false) } },
                { label: 'Research Problem', action: () => { handleQuickAction('research'); setShowCommandPalette(false) } },
                { label: 'Generate Abstract', action: () => { handleQuickAction('abstract'); setShowCommandPalette(false) } },
                { label: 'Create Frontend', action: () => { handleQuickAction('frontend'); setShowCommandPalette(false) } },
                { label: 'Create Backend', action: () => { handleQuickAction('backend'); setShowCommandPalette(false) } },
                { label: 'Run Tests', action: () => { handleQuickAction('test'); setShowCommandPalette(false) } },
                { label: 'Create Presentation', action: () => { handleQuickAction('presentation'); setShowCommandPalette(false) } },
                { label: 'Verify Project', action: () => { handleQuickAction('verify'); setShowCommandPalette(false) } },
              ].map((cmd, i) => (
                <div
                  key={i}
                  onClick={cmd.action}
                  className="px-3 py-2 hover:bg-[#2a2d2e] rounded cursor-pointer flex items-center gap-2 text-[13px]"
                >
                  <Command className="w-4 h-4 text-[#858585]" />
                  <span>{cmd.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* No Project Overlay */}
      {!currentProject && (
        <div className="fixed bottom-[22px] left-[48px] right-0 top-[60px] bg-[#1f1f1f]/90 backdrop-blur-sm flex items-center justify-center">
          <div className="text-center p-8 bg-[#181818] border border-[#2d2d30] rounded shadow-xl max-w-[500px]">
            <div className="w-16 h-16 mx-auto mb-4 bg-[#007acc] rounded flex items-center justify-center">
              <FolderOpen className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-[16px] font-semibold text-white mb-2">No Project Open</h2>
            <p className="text-[13px] text-[#858585] mb-4">
              Create a new project to start building with autonomous agents.
              The system will handle research, abstract, architecture, frontend, backend, testing, and presentation.
            </p>
            <button
              onClick={() => setShowNewProject(true)}
              className="px-4 py-2 bg-[#007acc] hover:bg-[#005a9e] text-white rounded text-[13px] flex items-center gap-2 mx-auto"
            >
              <Plus className="w-4 h-4" />
              Create New Project
            </button>
            <div className="mt-4 text-[11px] text-[#858585] text-left bg-[#0e0e10] p-3 rounded border border-[#2d2d30]">
              <div className="font-semibold text-[#cccccc] mb-1">Try the acceptance test:</div>
              "Create a web application for a smart greenhouse that monitors temperature, humidity, soil moisture and automatically controls irrigation."
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
