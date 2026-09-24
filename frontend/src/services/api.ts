import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
})

export const projectApi = {
  list: () => api.get('/projects/').then(r => r.data),
  create: (name: string, problem_statement: string) => 
    api.post('/projects/', { name, problem_statement }).then(r => r.data),
  get: (id: string) => api.get(`/projects/${id}`).then(r => r.data),
  delete: (id: string) => api.delete(`/projects/${id}`).then(r => r.data),
  setProblem: (id: string, problem_statement: string) =>
    api.post(`/projects/${id}/problem`, { problem_statement }).then(r => r.data),
  research: (id: string, query: string = '') =>
    api.post(`/projects/${id}/research`, { query }).then(r => r.data),
  createAbstract: (id: string) =>
    api.post(`/projects/${id}/abstract`, {}).then(r => r.data),
  critiqueAbstract: (id: string) =>
    api.post(`/projects/${id}/abstract/critique`).then(r => r.data),
  approveAbstract: (id: string) =>
    api.post(`/projects/${id}/abstract/approve`).then(r => r.data),
  createSolution: (id: string) =>
    api.post(`/projects/${id}/solution`, {}).then(r => r.data),
  createFrontend: (id: string) =>
    api.post(`/projects/${id}/frontend`, {}).then(r => r.data),
  createBackend: (id: string) =>
    api.post(`/projects/${id}/backend`, {}).then(r => r.data),
  test: (id: string) =>
    api.post(`/projects/${id}/test`, {}).then(r => r.data),
  debug: (id: string, error: any = {}) =>
    api.post(`/projects/${id}/debug`, { error }).then(r => r.data),
  verify: (id: string) =>
    api.post(`/projects/${id}/verify`).then(r => r.data),
  presentation: (id: string) =>
    api.post(`/projects/${id}/presentation`, {}).then(r => r.data),
  master: (id: string, action: string = 'auto') =>
    api.post(`/projects/${id}/master`, { action }).then(r => r.data),
  chat: (id: string, query: string) =>
    api.post(`/projects/${id}/chat`, { query }).then(r => r.data),
  events: (id: string, limit: number = 100) =>
    api.get(`/projects/${id}/events?limit=${limit}`).then(r => r.data),
  trajectories: (id: string) =>
    api.get(`/projects/${id}/trajectories`).then(r => r.data),
}

export const filesystemApi = {
  list: (projectId: string, path: string = '') =>
    api.get(`/filesystem/${projectId}/list?path=${encodeURIComponent(path)}`).then(r => r.data),
  tree: (projectId: string) =>
    api.get(`/filesystem/${projectId}/tree`).then(r => r.data),
  read: (projectId: string, path: string) =>
    api.post(`/filesystem/${projectId}/read`, { path }).then(r => r.data),
  write: (projectId: string, path: string, content: string, agent: string = 'user') =>
    api.post(`/filesystem/${projectId}/write`, { path, content, agent }).then(r => r.data),
  delete: (projectId: string, path: string) =>
    api.post(`/filesystem/${projectId}/delete`, { path }).then(r => r.data),
  mkdir: (projectId: string, path: string) =>
    api.post(`/filesystem/${projectId}/mkdir`, { path }).then(r => r.data),
  search: (projectId: string, query: string) =>
    api.post(`/filesystem/${projectId}/search`, { query }).then(r => r.data),
  move: (projectId: string, src: string, dest: string) =>
    api.post(`/filesystem/${projectId}/move`, { src, dest }).then(r => r.data),
  fileHistory: (projectId: string, path?: string) =>
    api.get(`/filesystem/${projectId}/file-history${path ? `?path=${encodeURIComponent(path)}` : ''}`).then(r => r.data),
}

export const terminalApi = {
  execute: (projectId: string, command: string, cwd: string = '', approve: boolean = false) =>
    api.post(`/terminal/${projectId}/execute`, { command, cwd, approve }).then(r => r.data),
  processes: (projectId: string) =>
    api.get(`/terminal/${projectId}/processes`).then(r => r.data),
  getProcess: (projectId: string, processId: string) =>
    api.get(`/terminal/${projectId}/process/${processId}`).then(r => r.data),
  kill: (projectId: string, processId: string) =>
    api.post(`/terminal/${projectId}/process/${processId}/kill`).then(r => r.data),
  install: (projectId: string, command: string) =>
    api.post(`/terminal/${projectId}/install`, { command }).then(r => r.data),
}

export const rlcdApi = {
  decision: (projectId: string, type: string = 'choice', scoreName?: string, question?: string) =>
    api.post('/rlcd/decision', { project_id: projectId, decision_type: type, score_name: scoreName, question }).then(r => r.data),
  calibration: () => api.get('/rlcd/calibration').then(r => r.data),
  evaluation: () => api.get('/rlcd/evaluation').then(r => r.data),
  actionSpace: () => api.get('/rlcd/action-space').then(r => r.data),
  trajectories: () => api.get('/rlcd/trajectories').then(r => r.data),
}

export const agentsApi = {
  list: () => api.get('/agents/').then(r => r.data),
  models: () => api.get('/agents/models').then(r => r.data),
}

export const gitApi = {
  status: (projectId: string) => api.get(`/git/${projectId}/status`).then(r => r.data),
  diff: (projectId: string) => api.get(`/git/${projectId}/diff`).then(r => r.data),
  commit: (projectId: string, message: string) => api.post(`/git/${projectId}/commit`, { args: message }).then(r => r.data),
  branch: (projectId: string) => api.get(`/git/${projectId}/branch`).then(r => r.data),
  log: (projectId: string) => api.get(`/git/${projectId}/log`).then(r => r.data),
}

export const exportApi = {
  package: (projectId: string) => `${API_BASE}/export/${projectId}/package`,
  readme: (projectId: string) => api.get(`/export/${projectId}/readme`).then(r => r.data),
  abstract: (projectId: string) => api.get(`/export/${projectId}/export/abstract`).then(r => r.data),
}

export default api
