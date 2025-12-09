<template>
  <div>
    <el-card>
      <template #header>
        <span>基本信息</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>来源</span>
            </template>
            <el-form :inline="true" :model="form.source" label-width="100px" label-position="left">
              <el-row>
                <el-form-item label="数据源">
                  <el-select v-model="form.source.dataSourceIds" style="width: 200px" multiple filterable clearable
                    collapse-tags placeholder="选择数据源">
                    <el-option v-for="ds in dsList" :key="ds.dataSourceId"
                      :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
                  </el-select>
                </el-form-item>
                <div v-if="sourceTypeError" style="color: #f56c6c; margin: 4px 0 8px 16px">来源数据源类型不一致（{{ sourceTypeText
                  }}），不允许进行同步</div>
              </el-row>
              <el-row>
                <el-form-item v-if="dbList.length" label="数据库">
                  <el-select v-model="form.source.databases" value-key="key" style="width: 200px" multiple filterable
                    clearable collapse-tags placeholder="选择数据库">
                    <el-option v-for="db in displayDbList" :key="db.key" :label="db.label" :value="db" />
                  </el-select>
                </el-form-item>
                <el-form-item v-if="dbList.length" label="库名正则">
                  <el-input v-model="form.source.databasePattern" style="width: 200px" placeholder="示例：^tenant_" />
                  <el-button size="small" style="margin-left: 8px" @click="applyDbPattern">匹配</el-button>
                </el-form-item>
              </el-row>
              <el-row>
                <el-form-item label="数据表">
                  <el-select v-model="form.source.tables" value-key="key" style="width: 200px" multiple filterable
                    clearable collapse-tags placeholder="选择表">
                    <el-option v-for="t in displayTableList" :key="t.key" :label="t.label" :value="t" />
                  </el-select>
                </el-form-item>
                <el-form-item label="表名正则">
                  <el-input v-model="form.source.tablePattern" style="width: 200px" placeholder="示例：^order_|_log$" />
                  <el-button size="small" style="margin-left: 8px" @click="applyTablePattern">匹配</el-button>
                </el-form-item>
              </el-row>
            </el-form>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>目标</span>
            </template>
            <el-form :inline="true" :model="form.target" label-width="100px">
              <el-row>
                <el-form-item label="数据源">
                  <el-select v-model="form.target.dataSourceId" placeholder="选择数据源" style="width: 200px">
                    <el-option v-for="ds in dsList" :key="ds.dataSourceId"
                      :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
                  </el-select>
                </el-form-item>
              </el-row>
              <el-row>
                <el-form-item v-if="targetDbList.length" label="数据库">
                  <el-select v-model="form.target.databaseName" style="width: 200px" filterable clearable
                    placeholder="选择数据库">
                    <el-option v-for="db in targetDbList" :key="db" :label="db" :value="db" />
                  </el-select>
                </el-form-item>
              </el-row>
              <el-row>
                <el-form-item label="数据表">
                  <el-select v-model="form.target.tableName" style="width: 200px" filterable allow-create
                    default-first-option clearable placeholder="选择或输入表名">
                    <el-option v-for="t in targetTableList" :key="t" :label="t" :value="t" />
                  </el-select>
                </el-form-item>
              </el-row>
            </el-form>
          </el-card>
        </el-col>
        <div
          v-if="form.target.dataSourceId && form.source.dataSourceIds.length && form.source.dataSourceIds.includes(form.target.dataSourceId)"
          style="color: #f56c6c; margin-left: 16px">目标数据源不能与来源数据源一致</div>
      </el-row>
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
            <el-select v-model="scope.row.targetField" filterable allow-create default-first-option placeholder="选择目标字段"
              style="width: 220px">
              <el-option v-for="c in targetColumns" :key="c" :label="c" :value="c" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="sourceExpr" label="来源字段/表达式">
          <template #default="scope">
            <el-select v-model="scope.row.sourceExpr" filterable allow-create default-first-option placeholder="选择或输入"
              style="width: 260px">
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
        <el-form-item v-if="form.mode.type === 'incremental'" label="增量字段">
          <el-select v-model="form.mode.incrementField" filterable allow-create placeholder="选择或输入增量字段"
            style="width: 240px">
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
const targetColumns = ref([])
const sourceTypeError = ref(false)
const sourceTypeText = ref('')

const form = reactive({
  source: { dataSourceIds: [], databases: [], databasePattern: '', tables: [], tablePattern: '' },
  target: { dataSourceId: undefined, databaseName: undefined, tableName: undefined },
  defaultMapping: false,
  mappings: [],
  where: '',
  mode: { type: 'full', incrementField: '', incrementType: 'id' }
})

