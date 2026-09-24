import { useState, useEffect } from 'react'
import { GitBranch, GitCommit, Plus, Minus, File } from 'lucide-react'
import { gitApi } from '../../services/api'
import { Project } from '../../types'

interface Props {
  projectId: string
  project: Project | null
}

export function SourceControl({ projectId, project }: Props) {
  const [status, setStatus] = useState('')
  const [log, setLog] = useState<any[]>([])
  const [commitMessage, setCommitMessage] = useState('')

  useEffect(() => {
    if (!projectId) return
    loadStatus()
    loadLog()
  }, [projectId, project?.file_changes?.length])

  const loadStatus = async () => {
    try {
      const data = await gitApi.status(projectId)
      if (data.success) {
        setStatus(data.status)
      }
    } catch (e) {
      console.error('Git status failed', e)
    }
  }

  const loadLog = async () => {
    try {
      const data = await gitApi.log(projectId)
      if (data.success) {
        setLog(data.log)
      }
    } catch (e) {
      console.error('Git log failed', e)
    }
  }

  const handleCommit = async () => {
    if (!commitMessage.trim()) return
    try {
      await gitApi.commit(projectId, commitMessage)
      setCommitMessage('')
      loadStatus()
      loadLog()
    } catch (e) {
      console.error('Commit failed', e)
    }
  }

  return (
    <div className="w-[260px] bg-[#181818] border-r border-[#2d2d30] flex flex-col h-full">
      <div className="h-[35px] px-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider border-b border-[#2d2d30]">
        <GitBranch className="w-4 h-4" />
        Source Control
      </div>

      <div className="p-3">
        <div className="flex items-center gap-2 mb-3">
          <input
            value={commitMessage}
            onChange={(e) => setCommitMessage(e.target.value)}
            placeholder="Message (Ctrl+Enter to commit)"
            className="flex-1 bg-[#1f1f1f] border border-[#3a3d41] rounded px-2 py-1 text-[12px] text-white focus:border-[#007acc] outline-none"
          />
          <button
            onClick={handleCommit}
            className="p-1.5 bg-[#007acc] hover:bg-[#005a9e] text-white rounded"
            title="Commit"
          >
            <GitCommit className="w-4 h-4" />
          </button>
        </div>

        <div className="text-[11px] font-semibold uppercase tracking-wider text-[#bbbbbb] mb-2">
          Changes ({project?.file_changes?.length || 0})
        </div>

        <div className="space-y-1 max-h-[200px] overflow-auto mb-4">
          {project?.file_changes?.slice(-20).reverse().map(change => (
            <div key={change.id} className="flex items-center gap-2 text-[12px] py-1 hover:bg-[#2a2d2e] rounded px-1">
              {change.operation === 'CREATE' ? (
                <Plus className="w-3 h-3 text-[#89d185]" />
              ) : change.operation === 'DELETE' ? (
                <Minus className="w-3 h-3 text-[#f85149]" />
              ) : (
                <File className="w-3 h-3 text-[#cca700]" />
              )}
              <span className="truncate text-[#cccccc]">{change.path}</span>
              <span className="text-[10px] text-[#858585] ml-auto">{change.agent}</span>
            </div>
          ))}
          {(!project?.file_changes || project.file_changes.length === 0) && (
            <div className="text-[11px] text-[#858585]">No changes</div>
          )}
        </div>

        {status && (
          <div className="mb-4">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-[#bbbbbb] mb-1">Git Status</div>
            <pre className="text-[11px] bg-[#1f1f1f] p-2 rounded border border-[#2d2d30] whitespace-pre-wrap text-[#cccccc]">
              {status || 'Clean'}
            </pre>
          </div>
        )}

        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[#bbbbbb] mb-2">File History</div>
          <div className="space-y-2 max-h-[200px] overflow-auto">
            {log.slice(0, 10).map((entry, i) => (
              <div key={i} className="text-[11px] border-l-2 border-[#007acc] pl-2 py-1">
                <div className="text-[#cccccc] truncate">{entry.path}</div>
                <div className="text-[#858585] text-[10px]">{entry.operation} by {entry.agent}</div>
                <div className="text-[#858585] text-[10px]">{new Date(entry.timestamp).toLocaleString()}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-auto p-3 border-t border-[#2d2d30] text-[11px] text-[#858585]">
        <div>Branch: main</div>
        <div>Does not auto-push without permission</div>
      </div>
    </div>
  )
}
