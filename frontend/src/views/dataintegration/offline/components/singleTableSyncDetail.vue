<template>
  <div>
    <el-card>
      <template #header>
        <span>基本信息</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="12">
            <el-card>
            <el-form :inline="true" :model="form.source" label-width="100px">
                <el-form-item label="数据源">
                <el-select v-model="form.source.dataSourceId" placeholder="选择数据源" style="width: 280px">
                    <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
                </el-select>
                </el-form-item>
                <el-form-item v-if="sourceDbList.length" label="数据库">
                <el-select v-model="form.source.databaseName" filterable clearable placeholder="选择数据库" style="width: 240px">
                    <el-option v-for="db in sourceDbList" :key="db" :label="db" :value="db" />
                </el-select>
                </el-form-item>
                <el-form-item label="数据表">
                <el-select v-model="form.source.tableName" filterable clearable placeholder="选择表" style="width: 280px">
                    <el-option v-for="t in sourceTableList" :key="t.tableName || t" :label="t.tableName || t" :value="t.tableName || t" />
                </el-select>
                </el-form-item>
            </el-form>
            </el-card>
        </el-col>
        <el-col :span="12">
            <el-card>
                <el-form :inline="true" :model="form.target" label-width="100px">
                    <el-row>
                    <el-form-item label="数据源">
                    <el-select v-model="form.target.dataSourceId" placeholder="选择数据源" style="width: 280px">
                        <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
                    </el-select>
                    </el-form-item>
                    </el-row>
                    <el-row>
                    <el-form-item v-if="targetDbList.length" label="数据库">
                    <el-select v-model="form.target.databaseName" filterable clearable placeholder="选择数据库" style="width: 240px">
                        <el-option v-for="db in targetDbList" :key="db" :label="db" :value="db" />
                    </el-select>
                    </el-form-item>
                    </el-row>
                    <el-row>
                    <el-form-item label="数据表">
                    <el-select v-model="form.target.tableName" allow-create default-first-option filterable clearable placeholder="选择或输入新表名" style="width: 280px">
                        <el-option v-for="t in targetTableList" :key="t.tableName || t" :label="t.tableName || t" :value="t.tableName || t" />
                    </el-select>
                    <!-- <el-input v-else v-model="form.target.tableName" placeholder="输入表名" style="width: 280px" />
                    <el-checkbox v-model="form.target.isNewTable" style="margin-right: 8px">创建新表</el-checkbox> -->
                    </el-form-item>
                    </el-row>

                </el-form>
            </el-card>
        </el-col>
        <div v-if="form.target.dataSourceId && form.source.dataSourceId && form.target.dataSourceId === form.source.dataSourceId" style="color: #f56c6c; margin-left: 16px">目标数据源不能与来源数据源一致</div>
      </el-row>

    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>
        <span>字段映射</span>
      </template>
      <div style="margin-bottom: 8px">
        <!-- <el-button type="primary" @click="applyDefaultMapping">默认同名映射</el-button> -->
        <el-checkbox v-model="form.defaultMapping" @change="applyDefaultMapping">默认同名映射</el-checkbox>
        <el-button size="small" style="margin-left: 12px" @click="addMappingRow">新增映射</el-button>
      </div>
      <el-table :data="form.mappings" border style="width: 100%">
        <el-table-column prop="targetField" label="目标字段">
          <template #header="scope">
            <span>目标字段{{form.mappings.length}}/{{targetColumns.length}}</span>
          </template>
          <template #default="scope">
            <el-select v-model="scope.row.targetField" filterable allow-create default-first-option placeholder="选择目标字段" style="width: 220px">
              <el-option v-for="c in targetColumns" :key="c.name || c.columnName" :label="c.name || c.columnName" :value="c.name || c.columnName" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="sourceExpr" label="来源字段/表达式">
          <template #default="scope">
            <el-select v-model="scope.row.sourceExpr" filterable allow-create default-first-option placeholder="选择或输入" style="width: 260px">
              <el-option v-for="c in sourceColumns" :key="c.name || c.columnName" :label="c.name || c.columnName" :value="c.name || c.columnName" />
            </el-select>
            <!-- <el-input v-else v-model="scope.row.sourceExpr" placeholder="请输入" style="width: 260px" /> -->
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
import { ElMessage } from 'element-plus'
import { listDatasource, listDatabases, listTables, listColumns } from '@/api/datasource'
const { proxy } = getCurrentInstance()