function getForm() { return JSON.parse(JSON.stringify(form)) }

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
  const src = unionSourceColumns.value || []
  const tgt = targetColumns.value || []
  if (tgt.length && src.length) {
    const srcSet = new Set(src)
    form.mappings = tgt.filter(n => srcSet.has(n)).map(n => ({ targetField: n, sourceExpr: n }))
    return
  }
  if (src.length) {
    form.mappings = src.map(n => ({ targetField: n, sourceExpr: n }))
  }
}

watch(() => form.source.dataSourceIds.slice().join(','), () => {
  // 校验来源数据源类型一致性
  const ids = form.source.dataSourceIds
  const types = Array.from(new Set(ids.map(id => {
    const ds = dsList.value.find(d => d.dataSourceId === id)
    return ds ? ds.dbType : 'UNKNOWN'
  })))
  sourceTypeError.value = types.length > 1
  sourceTypeText.value = types.join(', ')

  dbList.value = []
  displayDbList.value = []
  form.source.databases = []
  tableList.value = []
  displayTableList.value = []
  form.source.tables = []
  unionSourceColumns.value = []
  Object.keys(sourceColumnsMap).forEach(k => delete sourceColumnsMap[k])
  if (!ids.length) return
  const tasks = ids.map(id => listDatabases({ dataSourceId: id }))
  Promise.all(tasks).then(resList => {
    const aggregates = []
    let hasDb = false
    resList.forEach((res, idx) => {
      const dsId = ids[idx]
      const ds = dsList.value.find(d => d.dataSourceId === dsId)
      const dbArr = Array.isArray(res.data) ? res.data : []
      if (dbArr.length) hasDb = true
      dbArr.forEach(db => {
        const key = String(dsId) + ':' + String(db)
        aggregates.push({ key, dataSourceId: dsId, dataSourceName: ds ? ds.dataSourceName : String(dsId), databaseName: String(db), label: (ds ? ds.dataSourceName : dsId) + ' / ' + String(db) })
      })
    })
    dbList.value = aggregates
    displayDbList.value = aggregates
    if (!hasDb) {
      const tableTasks = ids.map(id => listTables({ dataSourceId: id }).then(res => ({ res, dsId: id })))
      Promise.all(tableTasks).then(results => {
        const tables = []
        results.forEach(({ res, dsId }) => {
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
  const selectedDbs = Array.isArray(form.source.databases) ? form.source.databases : []
  if (selectedDbs.length === 0) return
  const tasks = selectedDbs.map(d => listTables({ dataSourceId: d.dataSourceId, databaseName: d.databaseName }).then(res => ({ res, db: d })))
  Promise.all(tasks).then(results => {
    const tables = []
    results.forEach(({ res, db }) => {
      (res.rows || []).forEach(r => {
        const name = r.tableName || r
        const key = String(db.dataSourceId) + ':' + String(db.databaseName) + ':' + String(name)
        tables.push({ key, dataSourceId: db.dataSourceId, dataSourceName: db.dataSourceName, databaseName: db.databaseName, tableName: String(name), label: db.dataSourceName + ' / ' + db.databaseName + ' / ' + String(name) })
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
  targetColumns.value = []
  if (!v) return
  listDatabases({ dataSourceId: v }).then(res => {
    const dbArr = Array.isArray(res.data) ? res.data : []
    if (dbArr.length) targetDbList.value = dbArr
    if (dbArr.length === 0) {
      // 无数据库时直接加载表列表
      listTables({ dataSourceId: v }).then(res2 => {
        targetTableList.value = (res2.rows || []).map(r => r.tableName || r)
      })
    }
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

watch(() => form.target.tableName, v => {
  targetColumns.value = []
  const dsId = form.target.dataSourceId
  if (!dsId || !v) return
  const params = { dataSourceId: dsId, tableName: v }
  if (form.target.databaseName) params.databaseName = form.target.databaseName
  listColumns(params).then(res => {
    targetColumns.value = (res.rows || []).map(c => c.name || c.columnName)
    applyDefaultMapping()
  })
})

onMounted(() => { loadDs() })

function isValid() {
  const targetSameAsSource = form.target.dataSourceId && form.source.dataSourceIds.includes(form.target.dataSourceId)
  return !sourceTypeError.value && !targetSameAsSource
}

defineExpose({ getForm, isValid })
</script>

<style scoped></style>
