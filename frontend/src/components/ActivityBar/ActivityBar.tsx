import { 
  Files, Search, GitBranch, Bug, Puzzle, Bot, Settings, 
  FileText, BarChart3, Terminal as TerminalIcon
} from 'lucide-react'

interface Props {
  activeView: string
  onViewChange: (view: string) => void
}

const activities = [
  { id: 'explorer', icon: Files, label: 'Explorer' },
  { id: 'search', icon: Search, label: 'Search' },
  { id: 'git', icon: GitBranch, label: 'Source Control' },
  { id: 'debug', icon: Bug, label: 'Run and Debug' },
  { id: 'extensions', icon: Puzzle, label: 'Extensions' },
  { id: 'agents', icon: Bot, label: 'AI Agents' },
  { id: 'abstract', icon: FileText, label: 'Abstract' },
  { id: 'rlcd', icon: BarChart3, label: 'RLCD Evaluation' },
]

export function ActivityBar({ activeView, onViewChange }: Props) {
  return (
    <div className="w-[48px] bg-[#181818] border-r border-[#2d2d30] flex flex-col items-center py-2 gap-1">
      {activities.map(item => (
        <button
          key={item.id}
          onClick={() => onViewChange(item.id)}
          className={`w-[48px] h-[48px] flex items-center justify-center relative group transition-colors ${
            activeView === item.id 
              ? 'text-white' 
              : 'text-[#858585] hover:text-white'
          }`}
          title={item.label}
        >
          {activeView === item.id && (
            <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-[#007acc]"></div>
          )}
          <item.icon className="w-6 h-6" />
          <div className="absolute left-[56px] top-1/2 -translate-y-1/2 bg-[#252526] border border-[#454545] text-white text-[12px] px-2 py-1 rounded hidden group-hover:block whitespace-nowrap z-50">
            {item.label}
          </div>
        </button>
      ))}
      
      <div className="flex-1"></div>
      
      <button className="w-[48px] h-[48px] flex items-center justify-center text-[#858585] hover:text-white">
        <Settings className="w-6 h-6" />
      </button>
    </div>
  )
}
