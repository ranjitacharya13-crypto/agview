import { useState } from 'react'

interface Props {
  oldContent: string
  newContent: string
  path: string
  onAccept?: () => void
  onReject?: () => void
}

export function DiffViewer({ oldContent, newContent, path, onAccept, onReject }: Props) {
  const [view, setView] = useState<'split' | 'unified'>('split')

  const oldLines = oldContent.split('\n')
  const newLines = newContent.split('\n')

  return (
    <div className="flex flex-col h-full bg-[#1f1f1f]">
      <div className="h-[35px] bg-[#181818] border-b border-[#2d2d30] flex items-center px-3 justify-between">
        <span className="text-[13px]">Diff: {path}</span>
        <div className="flex items-center gap-2">
          <div className="flex bg-[#2d2d30] rounded text-[11px]">
            <button 
              onClick={() => setView('split')}
              className={`px-2 py-1 rounded ${view === 'split' ? 'bg-[#37373d] text-white' : 'text-[#858585]'}`}
            >
              Split
            </button>
            <button 
              onClick={() => setView('unified')}
              className={`px-2 py-1 rounded ${view === 'unified' ? 'bg-[#37373d] text-white' : 'text-[#858585]'}`}
            >
              Unified
            </button>
          </div>
          <button onClick={onAccept} className="px-3 py-1 bg-[#89d185] text-black rounded text-[12px]">Accept</button>
          <button onClick={onReject} className="px-3 py-1 bg-[#2d2d30] text-white rounded text-[12px]">Reject</button>
        </div>
      </div>

      <div className="flex-1 overflow-auto flex">
        {view === 'split' ? (
          <>
            <div className="flex-1 border-r border-[#2d2d30]">
              <div className="bg-[#2a1f1f] text-[#f85149] text-[11px] px-2 py-1 uppercase">Old</div>
              <pre className="p-2 text-[12px] font-mono text-[#cccccc] whitespace-pre-wrap">
                {oldLines.map((line, i) => (
                  <div key={i} className="flex">
                    <span className="text-[#858585] w-8 text-right mr-2 select-none">{i+1}</span>
                    <span>{line}</span>
                  </div>
                ))}
              </pre>
            </div>
            <div className="flex-1">
              <div className="bg-[#1f2a1f] text-[#89d185] text-[11px] px-2 py-1 uppercase">New</div>
              <pre className="p-2 text-[12px] font-mono text-[#cccccc] whitespace-pre-wrap">
                {newLines.map((line, i) => (
                  <div key={i} className="flex">
                    <span className="text-[#858585] w-8 text-right mr-2 select-none">{i+1}</span>
                    <span>{line}</span>
                  </div>
                ))}
              </pre>
            </div>
          </>
        ) : (
          <div className="flex-1">
            <pre className="p-2 text-[12px] font-mono">
              {oldLines.map((line, i) => {
                const newLine = newLines[i] || ''
                const changed = line !== newLine
                return (
                  <div key={i} className={changed ? 'bg-[#5a1d1d]/30' : ''}>
                    <span className="text-[#858585] w-8 inline-block text-right mr-2 select-none">{i+1}</span>
                    <span className="text-[#f85149]">- {line}</span>
                    {changed && <div><span className="text-[#858585] w-8 inline-block text-right mr-2"> </span><span className="text-[#89d185]">+ {newLine}</span></div>}
                  </div>
                )
              })}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
