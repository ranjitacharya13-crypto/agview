export class ProjectWebSocket {
  private ws: WebSocket | null = null
  private projectId: string
  private listeners: ((event: any) => void)[] = []
  private reconnectAttempts = 0
  private maxReconnect = 5
  private reconnectTimeout: any = null

  constructor(projectId: string) {
    this.projectId = projectId
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    // Use relative host for preview compatibility
    const url = `${protocol}//${host}/ws/projects/${this.projectId}`
    
    // Fallback to localhost if needed
    const wsUrl = url.includes('localhost') || url.includes('127.0.0.1') 
      ? url 
      : `${protocol}//${window.location.hostname}:8000/ws/projects/${this.projectId}`

    // Try relative first, then absolute
    const finalUrl = window.location.hostname.includes('e2b.app') || window.location.hostname.includes('localhost')
      ? `ws://${window.location.hostname}:8000/ws/projects/${this.projectId}`.replace(':3000', ':8000')
      : url

    console.log('Connecting WebSocket:', finalUrl)

    try {
      this.ws = new WebSocket(finalUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected for project', this.projectId)
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.listeners.forEach(cb => cb(data))
        } catch (e) {
          console.error('WS parse error', e)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket closed')
        this.tryReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error', error)
      }
    } catch (e) {
      console.error('WebSocket connection failed', e)
      this.tryReconnect()
    }
  }

  private tryReconnect() {
    if (this.reconnectAttempts < this.maxReconnect) {
      this.reconnectAttempts++
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000)
      console.log(`Reconnecting WebSocket in ${delay}ms (attempt ${this.reconnectAttempts})`)
      this.reconnectTimeout = setTimeout(() => this.connect(), delay)
    }
  }

  onEvent(callback: (event: any) => void) {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter(cb => cb !== callback)
    }
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.listeners = []
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}
