import { create } from 'zustand'
import { Project, ProjectEvent } from '../types'

interface ProjectState {
  projects: any[]
  currentProject: Project | null
  events: ProjectEvent[]
  loading: boolean
  error: string | null
  
  setProjects: (projects: any[]) => void
  setCurrentProject: (project: Project | null) => void
  addEvent: (event: ProjectEvent) => void
  setEvents: (events: ProjectEvent[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  updateProjectStage: (stage: string) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  currentProject: null,
  events: [],
  loading: false,
  error: null,
  
  setProjects: (projects) => set({ projects }),
  setCurrentProject: (project) => set({ currentProject: project }),
  addEvent: (event) => set((state) => ({ events: [...state.events.slice(-200), event] })),
  setEvents: (events) => set({ events }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  updateProjectStage: (stage) => set((state) => ({
    currentProject: state.currentProject ? { ...state.currentProject, stage } : null
  }))
}))
