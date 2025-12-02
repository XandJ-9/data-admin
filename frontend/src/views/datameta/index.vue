<template>
  <div class="app-container">
    <el-form :inline="true" label-width="80px" style="margin-bottom: 12px">
      <el-form-item label="数据源">
        <el-select v-model="dsId" placeholder="选择数据源" style="width: 260px">
          <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :disabled="!dsId || collecting" @click="handleCollect">采集元数据</el-button>
        <el-button type="success" :disabled="!dsId" @click="getTables">刷新</el-button>
      </el-form-item>
    </el-form>
    <el-form-item label="筛选">
      <el-input v-model="filterName" placeholder="搜索表名" />
    </el-form-item>

    <el-table v-loading="loading" :data="displayTables" row-key="id" style="width: 100%; margin-top: 12px" border>
      <el-table-column prop="tableName" label="表名" />
      <el-table-column label="操作" width="160">
        <template #default="scope">
          <el-button size="small" @click="openColumns(scope.row.tableName)">查看列</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showColumns" title="字段信息" width="70%">
      <div style="margin-bottom: 8px">当前表：{{ currentTable }}</div>
      <el-table :data="columns" border height="50vh">
        <el-table-column prop="name" label="列名" />
        <el-table-column prop="type" label="类型" />
        <el-table-column prop="notnull" label="非空" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.notnull ? 'danger' : 'info'">{{ scope.row.notnull ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="primary" label="主键" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.primary ? 'success' : 'info'">{{ scope.row.primary ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="default" label="默认值" />
      </el-table>
      <template #footer>
        <el-button @click="showColumns=false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
 </template>

 <script setup name="DataMeta">
import { listDatasource } from '@/api/datasource'
import { listMetaTables, listMetaColumns, collectMeta } from '@/api/datameta'
const { proxy } = getCurrentInstance()

const dsId = ref()
const dsList = ref([])
const tables = ref([])
const filterName = ref('')
const displayTables = computed(() => {
  const kw = (filterName.value || '').trim().toLowerCase()
  if (!kw) return tables.value
  return tables.value.filter(t => String(t.tableName || '').toLowerCase().includes(kw))
})
const columns = ref([])
const currentTable = ref('')
const loading = ref(false)
const collecting = ref(false)
const showColumns = ref(false)

function getDsList() {
  listDatasource({ pageNum: 1, pageSize: 100 }).then(res => {
    dsList.value = res.rows || []
  })
}

function getTables() {
  if (!dsId.value) return
  loading.value = true
  listMetaTables({ dataSourceId: dsId.value, pageNum: 1, pageSize: 1000 }).then(res => {
    tables.value = res.rows || []
  }).finally(() => (loading.value = false))
}

function openColumns(t) {
  if (!dsId.value) return
  currentTable.value = t
  listMetaColumns({ dataSourceId: dsId.value, tableName: t, pageNum: 1, pageSize: 1000 }).then(res => {
    columns.value = res.rows || []
    showColumns.value = true
  })
}

function handleCollect() {
  if (!dsId.value) return
  collecting.value = true
  collectMeta(dsId.value).then(() => {
    proxy.$modal.msgSuccess('采集完成')
    getTables()
  }).finally(() => (collecting.value = false))
}

onMounted(() => {
  getDsList()
})
 </script>

 <style scoped>
 </style>
