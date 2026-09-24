import { create } from 'zustand'
import { EditorTab, FileItem } from '../types'

interface EditorState {
  tabs: EditorTab[]
  activeTabId: string | null
  fileTree: FileItem | null
  expandedFolders: Set<string>
  searchQuery: string
  
  openTab: (tab: EditorTab) => void
  closeTab: (id: string) => void
  setActiveTab: (id: string) => void
  updateTabContent: (id: string, content: string, dirty?: boolean) => void
  setFileTree: (tree: FileItem | null) => void
  toggleFolder: (path: string) => void
  setSearchQuery: (query: string) => void
}

export const useEditorStore = create<EditorState>((set) => ({
  tabs: [],
  activeTabId: null,
  fileTree: null,
  expandedFolders: new Set(['', 'src', 'backend']),
  searchQuery: '',
  
  openTab: (tab) => set((state) => {
    const existing = state.tabs.find(t => t.path === tab.path)
    if (existing) {
      return { activeTabId: existing.id }
    }
    return {
      tabs: [...state.tabs, tab],
      activeTabId: tab.id
    }
  }),
  
  closeTab: (id) => set((state) => {
    const newTabs = state.tabs.filter(t => t.id !== id)
    let newActive = state.activeTabId
    if (state.activeTabId === id) {
      newActive = newTabs.length > 0 ? newTabs[newTabs.length - 1].id : null
    }
    return { tabs: newTabs, activeTabId: newActive }
  }),
  
  setActiveTab: (id) => set({ activeTabId: id }),
  
  updateTabContent: (id, content, dirty = true) => set((state) => ({
    tabs: state.tabs.map(t => t.id === id ? { ...t, content, dirty } : t)
  })),
  
  setFileTree: (tree) => set({ fileTree: tree }),
  
  toggleFolder: (path) => set((state) => {
    const newSet = new Set(state.expandedFolders)
    if (newSet.has(path)) {
      newSet.delete(path)
    } else {
      newSet.add(path)
    }
    return { expandedFolders: newSet }
  }),
  
  setSearchQuery: (query) => set({ searchQuery: query })
}))
