import { create } from 'zustand'

interface RLCDState {
  calibration: any | null
  evaluation: any | null
  actionSpace: string[]
  trajectories: any[]
  
  setCalibration: (cal: any) => void
  setEvaluation: (evalData: any) => void
  setActionSpace: (space: string[]) => void
  setTrajectories: (trajs: any[]) => void
}

export const useRLCDStore = create<RLCDState>((set) => ({
  calibration: null,
  evaluation: null,
  actionSpace: [],
  trajectories: [],
  
  setCalibration: (calibration) => set({ calibration }),
  setEvaluation: (evaluation) => set({ evaluation }),
  setActionSpace: (actionSpace) => set({ actionSpace }),
  setTrajectories: (trajectories) => set({ trajectories })
}))
