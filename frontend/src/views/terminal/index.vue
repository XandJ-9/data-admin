<template>
  <div class="terminal-container">
    <!-- Header -->
    <div class="terminal-header">
      <div class="header-info">
        <span class="title">Web Terminal</span>
        <el-tag :type="wsConnected ? 'success' : 'danger'" class="status-badge">
          {{ wsConnected ? 'Connected' : 'Disconnected' }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button
          v-if="wsConnected"
          @click="handleNewSession"
          type="primary"
          size="small"
          icon="Plus"
        >
          New Session
        </el-button>
        <el-button
          v-if="wsConnected"
          @click="handleClearTerminal"
          size="small"
          icon="Delete"
        >
          Clear
        </el-button>
        <el-button
          v-if="!wsConnected"
          @click="handleConnect"
          type="primary"
          size="small"
          icon="Connection"
        >
          Connect
        </el-button>
      </div>
    </div>

    <!-- Terminal Output Area -->
    <div ref="terminalRef" class="terminal-area"></div>

    <!-- Status Bar -->
    <div class="terminal-status-bar">
      <span>{{ statusMessage }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'
import TerminalWebSocket from '@/utils/terminalWs'
import { ElMessage } from 'element-plus'

// State
const terminalRef = ref(null)
const terminal = ref(null)
const fitAddon = ref(null)
const wsConnected = ref(false)
const statusMessage = ref('Ready')
let ws = null
let sessionId = ref('')

/**
 * Initialize xterm.js
 */
const initTerminal = () => {
  if (terminal.value) return

  terminal.value = new Terminal({
    cursorBlink: true,
    theme: {
      background: '#1a1b26',
      foreground: '#c0caf5',
      cursor: '#c0caf5',
      cursorAccent: '#1a1b26',
      selectionBackground: '#33467c',
      black: '#15161e',
      red: '#f7768e',
      green: '#9ece6a',
      yellow: '#e0af68',
      blue: '#7aa2f7',
      magenta: '#bb9af7',
      cyan: '#7dcfff',
      white: '#a9b1d6',
      brightBlack: '#414868',
      brightRed: '#f7768e',
      brightGreen: '#9ece6a',
      brightYellow: '#e0af68',
      brightBlue: '#7aa2f7',
      brightMagenta: '#bb9af7',
      brightCyan: '#7dcfff',
      brightWhite: '#c0caf5',
    },
    fontSize: 14,
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, Monaco, 'Courier New', monospace",
    scrollback: 5000,
  })

  fitAddon.value = new FitAddon()
  terminal.value.loadAddon(fitAddon.value)

  terminal.value.open(terminalRef.value)
  fitAddon.value.fit()

  // Forward all keystrokes directly to backend PTY
  terminal.value.onData(input => {
    if (ws && ws.connected()) {
      ws.sendInput(input)
    }
  })

  // Handle resize: update xterm fit and notify backend
  const handleResize = () => {
    if (fitAddon.value && terminalRef.value) {
      fitAddon.value.fit()
      if (ws && ws.connected() && terminal.value) {
        ws.sendResize(terminal.value.cols, terminal.value.rows)
      }
    }
  }
  window.addEventListener('resize', handleResize)

  // Also send resize when terminal dimensions change
  terminal.value.onResize(({ cols, rows }) => {
    if (ws && ws.connected()) {
      ws.sendResize(cols, rows)
    }
  })
}

/**
 * Connect to WebSocket
 */
const handleConnect = async () => {
  try {
    statusMessage.value = 'Connecting...'

    ws = new TerminalWebSocket(sessionId.value)

    ws.onMessage(handleWsMessage)
    ws.onError(handleWsError)
    ws.onClose(handleWsClose)

    await ws.connect()

    wsConnected.value = true
    statusMessage.value = 'Connected'

    // Send initial terminal size
    if (terminal.value) {
      ws.sendResize(terminal.value.cols, terminal.value.rows)
    }

    // Keep-alive ping
    const pingInterval = setInterval(() => {
      if (ws && ws.connected()) {
        ws.ping()
      } else {
        clearInterval(pingInterval)
      }
    }, 30000)

  } catch (error) {
    ElMessage.error('Failed to connect: ' + error.message)
    statusMessage.value = 'Connection failed'
  }
}

/**
 * Handle WebSocket messages from server
 */
const handleWsMessage = (message) => {
  if (!terminal.value) return

  switch (message.type) {
    case 'output':
      // Write PTY output directly to xterm (already has proper formatting)
      terminal.value.write(message.data)
      break

    case 'exit':
      terminal.value.writeln('\r\n[Session ended]')
      statusMessage.value = 'Session ended'
      break

    case 'error':
      terminal.value.writeln(`\r\n\x1b[1;31m[ERROR] ${message.data}\x1b[0m`)
      statusMessage.value = 'Error: ' + message.data
      break

    case 'pong':
      break

    default:
      console.warn('Unknown message type:', message.type)
  }
}

const handleWsError = (error) => {
  ElMessage.error('WebSocket error')
  wsConnected.value = false
  statusMessage.value = 'WebSocket error'
}

const handleWsClose = () => {
  wsConnected.value = false
  statusMessage.value = 'Disconnected'
  terminal.value?.writeln('\r\n\x1b[90m[Connection closed]\x1b[0m')
}

const handleNewSession = () => {
  if (ws) ws.close()
  sessionId.value = ''
  terminal.value?.clear()
  handleConnect()
}

const handleClearTerminal = () => {
  terminal.value?.clear()
}

onMounted(async () => {
  await nextTick()
  initTerminal()
  handleConnect()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
.terminal-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
  background-color: #1a1b26;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background-color: #16161e;
  border-bottom: 1px solid #292e42;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 14px;
  font-weight: 600;
  color: #c0caf5;
  letter-spacing: 0.5px;
}

.status-badge {
  font-size: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.terminal-area {
  flex: 1;
  overflow: hidden;
  padding: 4px 8px;
}

.terminal-status-bar {
  padding: 6px 16px;
  background-color: #16161e;
  border-top: 1px solid #292e42;
  color: #565f89;
  font-size: 12px;
  line-height: 1;
}

/* xterm styling adjustments */
:deep(.xterm) {
  padding: 0;
}

:deep(.xterm-viewport) {
  background-color: #1a1b26 !important;
}

:deep(.xterm-viewport::-webkit-scrollbar) {
  width: 8px;
}

:deep(.xterm-viewport::-webkit-scrollbar-track) {
  background: #1a1b26;
}

:deep(.xterm-viewport::-webkit-scrollbar-thumb) {
  background: #292e42;
  border-radius: 4px;
}

:deep(.xterm-viewport::-webkit-scrollbar-thumb:hover) {
  background: #3b4261;
}
</style>
