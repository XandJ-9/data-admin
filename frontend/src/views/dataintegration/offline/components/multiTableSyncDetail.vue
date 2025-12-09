<template>
  <div>
    <el-card>
      <template #header>
        <span>来源</span>
      </template>
      <el-form :inline="true" :model="form.source" label-width="100px">
        <el-form-item label="数据源">
          <el-select v-model="form.source.dataSourceIds" multiple filterable clearable placeholder="选择数据源" style="width: 420px">
            <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dbList.length" label="数据库">
          <el-select v-model="form.source.databases" value-key="key" multiple filterable clearable placeholder="选择数据库" style="width: 560px">
            <el-option v-for="db in displayDbList" :key="db.key" :label="db.label" :value="db" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dbList.length" label="数据库名称正则">
          <el-input v-model="form.source.databasePattern" placeholder="示例：^tenant_" style="width: 240px" />
          <el-button size="small" style="margin-left: 8px" @click="applyDbPattern">匹配</el-button>
        </el-form-item>
        <el-form-item label="数据表">
          <el-select v-model="form.source.tables" value-key="key" multiple filterable clearable placeholder="选择表" style="width: 640px">
            <el-option v-for="t in displayTableList" :key="t.key" :label="t.label" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据表名称正则">
          <el-input v-model="form.source.tablePattern" placeholder="示例：^order_|_log$" style="width: 240px" />
          <el-button size="small" style="margin-left: 8px" @click="applyTablePattern">匹配</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>
        <span>目标</span>
      </template>
      <el-form :inline="true" :model="form.target" label-width="100px">
        <el-form-item label="数据源">
          <el-select v-model="form.target.dataSourceId" placeholder="选择数据源" style="width: 280px">
            <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="targetDbList.length" label="数据库">
          <el-select v-model="form.target.databaseName" filterable clearable placeholder="选择数据库" style="width: 240px">
            <el-option v-for="db in targetDbList" :key="db" :label="db" :value="db" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据表">
          <el-select v-model="form.target.tableName" filterable allow-create default-first-option clearable placeholder="选择或输入表名" style="width: 280px">
            <el-option v-for="t in targetTableList" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
      </el-form>
      <div v-if="form.target.dataSourceId && form.source.dataSourceIds.length && form.source.dataSourceIds.includes(form.target.dataSourceId)" style="color: #f56c6c; margin-left: 16px">目标数据源不能与来源数据源一致</div>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>
        <span>字段映射</span>
      </template>
      <div style="margin-bottom: 8px">
        <el-checkbox v-model="form.defaultMapping" @change="applyDefaultMapping">默认同名映射</el-checkbox>
        <el-button size="small" style="margin-left: 12px" @click="addMappingRow">新增映射</el-button>
      </div>
      <el-table :data="form.mappings" border style="width: 100%">
        <el-table-column prop="targetField" label="目标字段">
          <template #default="scope">
            <el-input v-model="scope.row.targetField" placeholder="输入目标字段" style="width: 220px" />
          </template>
        </el-table-column>
        <el-table-column prop="sourceExpr" label="来源字段/表达式">
          <template #default="scope">
            <el-select v-model="scope.row.sourceExpr" filterable allow-create default-first-option placeholder="选择或输入" style="width: 260px">
              <el-option v-for="c in unionSourceColumns" :key="c" :label="c" :value="c" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button link type="danger" @click="removeMapping(scope.$index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>
        <span>同步配置</span>
      </template>
      <el-form :model="form" label-width="120px">
        <el-form-item label="where条件">
          <el-input v-model="form.where" type="textarea" :rows="2" placeholder="示例：status = 1" />
        </el-form-item>
        <el-form-item label="同步方式">
          <el-radio-group v-model="form.mode.type">
            <el-radio label="full">全量</el-radio>
            <el-radio label="incremental">增量</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.mode.type==='incremental'" label="增量字段">
          <el-select v-model="form.mode.incrementField" filterable allow-create placeholder="选择或输入增量字段" style="width: 240px">
            <el-option v-for="c in sourceColumns" :key="c.name || c.columnName" :label="c.name || c.columnName" :value="c.name || c.columnName" />
          </el-select>
          <el-select v-model="form.mode.incrementType" style="width: 180px; margin-left: 12px">
            <el-option label="自增ID" value="id" />
            <el-option label="时间戳" value="timestamp" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { listDatasource, listDatabases, listTables, listColumns } from '@/api/datasource'
const { proxy } = getCurrentInstance()

const dsList = ref([])
const dbList = ref([])
const displayDbList = ref([])
const tableList = ref([])
const displayTableList = ref([])
const sourceColumnsMap = reactive({})
const unionSourceColumns = ref([])
const targetDbList = ref([])
const targetTableList = ref([])

const form = reactive({
  source: { dataSourceIds: [], databases: [], databasePattern: '', tables: [], tablePattern: '' },
  target: { dataSourceId: undefined, databaseName: undefined, tableName: undefined },
  defaultMapping: false,
  mappings: [],
  where: '',
  mode: { type: 'full', incrementField: '', incrementType: 'id' }
})

function getForm() { return JSON.parse(JSON.stringify(form)) }
defineExpose({ getForm })

function loadDs() {
  listDatasource({ pageNum: 1, pageSize: 100 }).then(res => { dsList.value = res.rows || [] })
}

