export interface Project {
  project_id: string
  name: string
  root_directory: string
  created_date: string
  last_modified: string
  current_branch: string
  stage: string
  problem_statement: string
  requirements: any[]
  research: any[]
  abstract: string
  abstract_approved: boolean
  solution: any
  frontend: any
  backend: any
  verification: any
  presentation: any
  decisions: DecisionRecord[]
  file_changes: FileChange[]
  actors?: string[]
  features?: string[]
  screens?: string[]
  tech_stack?: any
}

export interface DecisionRecord {
  id: string
  timestamp: string
  type: string
  state: string
  action: string
  probabilities?: Record<string, number>
  raw_confidence: number
  calibrated_confidence: number
  risk: number
  evidence: string[]
  agent: string
}

export interface FileChange {
  id: string
  timestamp: string
  path: string
  operation: string
  agent: string
  old_content?: string
  new_content?: string
}

export interface FileItem {
  name: string
  path: string
  type: 'file' | 'directory'
  size?: number
  children?: FileItem[]
  collapsed?: boolean
}

export interface EditorTab {
  id: string
  path: string
  name: string
  content: string
  dirty: boolean
  language: string
}

export interface ProjectEvent {
  id: string
  project_id: string
  type: string
  timestamp: string
  agent?: string
  decision_id?: string
  data: any
  message: string
}

export interface TerminalProcess {
  id: string
  command: string
  stdout: string
  stderr: string
  exit_code?: number
  status: string
  duration_ms: number
}

export interface RLCDDecision {
  selected_action?: string
  probabilities?: Record<string, number>
  raw_confidence: number
  calibrated_confidence: number
  risk: number
  evidence: string[]
  reasoning_summary?: string
}
