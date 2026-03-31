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

    <!-- Command Input (Legacy fallback) -->
    <div class="terminal-input-area">
      <el-input
        v-model="inputCommand"
        @keyup.enter="handleSendCommand"
        :disabled="!wsConnected"
        placeholder="Type command and press Enter..."
        size="small"
      >
        <template #suffix>
          <el-icon
            v-if="inputCommand"
            @click="inputCommand = ''"
            class="is-clear"
          >
            <Close />
          </el-icon>
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'
import TerminalWebSocket from '@/utils/terminalWs'
import { useMessage } from 'element-plus'

const $message = useMessage()

// State
const terminalRef = ref(null)
const terminal = ref(null)
const fitAddon = ref(null)
const wsConnected = ref(false)
const inputCommand = ref('')
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
      background: '#1e1e1e',
      foreground: '#d4d4d4',
    },
    fontSize: 13,
    fontFamily: 'Courier New, Courier, monospace',
  })

  fitAddon.value = new FitAddon()
  terminal.value.loadAddon(fitAddon.value)

  terminal.value.open(terminalRef.value)
  fitAddon.value.fit()

  // Handle Terminal input (for direct typing)
  terminal.value.onData(input => {
    if (ws && ws.connected()) {
      ws.sendCommand(input)
    }
  })

  // Handle resize
  window.addEventListener('resize', () => {
    if (fitAddon.value && terminalRef.value) {
      fitAddon.value.fit()
    }
  })

  terminal.value.writeln('Web Terminal Ready')
  terminal.value.writeln('Commands will be executed on the server')
  terminal.value.writeln('')
}

/**
 * Connect to WebSocket
 */
const handleConnect = async () => {
  try {
    statusMessage.value = 'Connecting...'

    // Create new session
    ws = new TerminalWebSocket(sessionId.value)

    // Setup message handlers before connecting
    ws.onMessage(handleWsMessage)
    ws.onError(handleWsError)
    ws.onClose(handleWsClose)

    await ws.connect()

    wsConnected.value = true
    statusMessage.value = 'Connected'
    terminal.value.writeln('Connected to server terminal')

    // Start keep-alive ping
    setInterval(() => {
      if (ws && ws.connected()) {
        ws.ping()
      }
    }, 30000)

  } catch (error) {
    $message.error('Failed to connect: ' + error.message)
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
      terminal.value.write(message.data)
      break

    case 'error':
      terminal.value.writeln('\r\n[ERROR] ' + message.data + '\r\n')
      statusMessage.value = 'Error: ' + message.data
      break

    case 'exit':
      const exitCode = message.code
      terminal.value.writeln(`\r\n[Process exited with code ${exitCode}]`)
      statusMessage.value = `Process exited (code: ${exitCode})`
      break

    case 'pong':
      // Keep-alive response
      break

    default:
      console.warn('Unknown message type:', message.type)
  }
}

/**
 * Handle WebSocket errors
 */
const handleWsError = (error) => {
  $message.error('WebSocket error: ' + error.message)
  terminal.value?.writeln('WebSocket error: ' + error.message)
  wsConnected.value = false
  statusMessage.value = 'WebSocket error'
}

/**
 * Handle WebSocket close
 */
const handleWsClose = () => {
  wsConnected.value = false
  statusMessage.value = 'Disconnected'
  terminal.value?.writeln('\r\n[Connection closed]')
}

/**
 * Send command via input field (legacy mode)
 */
const handleSendCommand = () => {
  if (!inputCommand.value.trim()) return

  if (ws && ws.connected()) {
    terminal.value.writeln('$ ' + inputCommand.value)
    ws.sendCommand(inputCommand.value + '\n')
    inputCommand.value = ''
  } else {
    $message.warning('Not connected to terminal')
  }
}

/**
 * Create new session
 */
const handleNewSession = () => {
  if (ws) ws.close()

  sessionId.value = ''
  terminal.value?.clear()

  handleConnect()
}

/**
 * Clear terminal
 */
const handleClearTerminal = () => {
  terminal.value?.clear()
  statusMessage.value = 'Terminal cleared'
}

/**
 * Lifecycle hooks
 */
onMounted(async () => {
  await nextTick()
  initTerminal()
  handleConnect()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  window.removeEventListener('resize', () => {})
})
</script>

<style scoped>
.terminal-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
  background-color: #1e1e1e;
  border-radius: 4px;
  overflow: hidden;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #252526;
  border-bottom: 1px solid #3e3e42;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 16px;
  font-weight: 500;
  color: #d4d4d4;
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
  padding: 8px;
}

.terminal-status-bar {
  padding: 8px 16px;
  background-color: #252526;
  border-top: 1px solid #3e3e42;
  color: #858585;
  font-size: 12px;
  height: 22px;
  line-height: 1;
}

.terminal-input-area {
  padding: 8px 16px;
  background-color: #252526;
  border-top: 1px solid #3e3e42;
}

/* xterm styling adjustments */
:deep(.xterm) {
  padding: 0;
}

:deep(.xterm-viewport) {
  background-color: #1e1e1e;
}
</style>