const dsList = ref([])
const sourceDbList = ref([])
const targetDbList = ref([])
const sourceTableList = ref([])
const targetTableList = ref([])
const sourceColumns = ref([])
const targetColumns = ref([])

const form = reactive({
  source: { dataSourceId: undefined, databaseName: undefined, tableName: undefined },
  target: { dataSourceId: undefined, databaseName: undefined, tableName: undefined },
  defaultMapping: true,
  mappings: [],
  where: '',
  mode: { type: 'full', incrementField: '', incrementType: 'id' }
})

function getForm() {
  return JSON.parse(JSON.stringify(form))
}
defineExpose({ getForm })

function loadDs() {
  listDatasource({ pageNum: 1, pageSize: 100 }).then(res => {
    dsList.value = res.rows || []
  })
}

function addMappingRow() {
    if (form.mappings.length >= targetColumns.value.length) {
        ElMessage.warning('未指定目标表或超过目标表字段个数，最多只能添加' + targetColumns.value.length + '个映射')
        return
    }
  form.mappings.push({ targetField: '', sourceExpr: '' })
}

function removeMapping(i) {
  form.mappings.splice(i, 1)
}

function applyDefaultMapping() {
  if (!form.defaultMapping) return
  if (!targetColumns.value.length || !sourceColumns.value.length) return
  const srcNames = new Set((sourceColumns.value || []).map(c => c.name || c.columnName))
  const tgtNames = (targetColumns.value || []).map(c => c.name || c.columnName)
  form.mappings = tgtNames.filter(n => srcNames.has(n)).map(n => ({ targetField: n ,sourceExpr: n}))
}


watch(() => form.source.dataSourceId, v => {
  sourceDbList.value = []
  form.source.databaseName = undefined
  sourceTableList.value = []
  form.source.tableName = undefined
  sourceColumns.value = []
  if (!v) return
  listDatabases({ dataSourceId: v }).then(res => {
    const dbs = res.data
    if (Array.isArray(dbs)) sourceDbList.value = dbs
  })
  if (sourceDbList.value.length) return
  listTables({ dataSourceId: v}).then(res => {
    sourceTableList.value = res.rows || []
  })
})

watch(() => form.source.databaseName, v => {
  sourceTableList.value = []
  form.source.tableName = undefined
  sourceColumns.value = []
  if (!form.source.dataSourceId) return
  const params = { dataSourceId: form.source.dataSourceId }
  if (v) params.databaseName = v
  listTables(params).then(res => {
    sourceTableList.value = res.rows || []
  })
})

watch(() => form.source.tableName, v => {
  sourceColumns.value = []
  if (!form.source.dataSourceId || !v) return
  const params = { dataSourceId: form.source.dataSourceId, tableName: v }
  if (form.source.databaseName) params.databaseName = form.source.databaseName
  listColumns(params).then(res => {
    sourceColumns.value = res.rows || []
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
    const dbs = res.data
    if (Array.isArray(dbs)) targetDbList.value = dbs
  })
  if (targetDbList.value.length) return
  listTables({ dataSourceId: v }).then(res => {
    targetTableList.value = res.rows || []
  })
})

watch(() => form.target.databaseName, v => {
  targetTableList.value = []
  form.target.tableName = undefined
  targetColumns.value = []
  if (!form.target.dataSourceId) return
  const params = { dataSourceId: form.target.dataSourceId }
  if (v) params.databaseName = v
  listTables(params).then(res => {
    targetTableList.value = res.rows || []
  })
})

watch(() => form.target.tableName, v => {
  targetColumns.value = []
  if (!form.target.dataSourceId || !v) return
  const params = { dataSourceId: form.target.dataSourceId, tableName: v }
  if (form.target.databaseName) params.databaseName = form.target.databaseName
  listColumns(params).then(res => {
    targetColumns.value = res.rows || []
    applyDefaultMapping()
  })
})

onMounted(() => {
  loadDs()
})
</script>

<style scoped>
</style>



