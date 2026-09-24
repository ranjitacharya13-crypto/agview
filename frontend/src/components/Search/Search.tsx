import { useState } from 'react'
import { Search as SearchIcon, File, Replace } from 'lucide-react'
import { filesystemApi } from '../../services/api'

interface Props {
  projectId: string
  onFileOpen?: (path: string) => void
}

export function SearchPanel({ projectId, onFileOpen }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    if (!query.trim() || !projectId) return
    setLoading(true)
    try {
      const data = await filesystemApi.search(projectId, query)
      if (data.success) {
        setResults(data.results)
      }
    } catch (e) {
      console.error('Search failed', e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-[260px] bg-[#181818] border-r border-[#2d2d30] flex flex-col h-full">
      <div className="h-[35px] px-3 flex items-center text-[11px] font-semibold uppercase tracking-wider">
        Search
      </div>

      <div className="p-3 space-y-2">
        <div className="relative">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search"
            className="w-full bg-[#1f1f1f] border border-[#3a3d41] rounded px-2 py-1 pr-8 text-[13px] text-white focus:border-[#007acc] outline-none"
          />
          <SearchIcon className="w-4 h-4 absolute right-2 top-1/2 -translate-y-1/2 text-[#858585]" />
        </div>

        <div className="relative">
          <input
            placeholder="Replace"
            className="w-full bg-[#1f1f1f] border border-[#3a3d41] rounded px-2 py-1 pr-8 text-[13px] text-white focus:border-[#007acc] outline-none"
          />
          <Replace className="w-4 h-4 absolute right-2 top-1/2 -translate-y-1/2 text-[#858585]" />
        </div>

        <div className="flex gap-2 text-[11px]">
          <label className="flex items-center gap-1 text-[#cccccc]">
            <input type="checkbox" className="w-3 h-3" /> Match Case
          </label>
          <label className="flex items-center gap-1 text-[#cccccc]">
            <input type="checkbox" className="w-3 h-3" /> Whole Word
          </label>
        </div>

        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="w-full bg-[#2d2d30] hover:bg-[#37373d] disabled:bg-[#1f1f1f] disabled:text-[#858585] text-white py-1 rounded text-[12px]"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      <div className="flex-1 overflow-auto p-2">
        {results.length > 0 ? (
          <div className="space-y-2">
            <div className="text-[11px] text-[#858585]">{results.length} results in {results.length} files</div>
            {results.map((result, i) => (
              <div key={i} className="text-[12px]">
                <div className="flex items-center gap-1 text-[#cccccc] font-medium">
                  <File className="w-3 h-3" />
                  {result.name}
                </div>
                <div className="ml-4 text-[11px] text-[#858585] truncate">{result.path}</div>
                {result.lines?.map((line: any, j: number) => (
                  <div 
                    key={j} 
                    className="ml-4 mt-1 p-1 hover:bg-[#2a2d2e] cursor-pointer rounded text-[11px]"
                    onClick={() => onFileOpen?.(result.path)}
                  >
                    <span className="text-[#858585]">{line.line}:</span> {line.content}
                  </div>
                ))}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-[11px] text-[#858585] p-2">
            Search across real project files. Results show filename and content matches with line numbers.
          </div>
        )}
      </div>
    </div>
  )
}
