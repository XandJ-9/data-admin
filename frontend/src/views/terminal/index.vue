<template>
  <div class="terminal-container">
    <!-- Tab Bar -->
    <div class="terminal-tab-bar">
      <div class="tab-list">
        <div
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab-item', { active: tab.id === activeTabId }]"
          @click="switchTab(tab.id)"
        >
          <span class="tab-dot" :class="tab.connected ? 'dot-connected' : 'dot-disconnected'" />
          <span class="tab-name">{{ tab.name }}</span>
          <span class="tab-close" @click.stop="closeTab(tab.id)">×</span>
        </div>
      </div>
      <div class="tab-actions">
        <el-tooltip content="搜索 (Ctrl+Shift+F)" placement="bottom">
          <el-button @click="toggleSearch" size="small" icon="Search" circle />
        </el-tooltip>
        <el-button @click="handleNewSession" type="primary" size="small" icon="Plus">
          新会话
        </el-button>
        <el-button @click="handleClearTerminal" size="small" icon="Delete">
          清屏
        </el-button>
      </div>
    </div>

    <!-- Search Bar -->
    <div v-show="searchVisible" class="terminal-search-bar">
      <el-input
        ref="searchInputRef"
        v-model="searchQuery"
        placeholder="搜索终端内容..."
        size="small"
        clearable
        @input="handleSearchInput"
        @keyup.enter="searchNext"
        @keyup.escape="toggleSearch"
      >
        <template #append>
          <el-button @click="searchPrev" icon="ArrowUp" size="small" />
          <el-button @click="searchNext" icon="ArrowDown" size="small" />
          <el-button @click="toggleSearch" icon="Close" size="small" />
        </template>
      </el-input>
    </div>

    <!-- Terminal Area (all tabs render here, only active visible) -->
    <div ref="terminalAreaRef" class="terminal-area"></div>

    <!-- Status Bar -->
    <div class="terminal-status-bar">
      <span>{{ activeTab?.statusMessage || '就绪' }}</span>
      <span v-if="activeTab?.terminalSize" class="terminal-size">{{ activeTab.terminalSize }}</span>
    </div>
  </div>
</template>

<script setup name="WebTerminal">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebglAddon } from '@xterm/addon-webgl'
import { WebLinksAddon } from '@xterm/addon-web-links'
import { SearchAddon } from '@xterm/addon-search'
import { Unicode11Addon } from '@xterm/addon-unicode11'
import '@xterm/xterm/css/xterm.css'
import TerminalWebSocket from '@/utils/terminalWs'
import { ElMessage } from 'element-plus'

const MAX_TABS = 8

// ── State ────────────────────────────────────────────────────────
const terminalAreaRef = ref(null)
const searchInputRef = ref(null)
const searchVisible = ref(false)
const searchQuery = ref('')
const tabs = reactive([])
const activeTabId = ref(null)
let tabCounter = 0
let resizeObserver = null

const activeTab = computed(() => tabs.find(t => t.id === activeTabId.value))

