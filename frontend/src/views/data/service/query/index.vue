<template>
  <div class="app-container">
    <el-tabs v-model="active" type="card" @tab-click="onTabClick" @tab-remove="removeTab" :before-leave="beforeLeave">
      <el-tab-pane v-for="t in tabs" :key="t.key" :name="t.key" :label="t.title" :closable="tabs.length > 1">
        <div class="layout-controls" v-if="t.columns.length > 0">
          <span class="layout-label">布局预设：</span>
          <el-button-group size="small">
            <el-button :type="t.layoutMode === 'editor' ? 'primary' : ''" @click="setLayoutMode(t, 'editor')">
              <el-icon><Upload /></el-icon> 编辑优先
            </el-button>
            <el-button :type="t.layoutMode === 'balanced' ? 'primary' : ''" @click="setLayoutMode(t, 'balanced')">
              <el-icon><Minus /></el-icon> 均衡布局
            </el-button>
            <el-button :type="t.layoutMode === 'result' ? 'primary' : ''" @click="setLayoutMode(t, 'result')">
              <el-icon><Download /></el-icon> 结果优先
            </el-button>
          </el-button-group>
        </div>

        <div class="tab-content" :style="{ height: getTabHeight(t) + 'px' }">
          <splitpanes
            horizontal
            class="query-splitpanes default-theme"
            @resize="event => onPaneResize(t, event)"
          >
            <pane :size="getQueryPaneSize(t)" :min-size="getQueryPaneMinSize(t)">
              <div class="query-view-wrapper">
                <query-view
                  :dataSourceId="t.dataSourceId"
                  :sqlText="t.sqlText"
                  :pageSize="t.pageSize"
                  :offset="t.offset"
                  :templateParams="t.templateParams"
                  :next="t.next"
                  :ds-list="dsList"
                  :running="t.running"
                  :editorHeight="getEditorHeight(t)"
                  @update:dataSourceId="v => (t.dataSourceId = v)"
                  @update:sqlText="v => (t.sqlText = v)"
                  @update:pageSize="v => (t.pageSize = v)"
                  @update:offset="v => (t.offset = v)"
                  @update:templateParams="v => (t.templateParams = v)"
                  @run="(p) => runQuery(t, p)"
                  @export="(p) => exportRows(t, p)"
                />
              </div>
            </pane>

            <pane :size="100 - getQueryPaneSize(t)" :min-size="getResultPaneMinSize(t)">
              <div class="query-result-wrapper">
                <div v-if="t.columns.length === 0" class="empty-result">
                  <el-empty description="执行查询后在此显示结果" :image-size="80" />
                </div>
                <query-result v-else :columns="t.columns" :rows="t.rows" result-height="100%" />
              </div>
            </pane>
          </splitpanes>
        </div>
      </el-tab-pane>
      <el-tab-pane :name="addKey" label="新增查询">
        <template #label>
          <el-icon><Plus /></el-icon>
        </template>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup name="DataServiceQuery">
import { getCurrentInstance } from 'vue'
import { Plus, Upload, Minus, Download } from '@element-plus/icons-vue'
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'
import { listDatasource } from '@/api/data/datasource'
import { executeQuery, exportQuery } from '@/api/data/service'
import QueryView from './queryView.vue'
import QueryResult from './queryResult.vue'

const { proxy } = getCurrentInstance()

const active = ref('')
const tabs = ref([])
const dsList = ref([])
const addKey = '__add__'
const windowHeight = ref(window.innerHeight)

const LAYOUT_PRESETS = {
  editor: 0.65,
  balanced: 0.5,
  result: 0.35,
}

const STORAGE_KEY = 'query-layout-preference'
const BREAKPOINTS = {
  mobile: 768,
  tablet: 1024,
  desktop: 1440,
}

function getDeviceType() {
  const width = window.innerWidth
  if (width < BREAKPOINTS.mobile) return 'mobile'
  if (width < BREAKPOINTS.tablet) return 'tablet'
  return 'desktop'
}

function loadLayoutPreference() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    const preference = saved ? JSON.parse(saved) : { mode: 'balanced' }
    if (!saved && getDeviceType() === 'mobile') {
      preference.mode = 'result'
    }
    return preference
  } catch {
    return { mode: 'balanced' }
  }
}

