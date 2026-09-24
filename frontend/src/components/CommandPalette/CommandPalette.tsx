import { useState, useEffect } from 'react'
import { Search, Command } from 'lucide-react'

interface CommandItem {
  id: string
  label: string
  category: string
  action: () => void
}

interface Props {
  open: boolean
  onClose: () => void
  commands: CommandItem[]
}

export function CommandPalette({ open, onClose, commands }: Props) {
  const [query, setQuery] = useState('')

  useEffect(() => {
    if (!open) setQuery('')
  }, [open])

  if (!open) return null

  const filtered = commands.filter(c => 
    c.label.toLowerCase().includes(query.toLowerCase()) ||
    c.category.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center pt-[20vh] z-50" onClick={onClose}>
      <div className="bg-[#252526] border border-[#454545] rounded shadow-2xl w-[600px] overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center px-3 py-2 border-b border-[#454545]">
          <Search className="w-4 h-4 text-[#858585] mr-2" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent outline-none text-[14px] text-white placeholder:text-[#858585]"
          />
        </div>
        <div className="max-h-[300px] overflow-auto p-2">
          {filtered.map(cmd => (
            <div
              key={cmd.id}
              onClick={() => { cmd.action(); onClose() }}
              className="px-3 py-2 hover:bg-[#2a2d2e] rounded cursor-pointer flex items-center gap-2 text-[13px]"
            >
              <Command className="w-4 h-4 text-[#858585]" />
              <span className="text-[#858585] text-[11px]">{cmd.category}</span>
              <span>{cmd.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
