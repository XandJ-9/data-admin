<template>
  <div class="app-container">
    <el-tabs v-model="active" type="card" @tab-click="onTabClick" @tab-remove="removeTab" :before-leave="beforeLeave">
      <el-tab-pane v-for="t in tabs" :key="t.key" :name="t.key" :label="t.title" :closable="tabs.length > 1">
        <!-- 布局预设按钮 -->
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
          <div class="query-view-wrapper" :style="{ height: getQueryViewHeight(t) + 'px' }">
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

          <resizable-splitter @resize="(newSize) => onResizeSplitter(t, newSize)" />

          <div class="query-result-wrapper" :style="{ height: getResultHeight(t) + 'px', overflow: 'auto' }">
            <div v-if="t.columns.length === 0" class="empty-result">
              <el-empty description="执行查询后在此显示结果" :image-size="80" />
            </div>
            <query-result v-else :columns="t.columns" :rows="t.rows" :result-height="getResultHeight(t)"/>
          </div>
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
import { Plus, Upload, Minus, Download } from '@element-plus/icons-vue';
import { listDatasource } from '@/api/data/asset'
import { executeQuery, exportQuery } from '@/api/data/service'
import QueryView from './queryView.vue'
import QueryResult from './queryResult.vue'
import ResizableSplitter from './resizable-splitter.vue'

const { proxy } = getCurrentInstance()

const active = ref('')
const tabs = ref([])
const dsList = ref([])
const addKey = '__add__'

// 响应式：窗口高度
const windowHeight = ref(window.innerHeight)

// 布局比例配置
const LAYOUT_PRESETS = {
  editor: 0.65,    // 编辑优先：编辑器65%，结果35%
  balanced: 0.5,   // 均衡布局：各50%
  result: 0.35     // 结果优先：编辑器35%，结果65%
}

// 存储键名
const STORAGE_KEY = 'query-layout-preference'

// 响应式断点配置
const BREAKPOINTS = {
  mobile: 768,     // 移动端
  tablet: 1024,    // 平板
  desktop: 1440    // 桌面
}

// 获取当前设备类型
function getDeviceType() {
  const width = window.innerWidth
  if (width < BREAKPOINTS.mobile) return 'mobile'
  if (width < BREAKPOINTS.tablet) return 'tablet'
  return 'desktop'
}

// 加载用户保存的布局偏好
function loadLayoutPreference() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    const preference = saved ? JSON.parse(saved) : { mode: 'balanced' }
    // 根据设备类型调整默认布局
    const deviceType = getDeviceType()
    if (!saved && deviceType === 'mobile') {
      preference.mode = 'result' // 移动端默认结果优先
    }
    return preference
  } catch {
    return { mode: 'balanced' }
  }
}

// 保存布局偏好
function saveLayoutPreference(mode) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ mode }))
  } catch (e) {
    console.warn('保存布局偏好失败:', e)
  }
}

// 计算可用的头部高度（根据设备类型）
function getHeaderHeight() {
  const deviceType = getDeviceType()
  switch (deviceType) {
    case 'mobile':
      return 140  // 移动端头部更紧凑
    case 'tablet':
      return 160
    default:
      return 180  // 桌面端
  }
}

// 获取最小高度（根据设备类型）
function getMinTabHeight() {
  const deviceType = getDeviceType()
  switch (deviceType) {
    case 'mobile':
      return 400   // 移动端最小高度
    case 'tablet':
      return 450
    default:
      return 500   // 桌面端最小高度
  }
}

// 获取默认高度配置（响应式）
function getDefaultHeights() {
  const headerHeight = getHeaderHeight()
  const minHeight = getMinTabHeight()
  const tabHeight = Math.max(minHeight, windowHeight.value - headerHeight)
  const queryViewRatio = 0.5 // 默认均衡布局
  const queryViewHeight = Math.floor(tabHeight * queryViewRatio)
  const resultHeight = tabHeight - queryViewHeight - 8 // 8px for splitter

  // 根据设备调整编辑器最小高度
  const deviceType = getDeviceType()
  const minEditorHeight = deviceType === 'mobile' ? 120 : 150
  const editorHeight = Math.max(minEditorHeight, queryViewHeight - 110)

  return { tabHeight, queryViewHeight, resultHeight, editorHeight }
}

// 根据布局模式获取高度
function getHeightByMode(tabHeight, mode) {
  const ratio = LAYOUT_PRESETS[mode] || LAYOUT_PRESETS.balanced
  const queryViewHeight = Math.floor(tabHeight * ratio)
  const resultHeight = tabHeight - queryViewHeight - 8
  const editorHeight = Math.max(150, queryViewHeight - 110)
  return { queryViewHeight, resultHeight, editorHeight }
}

// 获取 tab 的各个高度
function getTabHeight(tab) {
  return tab.heights?.tabHeight ?? getDefaultHeights().tabHeight
}

function getQueryViewHeight(tab) {
  return tab.heights?.queryViewHeight ?? getDefaultHeights().queryViewHeight
}

function getResultHeight(tab) {
  return tab.heights?.resultHeight ?? getDefaultHeights().resultHeight
}

function getEditorHeight(tab) {
  return tab.heights?.editorHeight ?? getDefaultHeights().editorHeight
}

