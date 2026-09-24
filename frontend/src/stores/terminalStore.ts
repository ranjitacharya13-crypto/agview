import { create } from 'zustand'
import { TerminalProcess } from '../types'

interface TerminalState {
  processes: TerminalProcess[]
  activeProcessId: string | null
  commandHistory: string[]
  currentCommand: string
  
  setProcesses: (processes: TerminalProcess[]) => void
  addProcess: (process: TerminalProcess) => void
  setActiveProcess: (id: string | null) => void
  setCurrentCommand: (cmd: string) => void
  addToHistory: (cmd: string) => void
}

export const useTerminalStore = create<TerminalState>((set) => ({
  processes: [],
  activeProcessId: null,
  commandHistory: [],
  currentCommand: '',
  
  setProcesses: (processes) => set({ processes }),
  addProcess: (process) => set((state) => ({ processes: [process, ...state.processes.slice(0, 19)] })),
  setActiveProcess: (id) => set({ activeProcessId: id }),
  setCurrentCommand: (cmd) => set({ currentCommand: cmd }),
  addToHistory: (cmd) => set((state) => ({ commandHistory: [...state.commandHistory, cmd].slice(-50) }))
}))
