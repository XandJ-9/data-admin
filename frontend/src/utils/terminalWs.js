/**
 * Terminal WebSocket Connection Manager
 * Handles real-time terminal communication with backend.
 * Features: auto-reconnect, heartbeat, binary support.
 */
import { getToken } from '@/utils/auth'

const RECONNECT_BASE_DELAY = 1000    // ms
const RECONNECT_MAX_DELAY = 16000    // ms
const RECONNECT_MAX_ATTEMPTS = 8
const HEARTBEAT_INTERVAL = 25000     // ms  (server expects ≤30s)

class TerminalWebSocket {
  constructor(sessionId = '') {
    this.sessionId = sessionId || ''
    this.ws = null
    this.messageHandlers = []
    this.errorHandlers = []
    this.closeHandlers = []
    this.reconnectHandlers = []
    this.isConnecting = false
    this.isConnected = false
    this._reconnectAttempts = 0
    this._reconnectTimer = null
    this._heartbeatTimer = null
    this._intentionallyClosed = false
  }

  /** Build WebSocket URL based on current environment */
  _buildUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const basePath = '/ws/terminal/' + this.sessionId
    const token = getToken()
    if (!token) return `${protocol}//${host}${basePath}`
    return `${protocol}//${host}${basePath}?token=${encodeURIComponent(token)}`
  }

  /** Connect to WebSocket server */
  connect() {
    return new Promise((resolve, reject) => {
      if (this.isConnecting || this.isConnected) {
        resolve()
        return
      }
      this.isConnecting = true
      this._intentionallyClosed = false

      try {
        this.ws = new WebSocket(this._buildUrl())

        this.ws.onopen = () => {
          this.isConnecting = false
          this.isConnected = true
          this._reconnectAttempts = 0
          this._startHeartbeat()
          resolve()
        }

        this.ws.onmessage = (event) => {
          this._handleMessage(event.data)
        }

        this.ws.onerror = (error) => {
          this.isConnecting = false
          this.errorHandlers.forEach(h => h(error))
          reject(error)
        }

        this.ws.onclose = (event) => {
          this.isConnecting = false
          this.isConnected = false
          this._stopHeartbeat()
          this.closeHandlers.forEach(h => h(event))
          if (!this._intentionallyClosed) {
            this._scheduleReconnect()
          }
        }
      } catch (error) {
        this.isConnecting = false
        reject(error)
      }
    })
  }

  // ── Message sending ────────────────────────────────────────────

  /** Send raw input to backend PTY */
  sendInput(data) {
    return this._send({ type: 'input', data })
  }

  /** Send command to backend (legacy) */
  sendCommand(command) {
    return this._send({ type: 'command', data: command })
  }

  /** Send terminal resize event */
  sendResize(cols, rows) {
    return this._send({ type: 'resize', cols, rows })
  }

  /** Send ping to keep connection alive */
  ping() {
    return this._send({ type: 'ping' })
  }

  /** Send pong in reply to server ping */
  pong() {
    return this._send({ type: 'pong' })
  }

  _send(payload) {
    if (!this.isConnected || !this.ws) return false
    try {
      this.ws.send(JSON.stringify(payload))
      return true
    } catch (error) {
      console.error('[Terminal WS] Send failed:', error)
      return false
    }
  }

  // ── Heartbeat ──────────────────────────────────────────────────

  _startHeartbeat() {
    this._stopHeartbeat()
    this._heartbeatTimer = setInterval(() => {
      if (this.isConnected) this.ping()
    }, HEARTBEAT_INTERVAL)
  }

  _stopHeartbeat() {
    if (this._heartbeatTimer) {
      clearInterval(this._heartbeatTimer)
      this._heartbeatTimer = null
    }
  }

  // ── Auto-reconnect ────────────────────────────────────────────

  _scheduleReconnect() {
    if (this._reconnectAttempts >= RECONNECT_MAX_ATTEMPTS) return

    const delay = Math.min(
      RECONNECT_BASE_DELAY * Math.pow(2, this._reconnectAttempts),
      RECONNECT_MAX_DELAY,
    )
    this._reconnectAttempts++

    this._reconnectTimer = setTimeout(async () => {
      try {
        await this.connect()
        this.reconnectHandlers.forEach(h => h(this._reconnectAttempts))
      } catch {
        // onclose will fire again and re-schedule
      }
    }, delay)
  }

  // ── Message handling ───────────────────────────────────────────

  _handleMessage(raw) {
    try {
      const message = JSON.parse(raw)
      // Reply to server-initiated ping
      if (message.type === 'ping') {
        this.pong()
        return
      }
      this.messageHandlers.forEach(h => h(message))
    } catch (error) {
      console.error('[Terminal WS] Parse message failed:', error)
    }
  }

  // ── Event registration ────────────────────────────────────────

  onMessage(handler) {
    this.messageHandlers.push(handler)
    return () => { this.messageHandlers = this.messageHandlers.filter(h => h !== handler) }
  }

  onError(handler) {
    this.errorHandlers.push(handler)
    return () => { this.errorHandlers = this.errorHandlers.filter(h => h !== handler) }
  }

  onClose(handler) {
    this.closeHandlers.push(handler)
    return () => { this.closeHandlers = this.closeHandlers.filter(h => h !== handler) }
  }

  onReconnect(handler) {
    this.reconnectHandlers.push(handler)
    return () => { this.reconnectHandlers = this.reconnectHandlers.filter(h => h !== handler) }
  }

  // ── Cleanup ────────────────────────────────────────────────────

  close() {
    this._intentionallyClosed = true
    this._stopHeartbeat()
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer)
      this._reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
    this.isConnecting = false
  }

  connected() {
    return this.isConnected
  }
}

export default TerminalWebSocket