// 设置布局模式
function setLayoutMode(tab, mode) {
  if (!tab.heights) {
    tab.heights = { ...getDefaultHeights() }
    tab.heights.tabHeight = getTabHeight(tab)
  }

  const heights = getHeightByMode(tab.heights.tabHeight, mode)
  tab.heights.queryViewHeight = heights.queryViewHeight
  tab.heights.resultHeight = heights.resultHeight
  tab.heights.editorHeight = heights.editorHeight
  tab.layoutMode = mode

  saveLayoutPreference(mode)
}

// 更新所有标签页的高度（窗口大小变化时调用）
function updateAllTabsHeight() {
  const newDefaultHeights = getDefaultHeights()

  tabs.value.forEach(tab => {
    if (!tab.heights) {
      tab.heights = { ...newDefaultHeights }
      return
    }

    // 保存当前的比例
    const currentRatio = tab.heights.queryViewHeight / tab.heights.tabHeight

    // 更新tab高度
    tab.heights.tabHeight = newDefaultHeights.tabHeight

    // 根据当前比例重新分配高度
    if (tab.layoutMode && tab.layoutMode !== 'custom') {
      // 如果是预设模式，重新应用预设
      const heights = getHeightByMode(tab.heights.tabHeight, tab.layoutMode)
      tab.heights.queryViewHeight = heights.queryViewHeight
      tab.heights.resultHeight = heights.resultHeight
      tab.heights.editorHeight = heights.editorHeight
    } else {
      // 如果是自定义模式，保持比例
      let newQueryViewHeight = Math.floor(tab.heights.tabHeight * currentRatio)

      // 确保在合理范围内
      const minQueryHeight = getDeviceType() === 'mobile' ? 120 : 150
      const maxQueryHeight = tab.heights.tabHeight - 8 - 100
      newQueryViewHeight = Math.max(minQueryHeight, Math.min(maxQueryHeight, newQueryViewHeight))

      tab.heights.queryViewHeight = newQueryViewHeight
      tab.heights.resultHeight = tab.heights.tabHeight - newQueryViewHeight - 8

      const minEditorHeight = getDeviceType() === 'mobile' ? 120 : 150
      tab.heights.editorHeight = Math.max(minEditorHeight, tab.heights.queryViewHeight - 110)
    }
  })
}

// 防抖处理窗口大小变化
let resizeTimer = null
function handleWindowResize() {
  if (resizeTimer) {
    clearTimeout(resizeTimer)
  }

  resizeTimer = setTimeout(() => {
    windowHeight.value = window.innerHeight
    updateAllTabsHeight()
  }, 200) // 200ms 防抖
}

// 分割条拖拽调整（针对指定 tab）
function onResizeSplitter(tab, newSize) {
  if (!tab.heights) {
    tab.heights = { ...getDefaultHeights() }
    tab.heights.tabHeight = getTabHeight(tab)
  }

  const minQueryHeight = 150 // 最小查询区高度
  const minResultHeight = 100 // 最小结果区高度

  // 限制查询区高度范围
  const maxSize = tab.heights.tabHeight - 8 - minResultHeight
  const clampedSize = Math.max(minQueryHeight, Math.min(maxSize, newSize))

  tab.heights.queryViewHeight = clampedSize
  tab.heights.resultHeight = tab.heights.tabHeight - clampedSize - 8
  tab.heights.editorHeight = Math.max(150, tab.heights.queryViewHeight - 110)

  // 拖拽后清除预设模式标记
  tab.layoutMode = 'custom'
}

function addTab() {
  const key = 'new-' + Date.now()
  const preference = loadLayoutPreference()
  const mode = preference.mode || 'balanced'

  // 初始化时就设置好高度和布局模式
  const defaultHeights = getDefaultHeights()
  const layoutHeights = getHeightByMode(defaultHeights.tabHeight, mode)

  const newTab = {
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
    heights: {
      ...defaultHeights,
      ...layoutHeights
    }
  }

  tabs.value.push(newTab)
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
    // 不再自动调整高度，保持用户当前的布局
  }).finally(() => (t.running = false))
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
    // const blob = new Blob([res], { type: 'text/csv;charset=utf-8' })
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `query_export.csv`
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
  const next = data?.next || null
  t.columns = cols
  t.rows = rows.map(r => {
    const obj = {}
    // for (let i = 0; i < cols.length; i++) obj[cols[i]] = r[i]
    for (let i = 0; i < cols.length; i++) obj[i] = r[i]
    return obj
  })
  t.next = next
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

function beforeLeave(activeName, oldActiveName) {
  return new Promise((resolve, reject) => {
    if (activeName === addKey) {
      resolve(false);
    } else {
      resolve(true);
    }
  });
}



onMounted(() => {
  getDsList()
  addTab()
  // 添加窗口大小变化监听
  window.addEventListener('resize', handleWindowResize)
})

onUnmounted(() => {
  // 移除窗口大小变化监听
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
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.query-view-wrapper {
  flex-shrink: 0;
  overflow: hidden;
}

.query-result-wrapper {
  flex: 1;
  overflow: auto;
  min-height: 100px;
}

.empty-result {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}
</style>