function saveLayoutPreference(mode) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ mode }))
  } catch (error) {
    console.warn('保存布局偏好失败:', error)
  }
}

function getHeaderHeight() {
  switch (getDeviceType()) {
    case 'mobile':
      return 140
    case 'tablet':
      return 160
    default:
      return 180
  }
}

function getMinTabHeight() {
  switch (getDeviceType()) {
    case 'mobile':
      return 400
    case 'tablet':
      return 450
    default:
      return 500
  }
}

function getMinQueryHeight() {
  return getDeviceType() === 'mobile' ? 220 : 260
}

function getMinResultHeight() {
  return getDeviceType() === 'mobile' ? 150 : 180
}

function clampRatio(tabHeight, ratio) {
  const minQueryRatio = getMinQueryHeight() / tabHeight
  const maxQueryRatio = 1 - getMinResultHeight() / tabHeight
  return Math.min(maxQueryRatio, Math.max(minQueryRatio, ratio))
}

function buildHeights(tabHeight, ratio) {
  const splitRatio = clampRatio(tabHeight, ratio)
  const queryViewHeight = Math.round(tabHeight * splitRatio)
  return {
    tabHeight,
    splitRatio,
    queryViewHeight,
    resultHeight: Math.max(getMinResultHeight(), Math.round(tabHeight * (1 - splitRatio))),
    editorHeight: Math.max(180, queryViewHeight - 120),
  }
}

function getDefaultHeights() {
  const headerHeight = getHeaderHeight()
  const minHeight = getMinTabHeight()
  const tabHeight = Math.max(minHeight, windowHeight.value - headerHeight)
  return buildHeights(tabHeight, LAYOUT_PRESETS.balanced)
}

function getHeightByMode(tabHeight, mode) {
  return buildHeights(tabHeight, LAYOUT_PRESETS[mode] || LAYOUT_PRESETS.balanced)
}

function getTabHeight(tab) {
  return tab.heights?.tabHeight ?? getDefaultHeights().tabHeight
}

function getQueryPaneSize(tab) {
  return Number(((tab.heights?.splitRatio ?? LAYOUT_PRESETS.balanced) * 100).toFixed(2))
}

function getEditorHeight(tab) {
  return tab.heights?.editorHeight ?? getDefaultHeights().editorHeight
}

function getQueryPaneMinSize(tab) {
  return Number(((getMinQueryHeight() / getTabHeight(tab)) * 100).toFixed(2))
}

function getResultPaneMinSize(tab) {
  return Number(((getMinResultHeight() / getTabHeight(tab)) * 100).toFixed(2))
}

function setLayoutMode(tab, mode) {
  tab.heights = getHeightByMode(getTabHeight(tab), mode)
  tab.layoutMode = mode
  saveLayoutPreference(mode)
}

function updateAllTabsHeight() {
  const nextTabHeight = getDefaultHeights().tabHeight

  tabs.value.forEach(tab => {
    const currentRatio = tab.heights?.splitRatio ?? LAYOUT_PRESETS.balanced
    if (tab.layoutMode && tab.layoutMode !== 'custom') {
      tab.heights = getHeightByMode(nextTabHeight, tab.layoutMode)
    } else {
      tab.heights = buildHeights(nextTabHeight, currentRatio)
    }
  })
}

let resizeTimer = null
function handleWindowResize() {
  if (resizeTimer) {
    clearTimeout(resizeTimer)
  }

  resizeTimer = setTimeout(() => {
    windowHeight.value = window.innerHeight
    updateAllTabsHeight()
  }, 200)
}

function onPaneResize(tab, event) {
  const queryPane = event?.panes?.[0]
  if (!queryPane) {
    return
  }

  tab.heights = buildHeights(getTabHeight(tab), Number(queryPane.size) / 100)
  tab.layoutMode = 'custom'
}

