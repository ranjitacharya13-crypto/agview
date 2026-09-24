import { useState, useEffect } from 'react'
import { 
  Folder, File, ChevronRight, ChevronDown, 
  FilePlus, FolderPlus, RefreshCw, MoreHorizontal,
  FileCode, FileJson, FileText
} from 'lucide-react'
import { useEditorStore } from '../../stores/editorStore'
import { filesystemApi } from '../../services/api'
import { FileItem } from '../../types'

interface Props {
  projectId: string
}

export function Explorer({ projectId }: Props) {
  const { fileTree, setFileTree, expandedFolders, toggleFolder, openTab } = useEditorStore()
  const [loading, setLoading] = useState(false)
  const [contextMenu, setContextMenu] = useState<{x: number, y: number, path: string, type: string} | null>(null)

  const loadTree = async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const result = await filesystemApi.tree(projectId)
      if (result.success) {
        setFileTree(result.tree)
      }
    } catch (e) {
      console.error('Failed to load tree', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTree()
  }, [projectId])

  const handleFileClick = async (file: FileItem) => {
    if (file.type === 'directory') {
      toggleFolder(file.path)
    } else {
      // Open file
      try {
        const result = await filesystemApi.read(projectId, file.path)
        if (result.success) {
          const ext = file.name.split('.').pop() || 'txt'
          const langMap: Record<string, string> = {
            'tsx': 'typescript',
            'ts': 'typescript',
            'jsx': 'javascript',
            'js': 'javascript',
            'py': 'python',
            'json': 'json',
            'md': 'markdown',
            'css': 'css',
            'html': 'html'
          }
          openTab({
            id: file.path,
            path: file.path,
            name: file.name,
            content: result.content,
            dirty: false,
            language: langMap[ext] || 'plaintext'
          })
        }
      } catch (e) {
        console.error('Failed to read file', e)
      }
    }
  }

  const getFileIcon = (name: string) => {
    if (name.endsWith('.tsx') || name.endsWith('.ts')) return <FileCode className="w-4 h-4 text-[#519aba]" />
    if (name.endsWith('.json')) return <FileJson className="w-4 h-4 text-[#cbcb41]" />
    if (name.endsWith('.md')) return <FileText className="w-4 h-4 text-[#519aba]" />
    return <File className="w-4 h-4 text-[#cccccc]" />
  }

  const renderTree = (node: FileItem, depth: number = 0) => {
    const isExpanded = expandedFolders.has(node.path)
    const isFolder = node.type === 'directory'

    return (
      <div key={node.path || 'root'}>
        <div
          className="flex items-center gap-1 px-2 py-[2px] hover:bg-[#2a2d2e] cursor-pointer text-[13px] group"
          style={{ paddingLeft: `${8 + depth * 16}px` }}
          onClick={() => handleFileClick(node)}
          onContextMenu={(e) => {
            e.preventDefault()
            setContextMenu({ x: e.clientX, y: e.clientY, path: node.path, type: node.type })
          }}
        >
          {isFolder && (
            <span className="w-4 h-4 flex items-center justify-center">
              {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            </span>
          )}
          {!isFolder && <span className="w-4"></span>}
          {isFolder ? (
            <Folder className="w-4 h-4 text-[#dcad53]" />
          ) : (
            getFileIcon(node.name)
          )}
          <span className="truncate text-[#cccccc] group-hover:text-white">{node.name || 'workspace'}</span>
        </div>
        
        {isFolder && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderTree(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="w-[260px] bg-[#181818] border-r border-[#2d2d30] flex flex-col h-full">
      <div className="h-[35px] px-3 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-[#bbbbbb]">
        <span>Explorer</span>
        <div className="flex items-center gap-1">
          <button 
            onClick={() => {
              const name = prompt('File name:')
              if (name) {
                filesystemApi.write(projectId, name, '').then(() => loadTree())
              }
            }}
            className="p-1 hover:bg-[#2a2d2e] rounded"
            title="New File"
          >
            <FilePlus className="w-4 h-4" />
          </button>
          <button 
            onClick={() => {
              const name = prompt('Folder name:')
              if (name) {
                filesystemApi.mkdir(projectId, name).then(() => loadTree())
              }
            }}
            className="p-1 hover:bg-[#2a2d2e] rounded"
            title="New Folder"
          >
            <FolderPlus className="w-4 h-4" />
          </button>
          <button onClick={loadTree} className="p-1 hover:bg-[#2a2d2e] rounded" title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button className="p-1 hover:bg-[#2a2d2e] rounded">
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-[#bbbbbb] bg-[#181818]">
        {fileTree?.name || 'No Folder Opened'}
      </div>

      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="p-3 text-[12px] text-[#858585]">Loading...</div>
        ) : fileTree ? (
          renderTree(fileTree)
        ) : (
          <div className="p-3 text-[12px] text-[#858585]">
            No project loaded. Create a project to see files.
          </div>
        )}
      </div>

      {contextMenu && (
        <div 
          className="fixed bg-[#252526] border border-[#454545] rounded shadow-lg py-1 text-[13px] z-50 min-w-[200px]"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onMouseLeave={() => setContextMenu(null)}
        >
          <button 
            className="w-full text-left px-3 py-1 hover:bg-[#2a2d2e] text-[#cccccc]"
            onClick={() => {
              const newName = prompt('New name:', contextMenu.path.split('/').pop())
              if (newName) {
                const newPath = contextMenu.path.split('/').slice(0, -1).join('/') + '/' + newName
                filesystemApi.move(projectId, contextMenu.path, newPath).then(() => loadTree())
              }
              setContextMenu(null)
            }}
          >
            Rename
          </button>
          <button 
            className="w-full text-left px-3 py-1 hover:bg-[#2a2d2e] text-[#cccccc]"
            onClick={() => {
              if (confirm(`Delete ${contextMenu.path}?`)) {
                filesystemApi.delete(projectId, contextMenu.path).then(() => loadTree())
              }
              setContextMenu(null)
            }}
          >
            Delete
          </button>
        </div>
      )}
    </div>
  )
}
