import { GitBranch, AlertCircle, CheckCircle, Wifi, Cpu, Database } from 'lucide-react'
import { Project } from '../../types'

interface Props {
  project: Project | null
  branch?: string
  language?: string
  agentStatus?: string
  backendConnected?: boolean
}

export function StatusBar({ project, branch = 'main', language = 'TypeScript', agentStatus = 'Idle', backendConnected = true }: Props) {
  return (
    <div className="h-[22px] bg-[#007acc] text-white flex items-center px-2 text-[12px] gap-4">
      <div className="flex items-center gap-1">
        <GitBranch className="w-3 h-3" />
        <span>{branch}</span>
      </div>

      <div className="flex items-center gap-1">
        {project?.verification?.frontend_build ? (
          <CheckCircle className="w-3 h-3" />
        ) : (
          <AlertCircle className="w-3 h-3" />
        )}
        <span>{project?.stage || 'No Project'}</span>
      </div>

      <div className="flex-1"></div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <span>{language}</span>
        </div>
        
        <div className="flex items-center gap-1">
          <span>UTF-8</span>
        </div>

        <div className="flex items-center gap-1">
          <span>Ln 1, Col 1</span>
        </div>

        <div className="flex items-center gap-1">
          <Cpu className="w-3 h-3" />
          <span>{agentStatus}</span>
        </div>

        <div className="flex items-center gap-1">
          <Database className="w-3 h-3" />
          <span className={backendConnected ? '' : 'text-[#f85149]'}>Backend: {backendConnected ? 'Connected' : 'Offline'}</span>
        </div>

        <div className="flex items-center gap-1">
          <Wifi className="w-3 h-3" />
          <span>Model: Mock (Dev)</span>
        </div>

        <div className="flex items-center gap-1">
          <span>Calibration: Active</span>
        </div>
      </div>
    </div>
  )
}
