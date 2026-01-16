<template>
  <div class="app-container">
    <el-tabs v-model="active" type="card" @tab-click="onTabClick" @tab-remove="removeTab" :before-leave="beforeLeave">
      <el-tab-pane v-for="t in tabs" :key="t.key" :name="t.key" :label="t.title" :closable="tabs.length > 1">
        <div class="tab-content" :style="{ height: tabHeight + 'px' }">
          <div class="query-view-wrapper" :style="{ height: queryViewHeight + 'px' }">
            <query-view
              :dataSourceId="t.dataSourceId"
              :sqlText="t.sqlText"
              :pageSize="t.pageSize"
              :offset="t.offset"
              :templateParams="t.templateParams"
              :next="t.next"
              :ds-list="dsList"
              :running="t.running"
              :editorHeight="editorHeight"
              @update:dataSourceId="v => (t.dataSourceId = v)"
              @update:sqlText="v => (t.sqlText = v)"
              @update:pageSize="v => (t.pageSize = v)"
              @update:offset="v => (t.offset = v)"
              @update:templateParams="v => (t.templateParams = v)"
              @run="(p) => runQuery(t, p)"
              @export="(p) => exportRows(t, p)"
            />
          </div>

          <resizable-splitter v-if="t.columns.length > 0" @resize="onResizeSplitter" />

          <div v-if="t.columns.length > 0" class="query-result-wrapper" :style="{ height: resultHeight + 'px', overflow: 'auto' }">
            <query-result :columns="t.columns" :rows="t.rows" />
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
import { Plus } from '@element-plus/icons-vue';
import { listDatasource } from '@/api/datasource'
import { executeQuery, exportQuery } from '@/api/dataservice'
import { scrollTo } from '@/utils/scroll-to'
import QueryView from './queryView.vue'
import QueryResult from './queryResult.vue'
import ResizableSplitter from './resizable-splitter.vue'
const { proxy } = getCurrentInstance()

const active = ref('')
const tabs = ref([])
const dsList = ref([])
const addKey = '__add__'

// 高度管理
const tabHeight = ref(600)
const queryViewHeight = ref(450)
const editorHeight = ref(400)
const resultHeight = ref(300)

// 初始化高度
function initHeights() {
  const windowHeight = window.innerHeight
  tabHeight.value = Math.max(400, windowHeight - 200)
  queryViewHeight.value = Math.floor(tabHeight.value * 1.0)
  resultHeight.value = tabHeight.value - queryViewHeight.value - 8 // 8px for splitter
  editorHeight.value = queryViewHeight.value - 100 // 减去表单和其他元素的高度
}

// 分割条拖拽调整
function onResizeSplitter(newSize) {
  queryViewHeight.value = newSize
  const remainingHeight = tabHeight.value - newSize - 8 // 8px for splitter
  resultHeight.value = Math.max(100, remainingHeight)
  editorHeight.value = Math.max(100, queryViewHeight.value - 150)
}

// 重置高度
function resetHeights() {
  initHeights()
}

function addTab() {
  const key = 'new-' + Date.now()
  tabs.value.push({ key, title: '查询页', dataSourceId: undefined, sqlText: '', templateParams: {}, pageSize: 20, offset: 0, next: null, columns: [], rows: [], running: false })
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
      // 重置结果框高度
      resetHeights()
      // 查询成功，向下滚动30%
      scrollTo(300)
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
  initHeights()
  getDsList()
  addTab()
})
</script>
<style scoped>
.tab-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.query-view-wrapper {
  flex-shrink: 0;
  overflow: hidden;
  border: solid 1px #77d50d;
}

.query-result-wrapper {
  flex: 1;
  overflow: auto;
  border: solid 1px #c10909;
}
</style>