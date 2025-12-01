<template>
  <div class="app-container">
    <el-tabs v-model="active" type="card" @tab-click="onTabClick" @tab-remove="removeTab">
      <el-tab-pane v-for="t in tabs" :key="t.key" :name="t.key" :label="t.title" :closable="tabs.length > 1">
        <query-view v-model:dataSourceId="t.dataSourceId" v-model:sqlText="t.sqlText" v-model:pageSize="t.pageSize" v-model:offset="t.offset" :next="t.next" :ds-list="dsList" :running="t.running" @run="(p) => runQuery(t, p)" />
        <query-result :columns="t.columns" :rows="t.rows" />
      </el-tab-pane>
      <el-tab-pane :name="addKey" label="新增查询">
            <template #label>
                <el-icon><Plus /></el-icon>
            </template>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { Plus } from '@element-plus/icons-vue';
import { listDatasource, executeQueryById } from '@/api/datasource'
import QueryView from './queryView.vue'
import QueryResult from './queryResult.vue'
const { proxy } = getCurrentInstance()

const active = ref('')
const tabs = ref([])
const dsList = ref([])
const addKey = '__add__'

function addTab() {
  const key = 'new-' + Date.now()
  tabs.value.push({ key, title: '未命名查询', dataSourceId: undefined, sqlText: '', pageSize: 20, offset: 0, next: null, columns: [], rows: [], running: false })
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
  const payload = { sql: t.sqlText }
  if (p && typeof p.pageSize !== 'undefined') payload.pageSize = p.pageSize
  if (p && typeof p.offset !== 'undefined') payload.offset = p.offset
  executeQueryById(t.dataSourceId, payload).then(res => {
    applyResult(t, res.data)
  }).finally(() => (t.running = false))
}

function applyResult(t, data) {
  const cols = data?.columns || []
  const rows = data?.rows || []
  const next = data?.next || null
  t.columns = cols
  t.rows = rows.map(r => {
    const obj = {}
    for (let i = 0; i < cols.length; i++) obj[cols[i]] = r[i]
    return obj
  })
  t.next = next
}

function getDsList() {
  listDatasource({ pageNum: 1, pageSize: 100 }).then(res => {
    dsList.value = res.rows || []
  })
}

function onTabClick(tab) {
  if (tab.paneName === addKey) {
    addTab()
  }
}

onMounted(() => {
  getDsList()
  addTab()
})
</script>
