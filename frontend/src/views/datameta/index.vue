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

    <el-table v-loading="loading" :data="tables" row-key="id">
      <el-table-column prop="tableName" label="表名" />
      <el-table-column label="查看列" width="120">
        <template #default="scope">
          <el-button size="small" @click="loadColumns(scope.row.tableName)">列</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="columns.length" style="margin-top: 16px">
      <h4>列信息：{{ currentTable }}</h4>
      <el-table :data="columns">
        <el-table-column prop="name" label="列名" />
        <el-table-column prop="type" label="类型" />
        <el-table-column prop="notnull" label="非空" width="80">
          <template #default="scope"><el-tag :type="scope.row.notnull ? 'danger' : 'info'">{{ scope.row.notnull ? '是' : '否' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="primary" label="主键" width="80">
          <template #default="scope"><el-tag :type="scope.row.primary ? 'success' : 'info'">{{ scope.row.primary ? '是' : '否' }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="default" label="默认值" />
      </el-table>
    </div>
  </div>
 </template>

 <script setup>
import { listDatasource } from '@/api/datasource'
import { listMetaTables, listMetaColumns, collectMeta } from '@/api/datameta'
const { proxy } = getCurrentInstance()

const dsId = ref()
const dsList = ref([])
const tables = ref([])
const columns = ref([])
const currentTable = ref('')
const loading = ref(false)
const collecting = ref(false)

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

function loadColumns(t) {
  if (!dsId.value) return
  currentTable.value = t
  listMetaColumns({ dataSourceId: dsId.value, tableName: t, pageNum: 1, pageSize: 1000 }).then(res => {
    columns.value = res.rows || []
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
