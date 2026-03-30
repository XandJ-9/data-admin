<template>
  <div class="app-container query-page">
    <el-tabs v-model="active" type="card" @tab-click="onTabClick" @tab-remove="removeTab" :before-leave="beforeLeave">
      <el-tab-pane v-for="t in tabs" :key="t.key" :name="t.key" :label="t.title" :closable="tabs.length > 1">
        <div class="tab-content">
          <splitpanes horizontal class="query-splitpanes default-theme" @resized="event => onPaneResized(t, event)">
            <pane :size="t.splitSize" :min-size="20">
              <div class="pane-inner">
                <query-view
                  :dataSourceId="t.dataSourceId"
                  :sqlText="t.sqlText"
                  :pageSize="t.pageSize"
                  :offset="t.offset"
                  :templateParams="t.templateParams"
                  :next="t.next"
                  :ds-list="dsList"
                  :running="t.running"
                  :hasResult="t.columns.length > 0"
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
            <pane :size="100 - t.splitSize" :min-size="15">
              <div class="pane-inner">
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
import { Plus } from '@element-plus/icons-vue'
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

const DEFAULT_SPLIT = 55

function onPaneResized(tab, event) {
  const first = event?.[0]
  if (first) {
    tab.splitSize = Number(first.size.toFixed(1))
  }
}

function addTab() {
  const key = 'new-' + Date.now()
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
    splitSize: DEFAULT_SPLIT,
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
  return activeName !== addKey
}

onMounted(() => {
  getDsList()
  addTab()
})
</script>

<style scoped>
.query-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 84px);
  overflow: hidden;
}

.query-page :deep(.el-tabs) {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.query-page :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.query-page :deep(.el-tab-pane) {
  height: 100%;
}

.tab-content {
  height: 100%;
  overflow: hidden;
}

.query-splitpanes {
  height: 100%;
}

.pane-inner {
  height: 100%;
  overflow: hidden;
}

:deep(.query-splitpanes > .splitpanes__pane) {
  background-color: transparent;
}

.empty-result {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

:deep(.query-splitpanes > .splitpanes__splitter) {
  background: #f0f2f5;
  border-top: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
  height: 7px;
  position: relative;
  transition: background 0.2s;
}

:deep(.query-splitpanes > .splitpanes__splitter::before) {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 40px;
  height: 4px;
  border-radius: 2px;
  transform: translate(-50%, -50%);
  background: #c0c4cc;
  transition: background 0.2s;
}

:deep(.query-splitpanes > .splitpanes__splitter:hover) {
  background: #e6e9ed;
}

:deep(.query-splitpanes > .splitpanes__splitter:hover::before) {
  background: #409eff;
}
</style>
