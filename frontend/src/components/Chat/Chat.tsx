import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, Loader2 } from 'lucide-react'
import { projectApi } from '../../services/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  action?: string
}

interface Props {
  projectId: string
  onProjectUpdate?: () => void
}

export function ChatPanel({ projectId, onProjectUpdate }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I am your RLCD Agentic IDE assistant. I can help you build applications.\n\nTry commands like:\n- "Create a web application for a smart greenhouse"\n- "Research this problem"\n- "Create the frontend"\n- "Create the backend"\n- "Run the tests"\n- "Create presentation"\n- "Fix this error"',
      timestamp: new Date().toISOString()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || !projectId || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const result = await projectApi.chat(projectId, userMessage.content)
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Action: ${result.action}\n\nResult: ${JSON.stringify(result.result, null, 2).slice(0, 1000)}${JSON.stringify(result.result, null, 2).length > 1000 ? '...' : ''}`,
        timestamp: new Date().toISOString(),
        action: result.action
      }

      setMessages(prev => [...prev, assistantMessage])
      
      if (onProjectUpdate) {
        onProjectUpdate()
      }
    } catch (e: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${e.response?.data?.detail || e.message || 'Failed to process command'}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const quickCommands = [
    "Create abstract for this problem",
    "Research this problem",
    "Create solution architecture",
    "Create frontend",
    "Create backend",
    "Run tests",
    "Create presentation",
    "Verify project"
  ]

  return (
    <div className="w-[320px] bg-[#181818] border-l border-[#2d2d30] flex flex-col h-full">
      <div className="h-[35px] px-3 flex items-center gap-2 border-b border-[#2d2d30]">
        <Bot className="w-4 h-4 text-[#007acc]" />
        <span className="text-[11px] font-semibold uppercase tracking-wider">AI Chat</span>
        <div className="ml-auto flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-[#cca700]" />
          <span className="text-[10px] text-[#858585]">RLCD</span>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-3 space-y-3">
        {messages.map(msg => (
          <div key={msg.id} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-6 h-6 rounded-full bg-[#007acc] flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}
            <div className={`max-w-[240px] rounded p-2 text-[12px] whitespace-pre-wrap break-words ${
              msg.role === 'user' 
                ? 'bg-[#007acc] text-white' 
                : 'bg-[#1f1f1f] border border-[#2d2d30] text-[#cccccc]'
            }`}>
              {msg.content}
              {msg.action && (
                <div className="mt-2 text-[10px] px-2 py-1 bg-[#2d2d30] rounded inline-block">
                  {msg.action}
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-6 h-6 rounded-full bg-[#2d2d30] flex items-center justify-center flex-shrink-0 mt-1">
                <User className="w-4 h-4 text-[#cccccc]" />
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full bg-[#007acc] flex items-center justify-center">
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            </div>
            <div className="bg-[#1f1f1f] border border-[#2d2d30] rounded p-2 text-[12px] text-[#858585]">
              Agent thinking...
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="p-2 border-t border-[#2d2d30]">
        <div className="text-[10px] text-[#858585] mb-2 uppercase tracking-wider">Quick Commands</div>
        <div className="flex flex-wrap gap-1 mb-2">
          {quickCommands.slice(0, 4).map(cmd => (
            <button
              key={cmd}
              onClick={() => setInput(cmd)}
              className="text-[10px] px-2 py-1 bg-[#2d2d30] hover:bg-[#37373d] text-[#cccccc] rounded"
            >
              {cmd}
            </button>
          ))}
        </div>
      </div>

      <div className="p-3 border-t border-[#2d2d30]">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={projectId ? "Ask agent..." : "Select project first"}
            disabled={!projectId || isLoading}
            className="flex-1 bg-[#1f1f1f] border border-[#3a3d41] rounded px-3 py-2 text-[13px] text-[#cccccc] placeholder:text-[#858585] resize-none outline-none focus:border-[#007acc] min-h-[40px] max-h-[100px]"
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !projectId || isLoading}
            className="w-8 h-8 bg-[#007acc] hover:bg-[#005a9e] disabled:bg-[#2d2d30] disabled:text-[#858585] text-white rounded flex items-center justify-center flex-shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="text-[10px] text-[#858585] mt-2">
          Context-aware: current file, terminal, project state
        </div>
      </div>
    </div>
  )
}
