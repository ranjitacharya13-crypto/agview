import { useState, useEffect, useRef } from 'react'
import { Terminal as TerminalIcon, X, Trash2, Plus } from 'lucide-react'
import { terminalApi } from '../../services/api'
import { useTerminalStore } from '../../stores/terminalStore'

interface Props {
  projectId: string
}

export function TerminalPanel({ projectId }: Props) {
  const [input, setInput] = useState('')
  const [history, setHistory] = useState<{command: string, output: string, error?: string, success: boolean}[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const terminalRef = useRef<HTMLDivElement>(null)

  const { processes } = useTerminalStore()

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [history])

  const executeCommand = async (cmd: string) => {
    if (!cmd.trim() || !projectId) return
    
    setIsRunning(true)
    const newEntry = { command: cmd, output: 'Running...', success: true }
    setHistory(prev => [...prev, newEntry])

    try {
      const result = await terminalApi.execute(projectId, cmd)
      
      setHistory(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          command: cmd,
          output: result.stdout || result.stderr || (result.success ? 'Command completed' : 'Command failed'),
          error: result.success ? undefined : result.stderr,
          success: result.success
        }
        return updated
      })
    } catch (e: any) {
      setHistory(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          command: cmd,
          output: e.response?.data?.detail || e.message || 'Error',
          success: false
        }
        return updated
      })
    } finally {
      setIsRunning(false)
      setInput('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      executeCommand(input)
    }
  }

  return (
    <div className="h-[300px] bg-[#181818] border-t border-[#2d2d30] flex flex-col">
      {/* Header */}
      <div className="h-[35px] flex items-center justify-between px-3 bg-[#181818] border-b border-[#2d2d30]">
        <div className="flex items-center gap-4 text-[11px] uppercase">
          <span className="flex items-center gap-1 text-white border-b border-white pb-[2px]">
            <TerminalIcon className="w-4 h-4" />
            Terminal
          </span>
          <span className="text-[#858585] hover:text-[#cccccc] cursor-pointer">Problems</span>
          <span className="text-[#858585] hover:text-[#cccccc] cursor-pointer">Output</span>
          <span className="text-[#858585] hover:text-[#cccccc] cursor-pointer">Debug Console</span>
          <span className="text-[#858585] hover:text-[#cccccc] cursor-pointer">Agent Logs</span>
        </div>
        <div className="flex items-center gap-1">
          <button 
            onClick={() => setHistory([])}
            className="p-1 hover:bg-[#2a2d2e] rounded text-[#858585] hover:text-white"
            title="Clear"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button className="p-1 hover:bg-[#2a2d2e] rounded text-[#858585] hover:text-white">
            <Plus className="w-4 h-4" />
          </button>
          <button className="p-1 hover:bg-[#2a2d2e] rounded text-[#858585] hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Terminal Content */}
      <div ref={terminalRef} className="flex-1 overflow-auto p-3 font-mono text-[13px] bg-[#1f1f1f]">
        {history.length === 0 && (
          <div className="text-[#858585] text-[12px] mb-2">
            Integrated terminal - runs actual commands in workspace sandbox<br/>
            Try: npm install, npm run build, npm run dev, ls, cat package.json<br/>
            Security: dangerous commands blocked, secrets redacted, path traversal prevented
          </div>
        )}
        
        {history.map((entry, i) => (
          <div key={i} className="mb-3">
            <div className="flex items-center gap-2 text-[#cccccc]">
              <span className="text-[#89d185]">$</span>
              <span>{entry.command}</span>
            </div>
            <div className={`mt-1 whitespace-pre-wrap break-words text-[12px] ${
              entry.success ? 'text-[#cccccc]' : 'text-[#f85149]'
            }`}>
              {entry.output}
            </div>
          </div>
        ))}

        {/* Processes from backend */}
        {processes.length > 0 && (
          <div className="mt-4 border-t border-[#2d2d30] pt-2">
            <div className="text-[11px] uppercase text-[#858585] mb-2">Recent Processes</div>
            {processes.slice(0, 5).map(proc => (
              <div key={proc.id} className="text-[11px] text-[#858585] flex gap-2">
                <span className={proc.status === 'completed' ? 'text-[#89d185]' : 'text-[#cca700]'}>●</span>
                <span>{proc.command}</span>
                <span>({proc.duration_ms}ms)</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="h-[30px] flex items-center px-3 bg-[#1f1f1f] border-t border-[#2d2d30]">
        <span className="text-[#89d185] mr-2 font-mono text-[13px]">$</span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isRunning || !projectId}
          placeholder={projectId ? "Enter command..." : "No project selected"}
          className="flex-1 bg-transparent outline-none text-[#cccccc] font-mono text-[13px] placeholder:text-[#858585]"
        />
        {isRunning && <span className="text-[11px] text-[#858585]">Running...</span>}
      </div>
    </div>
  )
}
