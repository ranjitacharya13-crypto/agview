import { create } from 'zustand'

interface AgentState {
  currentAgent: string | null
  currentTask: string | null
  decision: any | null
  confidence: number
  calibratedConfidence: number
  isRunning: boolean
  logs: string[]
  toolActivity: any[]
  
  setCurrentAgent: (agent: string | null) => void
  setCurrentTask: (task: string | null) => void
  setDecision: (decision: any) => void
  setRunning: (running: boolean) => void
  addLog: (log: string) => void
  addToolActivity: (activity: any) => void
  clearLogs: () => void
}

export const useAgentStore = create<AgentState>((set) => ({
  currentAgent: null,
  currentTask: null,
  decision: null,
  confidence: 0,
  calibratedConfidence: 0,
  isRunning: false,
  logs: [],
  toolActivity: [],
  
  setCurrentAgent: (agent) => set({ currentAgent: agent }),
  setCurrentTask: (task) => set({ currentTask: task }),
  setDecision: (decision) => set({ 
    decision,
    confidence: decision?.raw_confidence || decision?.confidence || 0,
    calibratedConfidence: decision?.calibrated_confidence || decision?.calibrated_confidence || 0
  }),
  setRunning: (running) => set({ isRunning: running }),
  addLog: (log) => set((state) => ({ logs: [...state.logs.slice(-100), log] })),
  addToolActivity: (activity) => set((state) => ({ toolActivity: [...state.toolActivity.slice(-50), activity] })),
  clearLogs: () => set({ logs: [], toolActivity: [] })
}))