function addTab() {
  const key = 'new-' + Date.now()
  const preference = loadLayoutPreference()
  const mode = preference.mode || 'balanced'
  const defaultHeights = getDefaultHeights()

  tabs.value.push({
    key,
    title: '查询页',
    dataSourceId: undefined,
    sqlText: '',
    templateParams: {},
    pageSize: 20,
    offset: 0,
    next: null,
    columns: [],
    rows: [],
    running: false,
    layoutMode: mode,
    heights: getHeightByMode(defaultHeights.tabHeight, mode),
  })
  active.value = key
}

function removeTab(name) {
  if (tabs.value.length <= 1) {
    proxy.$modal.msgWarning('至少保留一个查询页')
    return
  }
  const idx = tabs.value.findIndex(t => t.key === name)
  if (idx >= 0) {
    tabs.value.splice(idx, 1)
    if (tabs.value.length) active.value = tabs.value[Math.max(0, idx - 1)].key
  }
}

function runQuery(t, p) {
  if (!t.dataSourceId || !t.sqlText) {
    proxy.$modal.msgError('请选择数据源并输入SQL')
    return
  }
  t.running = true
  const payload = { dataSourceId: t.dataSourceId, sql: t.sqlText, params: t.templateParams || {} }
  if (p && typeof p.pageSize !== 'undefined') payload.pageSize = p.pageSize
  if (p && typeof p.offset !== 'undefined') payload.offset = p.offset
  executeQuery(payload).then(res => {
    applyResult(t, res.data)
    proxy.$modal.msgSuccess('查询成功')
  }).finally(() => {
    t.running = false
  })
}

function exportRows(t, p) {
  if (!t.dataSourceId || !t.sqlText) {
    proxy.$modal.msgError('请选择数据源并输入SQL')
    return
  }
  const payload = { dataSourceId: t.dataSourceId, sql: t.sqlText, params: (p && p.params) || t.templateParams || {} }
  if (p && typeof p.pageSize !== 'undefined') payload.pageSize = p.pageSize
  if (p && typeof p.offset !== 'undefined') payload.offset = p.offset
  exportQuery(payload).then(res => {
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'query_export.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    proxy.$modal.msgSuccess('导出成功')
  }).catch(err => {
    proxy.$modal.msgError(err?.msg || '导出失败')
  })
}

function applyResult(t, data) {
  const cols = data?.columns || []
  const rows = data?.rows || []
  t.columns = cols
  t.rows = rows.map(row => {
    const item = {}
    for (let i = 0; i < cols.length; i++) item[i] = row[i]
    return item
  })
  t.next = data?.next || null
}

function getDsList() {
  listDatasource().then(res => {
    dsList.value = res.rows || []
  })
}

function onTabClick(tab) {
  if (tab.paneName === addKey) {
    addTab()
  }
}

function beforeLeave(activeName) {
  return new Promise(resolve => {
    resolve(activeName !== addKey)
  })
}

onMounted(() => {
  getDsList()
  addTab()
  window.addEventListener('resize', handleWindowResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleWindowResize)
  if (resizeTimer) {
    clearTimeout(resizeTimer)
  }
})
</script>

<style scoped>
.layout-controls {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 0;
}

.layout-label {
  font-size: 13px;
  color: #606266;
  margin-right: 12px;
  font-weight: 500;
}

.tab-content {
  overflow: hidden;
}

.query-splitpanes {
  height: 100%;
}

:deep(.query-splitpanes > .splitpanes__pane) {
  background-color: transparent;
}

.query-view-wrapper {
  height: 100%;
  overflow: hidden;
}

.query-result-wrapper {
  height: 100%;
  overflow: hidden;
  min-height: 0;
  box-sizing: border-box;
}

.empty-result {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

:deep(.query-splitpanes .splitpanes__splitter) {
  position: relative;
  background: linear-gradient(180deg, #eef3fb 0%, #dbe7f8 100%);
  border-top: 1px solid #c6d6f0;
  border-bottom: 1px solid #c6d6f0;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

:deep(.query-splitpanes .splitpanes__splitter::before) {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 52px;
  height: 6px;
  border-radius: 999px;
  transform: translate(-50%, -50%);
  background: rgba(64, 158, 255, 0.35);
}

:deep(.query-splitpanes .splitpanes__splitter:hover) {
  background: linear-gradient(180deg, #dfeafb 0%, #c9dcf8 100%);
  border-color: #8fb3ea;
}
</style>