function applyDbPattern() {
  const p = (form.source.databasePattern || '').trim()
  if (!p) { displayDbList.value = [...dbList.value]; return }
  try {
    const re = new RegExp(p)
    displayDbList.value = dbList.value.filter(d => re.test(String(d.databaseName)))
  } catch { displayDbList.value = [...dbList.value] }
}

function applyTablePattern() {
  const p = (form.source.tablePattern || '').trim()
  if (!p) { displayTableList.value = [...tableList.value]; return }
  try {
    const re = new RegExp(p)
    displayTableList.value = tableList.value.filter(t => re.test(String(t.tableName)))
  } catch { displayTableList.value = [...tableList.value] }
}

function addMappingRow() { form.mappings.push({ targetField: '', sourceExpr: '' }) }
function removeMapping(i) { form.mappings.splice(i, 1) }

function applyDefaultMapping() {
  if (!form.defaultMapping) return
  if (!unionSourceColumns.value.length) return
  form.mappings = unionSourceColumns.value.map(n => ({ targetField: n, sourceExpr: n }))
}

watch(() => form.source.dataSourceIds.slice().join(','), () => {
  dbList.value = []
  displayDbList.value = []
  form.source.databases = []
  tableList.value = []
  displayTableList.value = []
  form.source.tables = []
  unionSourceColumns.value = []
  Object.keys(sourceColumnsMap).forEach(k => delete sourceColumnsMap[k])
  const ids = form.source.dataSourceIds
  if (!ids.length) return
  const tasks = ids.map(id => listDatabases({ dataSourceId: id }))
  Promise.all(tasks).then(resList => {
    const aggregates = []
    let hasDb = false
    resList.forEach((res, idx) => {
      const dsId = ids[idx]
      const ds = dsList.value.find(d => d.dataSourceId === dsId)
      const dbs = Array.isArray(res.data) ? res.data : []
      if (dbs.length) hasDb = true
      dbs.forEach(db => {
        const key = String(dsId) + ':' + String(db)
        aggregates.push({ key, dataSourceId: dsId, dataSourceName: ds ? ds.dataSourceName : String(dsId), databaseName: String(db), label: (ds ? ds.dataSourceName : dsId) + ' / ' + String(db) })
      })
    })
    dbList.value = aggregates
    displayDbList.value = aggregates
    if (!hasDb) {
      const tableTasks = ids.map(id => listTables({ dataSourceId: id }))
      Promise.all(tableTasks).then(tResList => {
        const tables = []
        tResList.forEach((res, idx) => {
          const dsId = ids[idx]
          const ds = dsList.value.find(d => d.dataSourceId === dsId)
          (res.rows || []).forEach(r => {
            const name = r.tableName || r
            const key = String(dsId) + '::' + String(name)
            tables.push({ key, dataSourceId: dsId, dataSourceName: ds ? ds.dataSourceName : String(dsId), tableName: String(name), label: (ds ? ds.dataSourceName : dsId) + ' / ' + String(name) })
          })
        })
        tableList.value = tables
        displayTableList.value = tables
      })
    }
  })
})

watch(() => form.source.databases.map(d => d.key).join(','), () => {
  tableList.value = []
  displayTableList.value = []
  form.source.tables = []
  unionSourceColumns.value = []
  Object.keys(sourceColumnsMap).forEach(k => delete sourceColumnsMap[k])
  const dbs = form.source.databases
  if (!dbs.length) return
  const tasks = dbs.map(d => listTables({ dataSourceId: d.dataSourceId, databaseName: d.databaseName }))
  Promise.all(tasks).then(resList => {
    const tables = []
    resList.forEach((res, idx) => {
      const d = dbs[idx]
      (res.rows || []).forEach(r => {
        const name = r.tableName || r
        const key = String(d.dataSourceId) + ':' + String(d.databaseName) + ':' + String(name)
        tables.push({ key, dataSourceId: d.dataSourceId, dataSourceName: d.dataSourceName, databaseName: d.databaseName, tableName: String(name), label: d.dataSourceName + ' / ' + d.databaseName + ' / ' + String(name) })
      })
    })
    tableList.value = tables
    displayTableList.value = tables
  })
})

watch(() => form.source.tables.map(t => t.key).join(','), () => {
  unionSourceColumns.value = []
  Object.keys(sourceColumnsMap).forEach(k => delete sourceColumnsMap[k])
  const first = form.source.tables[0]
  if (!first) return
  const params = { dataSourceId: first.dataSourceId, tableName: first.tableName }
  if (first.databaseName) params.databaseName = first.databaseName
  listColumns(params).then(res => {
    const cols = (res.rows || []).map(c => c.name || c.columnName)
    unionSourceColumns.value = Array.from(new Set(cols))
    applyDefaultMapping()
  })
})

watch(() => form.target.dataSourceId, v => {
  targetDbList.value = []
  form.target.databaseName = undefined
  targetTableList.value = []
  form.target.tableName = undefined
  if (!v) return
  listDatabases({ dataSourceId: v }).then(res => {
    const dbs = res.data
    if (Array.isArray(dbs)) targetDbList.value = dbs
  })
})

watch(() => form.target.databaseName, v => {
  targetTableList.value = []
  form.target.tableName = undefined
  const dsId = form.target.dataSourceId
  if (!dsId) return
  const params = { dataSourceId: dsId }
  if (v) params.databaseName = v
  listTables(params).then(res => {
    targetTableList.value = (res.rows || []).map(r => r.tableName || r)
  })
})

onMounted(() => { loadDs() })
</script>

<style scoped>
</style>

