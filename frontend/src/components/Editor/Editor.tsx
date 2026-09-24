import { useEffect, useRef } from 'react'
import Editor, { OnMount } from '@monaco-editor/react'
import { X, Circle } from 'lucide-react'
import { useEditorStore } from '../../stores/editorStore'
import { filesystemApi } from '../../services/api'

interface Props {
  projectId: string
}

export function EditorArea({ projectId }: Props) {
  const { tabs, activeTabId, setActiveTab, closeTab, updateTabContent } = useEditorStore()
  const editorRef = useRef<any>(null)

  const activeTab = tabs.find(t => t.id === activeTabId)

  const handleEditorMount: OnMount = (editor) => {
    editorRef.current = editor
    
    // VS Code keybindings
    editor.addCommand(2048 | 49, () => { // Ctrl+S
      handleSave()
    })
  }

  const handleSave = async () => {
    if (!activeTab || !projectId) return
    
    try {
      await filesystemApi.write(projectId, activeTab.path, activeTab.content, 'user')
      updateTabContent(activeTab.id, activeTab.content, false)
    } catch (e) {
      console.error('Save failed', e)
    }
  }

  const handleContentChange = (value: string | undefined) => {
    if (!activeTab || value === undefined) return
    updateTabContent(activeTab.id, value, value !== activeTab.content)
  }

  // Auto-save
  useEffect(() => {
    if (!activeTab?.dirty) return
    const timeout = setTimeout(() => {
      handleSave()
    }, 1000)
    return () => clearTimeout(timeout)
  }, [activeTab?.content])

  if (tabs.length === 0) {
    return (
      <div className="flex-1 bg-[#1f1f1f] flex items-center justify-center">
        <div className="text-center max-w-[400px] p-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-[#2d2d30] rounded flex items-center justify-center">
            <span className="text-2xl">📁</span>
          </div>
          <h2 className="text-[16px] font-semibold text-white mb-2">RLCD Agentic Engineering IDE</h2>
          <p className="text-[13px] text-[#858585] mb-4">
            A VS Code-style AI-native development environment with autonomous coding agents, 
            calibrated decision engine, and real file operations.
          </p>
          <div className="text-[12px] text-[#858585] space-y-1 text-left bg-[#181818] p-3 rounded border border-[#2d2d30]">
            <div>✓ Real filesystem integration</div>
            <div>✓ Monaco editor with syntax highlighting</div>
            <div>✓ Integrated terminal</div>
            <div>✓ RLCD decision engine (CHOICE/SCORE/NOUL)</div>
            <div>✓ Autonomous agents (Frontend, Backend, Research)</div>
            <div>✓ Project memory & trajectory tracking</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 bg-[#1f1f1f] flex flex-col min-w-0">
      {/* Tabs */}
      <div className="h-[35px] bg-[#181818] flex items-center overflow-x-auto border-b border-[#2d2d30] scrollbar-thin">
        {tabs.map(tab => (
          <div
            key={tab.id}
            className={`h-full flex items-center gap-2 px-3 border-r border-[#2d2d30] cursor-pointer text-[13px] min-w-[120px] max-w-[200px] group ${
              activeTabId === tab.id 
                ? 'bg-[#1f1f1f] text-white border-t border-t-[#007acc]' 
                : 'bg-[#2d2d2d] text-[#969696] hover:text-[#cccccc]'
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="truncate flex-1">{tab.name}</span>
            {tab.dirty ? (
              <Circle className="w-3 h-3 fill-[#cccccc] text-[#cccccc]" />
            ) : (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  closeTab(tab.id)
                }}
                className="p-0.5 hover:bg-[#464647] rounded opacity-60 group-hover:opacity-100"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Breadcrumbs */}
      {activeTab && (
        <div className="h-[22px] bg-[#1f1f1f] px-3 flex items-center text-[12px] text-[#858585] border-b border-[#2d2d30]">
          <span>{activeTab.path}</span>
        </div>
      )}

      {/* Editor */}
      <div className="flex-1 min-h-0">
        {activeTab ? (
          <Editor
            height="100%"
            language={activeTab.language}
            value={activeTab.content}
            onChange={handleContentChange}
            onMount={handleEditorMount}
            theme="vs-dark"
            options={{
              fontSize: 14,
              fontFamily: 'Cascadia Code, Consolas, monospace',
              minimap: { enabled: true },
              scrollBeyondLastLine: false,
              wordWrap: 'on',
              lineNumbers: 'on',
              folding: true,
              bracketPairColorization: { enabled: true },
              autoClosingBrackets: 'always',
              formatOnType: true,
              tabSize: 2,
              cursorBlinking: 'smooth',
              smoothScrolling: true,
              mouseWheelZoom: true
            }}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-[#858585] text-[13px]">
            Select a file to edit
          </div>
        )}
      </div>
    </div>
  )
}
