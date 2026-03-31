/**
 * Terminal WebSocket Connection Manager
 * Handles real-time terminal communication with backend
 */

class TerminalWebSocket {
  constructor(sessionId = '') {
    this.sessionId = sessionId || ''
    this.ws = null
    this.url = this.buildUrl()
    this.messageHandlers = []
    this.errorHandlers = []
    this.closeHandlers = []
    this.isConnecting = false
    this.isConnected = false
  }

  /**
   * Build WebSocket URL based on current environment
   */
  buildUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const basePath = '/ws/terminal/' + this.sessionId
    return `${protocol}//${host}${basePath}`
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    return new Promise((resolve, reject) => {
      if (this.isConnecting || this.isConnected) {
        resolve()
        return
      }

      this.isConnecting = true

      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          this.isConnecting = false
          this.isConnected = true
          // WebSocket 连接建立
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onerror = (error) => {
          this.isConnecting = false
          console.error('[Terminal WS] Error:', error)
          this.errorHandlers.forEach(handler => handler(error))
          reject(error)
        }

        this.ws.onclose = () => {
          this.isConnecting = false
          this.isConnected = false
          // WebSocket 连接断开
          this.closeHandlers.forEach(handler => handler())
        }
      } catch (error) {
        this.isConnecting = false
        console.error('[Terminal WS] Connection failed:', error)
        reject(error)
      }
    })
  }

  /**
   * Send command to backend
   */
  sendCommand(command) {
    if (!this.isConnected) {
      console.error('[Terminal WS] Not connected')
      return false
    }

    const message = JSON.stringify({
      type: 'command',
      data: command
    })

    try {
      this.ws.send(message)
      return true
    } catch (error) {
      console.error('[Terminal WS] Send failed:', error)
      return false
    }
  }

  /**
   * Send ping to keep connection alive
   */
  ping() {
    if (!this.isConnected) return

    const message = JSON.stringify({ type: 'ping' })
    try {
      this.ws.send(message)
    } catch (error) {
      console.error('[Terminal WS] Ping failed:', error)
    }
  }

  /**
   * Handle incoming messages
   */
  handleMessage(data) {
    try {
      const message = JSON.parse(data)
      this.messageHandlers.forEach(handler => handler(message))
    } catch (error) {
      console.error('[Terminal WS] Parse message failed:', error, data)
    }
  }

  /**
   * Register message handler
   */
  onMessage(handler) {
    this.messageHandlers.push(handler)
    return () => {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler)
    }
  }

  /**
   * Register error handler
   */
  onError(handler) {
    this.errorHandlers.push(handler)
    return () => {
      this.errorHandlers = this.errorHandlers.filter(h => h !== handler)
    }
  }

  /**
   * Register close handler
   */
  onClose(handler) {
    this.closeHandlers.push(handler)
    return () => {
      this.closeHandlers = this.closeHandlers.filter(h => h !== handler)
    }
  }

  /**
   * Close connection
   */
  close() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
    this.isConnecting = false
  }

  /**
   * Check if connected
   */
  connected() {
    return this.isConnected
  }
}

export default TerminalWebSocket
