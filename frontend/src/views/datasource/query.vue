<template>
  <div class="app-container">
    <el-form :inline="true" label-width="80px">
      <el-form-item label="数据源">
        <el-select v-model="currentId" placeholder="选择数据源" style="width: 260px" @change="loadInfo">
          <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="runQuery" :disabled="!currentId || running">执行</el-button>
        <el-button @click="resetResult">清空结果</el-button>
      </el-form-item>
    </el-form>

    <el-input v-model="sql" type="textarea" :rows="8" placeholder="输入 SQL" />

    <el-table v-loading="running" :data="rows" style="margin-top: 16px">
      <el-table-column v-for="col in columns" :key="col" :prop="col" :label="col" />
    </el-table>
  </div>
</template>

<script setup>
import { listDatasource, executeQueryById } from '@/api/datasource'
const route = useRoute()
const { proxy } = getCurrentInstance()

const currentId = ref(undefined)
const dsList = ref([])
const sql = ref('')
const columns = ref([])
const rows = ref([])
const running = ref(false)

function getList() {
  listDatasource({ pageNum: 1, pageSize: 100 }).then(res => {
    dsList.value = res.rows || []
  })
}

function loadInfo() {}

function resetResult() {
  columns.value = []
  rows.value = []
}

function runQuery() {
  if (!currentId.value || !sql.value) return
  running.value = true
  executeQueryById(currentId.value, { sql: sql.value }).then(res => {
    const data = res.data || {}
    columns.value = data.columns || []
    rows.value = (data.rows || []).map(r => {
      const obj = {}
      for (let i = 0; i < columns.value.length; i++) obj[columns.value[i]] = r[i]
      return obj
    })
  }).finally(() => {
    running.value = false
  })
}

onMounted(() => {
  getList()
  const pid = route.params.id
  if (pid) {
    currentId.value = Number(pid)
  }
})
</script>