// ── Terminal Options ─────────────────────────────────────────────
const TERMINAL_OPTIONS = {
  cursorBlink: true,
  cursorStyle: 'bar',
  allowProposedApi: true,
  theme: {
    background: '#1a1b26',
    foreground: '#c0caf5',
    cursor: '#c0caf5',
    cursorAccent: '#1a1b26',
    selectionBackground: '#33467c',
    selectionForeground: '#c0caf5',
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
  scrollback: 10000,
  convertEol: true,
  macOptionIsMeta: true,
  macOptionClickForcesSelection: true,
  rightClickSelectsWord: true,
  wordSeparator: ' ()[]{}\'"`,;:',
}

// ── Tab Management ───────────────────────────────────────────────

/** Create a new terminal tab, init xterm + ws, and switch to it. */
async function createTab() {
  if (tabs.length >= MAX_TABS) {
    ElMessage.warning(`最多支持 ${MAX_TABS} 个终端会话`)
    return
  }

  tabCounter++
  const id = tabCounter
  const name = `终端 ${id}`

  // Container div for this tab's xterm instance
  const containerEl = document.createElement('div')
  containerEl.className = 'terminal-tab-pane'
  containerEl.style.display = 'none'
  terminalAreaRef.value.appendChild(containerEl)

  const tab = reactive({
    id,
    name,
    terminal: null,
    fitAddon: null,
    searchAddon: null,
    ws: null,
    containerEl,
    connected: false,
    reconnecting: false,
    statusMessage: '正在连接...',
    terminalSize: '',
  })
  tabs.push(tab)

  // Init xterm
  const term = new Terminal(TERMINAL_OPTIONS)

  const fit = new FitAddon()
  term.loadAddon(fit)

  const search = new SearchAddon()
  term.loadAddon(search)

  term.loadAddon(new WebLinksAddon())

  const unicode11 = new Unicode11Addon()
  term.loadAddon(unicode11)
  term.unicode.activeVersion = '11'

  term.open(containerEl)

  try { term.loadAddon(new WebglAddon()) } catch { /* canvas fallback */ }

  tab.terminal = term
  tab.fitAddon = fit
  tab.searchAddon = search

  // Forward keystrokes to this tab's WS
  term.onData(input => {
    if (tab.ws && tab.ws.connected()) tab.ws.sendInput(input)
  })

  term.onResize(({ cols, rows }) => {
    tab.terminalSize = `${cols}×${rows}`
    if (tab.ws && tab.ws.connected()) tab.ws.sendResize(cols, rows)
  })

  term.attachCustomKeyEventHandler((ev) => {
    if (ev.ctrlKey && ev.shiftKey && ev.key === 'F') { toggleSearch(); return false }
    if (ev.ctrlKey && ev.shiftKey && ev.key === 'C') return false
    if (ev.ctrlKey && ev.shiftKey && ev.key === 'V') return false
    return true
  })

  // Switch to this tab (shows container, hides others)
  switchTab(id)
  await nextTick()
  fit.fit()

  // Connect WS
  await connectTab(tab)
}

/** Connect (or reconnect) WebSocket for a given tab. */
async function connectTab(tab) {
  try {
    tab.statusMessage = '正在连接...'
    const ws = new TerminalWebSocket('')
    tab.ws = ws

    ws.onMessage((msg) => onTabMessage(tab, msg))
    ws.onError(() => { tab.connected = false; tab.statusMessage = '连接异常' })
    ws.onClose(() => {
      tab.connected = false
      tab.reconnecting = true
      tab.statusMessage = '连接断开，重连中...'
      tab.terminal?.writeln('\r\n\x1b[90m[连接断开，正在自动重连...]\x1b[0m')
    })
    ws.onReconnect((attempt) => {
      tab.connected = true
      tab.reconnecting = false
      tab.statusMessage = `已重连 (第${attempt}次)`
      tab.terminal?.writeln('\r\n\x1b[32m[已重新连接]\x1b[0m')
      if (tab.terminal) ws.sendResize(tab.terminal.cols, tab.terminal.rows)
    })

    await ws.connect()
    tab.connected = true
    tab.reconnecting = false
    tab.statusMessage = '已连接'

    if (tab.terminal) ws.sendResize(tab.terminal.cols, tab.terminal.rows)
  } catch {
    ElMessage.error('连接失败，请检查网络')
    tab.statusMessage = '连接失败'
  }
}

function onTabMessage(tab, message) {
  if (!tab.terminal) return
  switch (message.type) {
    case 'output':
      tab.terminal.write(message.data)
      break
    case 'exit':
      tab.terminal.writeln('\r\n\x1b[33m[会话已结束]\x1b[0m')
      tab.statusMessage = '会话已结束'
      tab.connected = false
      break
    case 'error':
      tab.terminal.writeln(`\r\n\x1b[1;31m[错误] ${message.data}\x1b[0m`)
      tab.statusMessage = '错误: ' + message.data
      break
    case 'pong':
      break
  }
}

/** Switch the visible tab. */
function switchTab(id) {
  activeTabId.value = id
  for (const tab of tabs) {
    const visible = tab.id === id
    tab.containerEl.style.display = visible ? '' : 'none'
    if (visible) {
      nextTick(() => {
        tab.fitAddon?.fit()
        tab.terminal?.focus()
      })
    }
  }
  // Reset search when switching tabs
  if (searchVisible.value) {
    searchQuery.value = ''
  }
}

/** Close a tab and clean up all resources. */
function closeTab(id) {
  const idx = tabs.findIndex(t => t.id === id)
  if (idx === -1) return

  const tab = tabs[idx]
  tab.ws?.close()
  tab.terminal?.dispose()
  tab.containerEl.remove()
  tabs.splice(idx, 1)

  if (tabs.length === 0) {
    // All tabs closed — create a fresh one
    createTab()
  } else if (activeTabId.value === id) {
    // Switch to neighbor tab
    const next = tabs[Math.min(idx, tabs.length - 1)]
    switchTab(next.id)
  }
}

// ── Search (operates on active tab) ──────────────────────────────
function toggleSearch() {
  searchVisible.value = !searchVisible.value
  if (searchVisible.value) {
    nextTick(() => searchInputRef.value?.focus())
  } else {
    searchQuery.value = ''
    activeTab.value?.searchAddon?.clearDecorations()
    activeTab.value?.terminal?.focus()
  }
}

function handleSearchInput(val) {
  if (val) activeTab.value?.searchAddon?.findNext(val)
  else activeTab.value?.searchAddon?.clearDecorations()
}

function searchNext() {
  if (searchQuery.value) activeTab.value?.searchAddon?.findNext(searchQuery.value)
}
function searchPrev() {
  if (searchQuery.value) activeTab.value?.searchAddon?.findPrevious(searchQuery.value)
}

// ── Header Actions ───────────────────────────────────────────────
function handleNewSession() {
  createTab()
}

function handleClearTerminal() {
  activeTab.value?.terminal?.clear()
}

// ── Lifecycle ────────────────────────────────────────────────────
onMounted(async () => {
  await nextTick()

  // ResizeObserver on the shared terminal area
  resizeObserver = new ResizeObserver(() => {
    const tab = activeTab.value
    if (tab?.fitAddon && terminalAreaRef.value) tab.fitAddon.fit()
  })
  resizeObserver.observe(terminalAreaRef.value)

  // Create first tab
  createTab()
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  for (const tab of tabs) {
    tab.ws?.close()
    tab.terminal?.dispose()
  }
  tabs.length = 0
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

/* ── Tab Bar ────────────────────────────────────────────────────── */
.terminal-tab-bar {
  display: flex;
  /* align-items: center; */
  justify-content: space-between;
  background-color: #16161e;
  border-bottom: 1px solid #292e42;
  padding: 0 8px;
  min-height: 38px;
  gap: 8px;
}

.tab-list {
  display: flex;
  align-items: center;
  gap: 2px;
  overflow-x: auto;
  flex: 1;
  min-width: 0;
}

.tab-list::-webkit-scrollbar { height: 0; }

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 12px;
  color: #565f89;
  cursor: pointer;
  border-radius: 6px 6px 0 0;
  white-space: nowrap;
  user-select: none;
  transition: background 0.15s, color 0.15s;
  border: 1px solid transparent;
  border-bottom: none;
  position: relative;
}

.tab-item:hover {
  color: #a9b1d6;
  background-color: #1f2335;
}

.tab-item.active {
  color: #c0caf5;
  background-color: #1a1b26;
  border-color: #292e42;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 1px;
  background-color: #1a1b26;
}

.tab-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-connected { background-color: #9ece6a; }
.dot-disconnected { background-color: #f7768e; }

.tab-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tab-close {
  font-size: 14px;
  line-height: 1;
  color: #565f89;
  border-radius: 3px;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
}

.tab-close:hover {
  color: #f7768e;
  background-color: rgba(247, 118, 142, 0.15);
}

.tab-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-shrink: 0;
  padding: 4px 0;
}

.tab-actions :deep(.el-button) {
  --el-button-bg-color: #292e42;
  --el-button-border-color: #292e42;
  --el-button-text-color: #a9b1d6;
  --el-button-hover-bg-color: #3b4261;
  --el-button-hover-border-color: #3b4261;
  --el-button-hover-text-color: #c0caf5;
}

.tab-actions :deep(.el-button--primary) {
  --el-button-bg-color: var(--el-color-primary);
  --el-button-border-color: var(--el-color-primary);
  --el-button-text-color: #fff;
}

/* ── Search Bar ─────────────────────────────────────────────────── */
.terminal-search-bar {
  padding: 6px 16px;
  background-color: #1f2335;
  border-bottom: 1px solid #292e42;
}

.terminal-search-bar :deep(.el-input) {
  max-width: 400px;
}

.terminal-search-bar :deep(.el-input__wrapper) {
  background-color: #292e42;
  box-shadow: none;
}

.terminal-search-bar :deep(.el-input__inner) {
  color: #c0caf5;
}

/* ── Terminal Area ──────────────────────────────────────────────── */
.terminal-area {
  flex: 1;
  overflow: hidden;
  padding: 4px 8px;
  position: relative;
}

:deep(.terminal-tab-pane) {
  width: 100%;
  height: 100%;
}

/* ── Status Bar ─────────────────────────────────────────────────── */
.terminal-status-bar {
  display: flex;
  justify-content: space-between;
  padding: 6px 16px;
  background-color: #16161e;
  border-top: 1px solid #292e42;
  color: #565f89;
  font-size: 12px;
  line-height: 1;
}

.terminal-size {
  font-family: monospace;
  color: #414868;
}

/* ── xterm overrides ────────────────────────────────────────────── */
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
