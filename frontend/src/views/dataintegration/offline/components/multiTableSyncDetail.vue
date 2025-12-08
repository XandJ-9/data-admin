<template>
  <div>
    <el-card>
      <template #header>
        <span>来源</span>
      </template>
      <el-form :inline="true" :model="form.source" label-width="100px">
        <el-form-item label="数据源">
          <el-select v-model="form.source.dataSourceId" placeholder="选择数据源" style="width: 280px">
            <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dbList.length" label="数据库">
          <el-select v-model="form.source.databaseNames" multiple filterable clearable placeholder="选择数据库" style="width: 360px">
            <el-option v-for="db in displayDbList" :key="db" :label="db" :value="db" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dbList.length" label="数据库名称正则">
          <el-input v-model="form.source.databasePattern" placeholder="示例：^tenant_" style="width: 240px" />
          <el-button size="small" style="margin-left: 8px" @click="applyDbPattern">匹配</el-button>
        </el-form-item>
        <el-form-item label="数据表">
          <el-select v-model="form.source.tableNames" multiple filterable clearable placeholder="选择表" style="width: 480px">
            <el-option v-for="t in displayTableList" :key="t" :label="t" :value="t" />
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
      <div v-if="form.target.dataSourceId && form.source.dataSourceId && form.target.dataSourceId === form.source.dataSourceId" style="color: #f56c6c; margin-left: 16px">目标数据源不能与来源数据源一致</div>
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
        <el-form-item label="调度策略">
          <el-radio-group v-model="form.schedule.type">
            <el-radio label="manual">手动</el-radio>
            <el-radio label="cron">定时</el-radio>
          </el-radio-group>
          <el-input v-if="form.schedule.type==='cron'" v-model="form.schedule.cronExpr" placeholder="cron表达式" style="width: 240px; margin-left: 12px" />
        </el-form-item>
        <el-form-item label="同步方式">
          <el-radio-group v-model="form.mode.type">
            <el-radio label="full">全量</el-radio>
            <el-radio label="incremental">增量</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.mode.type==='incremental'" label="增量字段">
          <el-select v-model="form.mode.incrementField" filterable allow-create placeholder="选择或输入增量字段" style="width: 240px">
            <el-option v-for="c in unionSourceColumns" :key="c" :label="c" :value="c" />
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
  source: { dataSourceId: undefined, databaseNames: [], databasePattern: '', tableNames: [], tablePattern: '' },
  target: { dataSourceId: undefined, databaseName: undefined, tableName: undefined },
  defaultMapping: false,
  mappings: [],
  where: '',
  schedule: { type: 'manual', cronExpr: '' },
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
    displayDbList.value = dbList.value.filter(d => re.test(String(d)))
  } catch { displayDbList.value = [...dbList.value] }
}

function applyTablePattern() {
  const p = (form.source.tablePattern || '').trim()
  if (!p) { displayTableList.value = [...tableList.value]; return }
  try {
    const re = new RegExp(p)
    displayTableList.value = tableList.value.filter(t => re.test(String(t)))
  } catch { displayTableList.value = [...tableList.value] }
}

function addMappingRow() { form.mappings.push({ targetField: '', sourceExpr: '' }) }
function removeMapping(i) { form.mappings.splice(i, 1) }

function applyDefaultMapping() {
  if (!form.defaultMapping) return
  if (!unionSourceColumns.value.length) return
  form.mappings = unionSourceColumns.value.map(n => ({ targetField: n, sourceExpr: n }))
}

watch(() => form.source.dataSourceId, v => {
  dbList.value = []
  displayDbList.value = []
  form.source.databaseNames = []
  tableList.value = []
  displayTableList.value = []
  form.source.tableNames = []
  unionSourceColumns.value = []
  Object.keys(sourceColumnsMap).forEach(k => delete sourceColumnsMap[k])
  if (!v) return
  listDatabases({ dataSourceId: v }).then(res => {
    const dbs = res.data
    if (Array.isArray(dbs)) { dbList.value = dbs; displayDbList.value = dbs }
  })
  if (dbList.length) return
  listTables({ dataSourceId: v }).then(res => {
    const tableNames = (res.rows || []).map(t => t.tableName || t)
    if (Array.isArray(tableNames)) {
      tableList.value = tableNames;
      displayTableList.value = tableNames
    }
  })
})

watch(() => form.source.databaseNames.slice().join(','), () => {
  tableList.value = []
  displayTableList.value = []
  form.source.tableNames = []
  unionSourceColumns.value = []
  Object.keys(sourceColumnsMap).forEach(k => delete sourceColumnsMap[k])
  const dsId = form.source.dataSourceId
  if (!dsId || !form.source.databaseNames.length) return
  const promises = form.source.databaseNames.map(db => listTables({ dataSourceId: dsId, databaseName: db }))
  Promise.all(promises).then(list => {
    const names = []
    list.forEach(res => {
      (res.rows || []).forEach(r => names.push(r.tableName))
    })
    const uniq = Array.from(new Set(names))
    tableList.value = uniq
    displayTableList.value = uniq
  })
})

watch(() => form.source.tableNames.slice().join(','), () => {
  unionSourceColumns.value = []
  Object.keys(sourceColumnsMap).forEach(k => delete sourceColumnsMap[k])
  const dsId = form.source.dataSourceId
  if (!dsId || !form.source.tableNames.length) return
  const firstDb = form.source.databaseNames[0]
  const firstTable = form.source.tableNames[0]
  if (!firstTable) return
  const params = { dataSourceId: dsId, tableName: firstTable }
  if (firstDb) params.databaseName = firstDb
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

