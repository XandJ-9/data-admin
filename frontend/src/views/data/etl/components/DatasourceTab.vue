<template>
  <el-form :model="form" label-width="120px" :disabled="!isEdit">
    <el-row :gutter="20">
      <!-- 源端配置 -->
      <el-col :span="12">
        <el-divider content-position="left">源端配置</el-divider>
        <el-form-item label="源数据源">
          <el-select
            v-model="form.sourceDatasourceId"
            placeholder="请选择源数据源"
            filterable
            style="width: 100%"
            @change="handleSourceDatasourceChange"
          >
            <el-option
              v-for="ds in datasourceList"
              :key="ds.dataSourceId"
              :label="ds.dataSourceName"
              :value="ds.dataSourceId"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="sourceDatabases.length > 0" label="源数据库">
          <el-select
            v-model="form.sourceDatabaseName"
            placeholder="请选择数据库"
            filterable
            style="width: 100%"
            @change="handleSourceDatabaseChange"
          >
            <el-option v-for="db in sourceDatabases" :key="db" :label="db" :value="db" />
          </el-select>
        </el-form-item>
        <el-form-item label="源表">
          <el-select
            v-model="form.sourceTableName"
            placeholder="请选择源表"
            filterable
            style="width: 100%"
            :loading="loadingTables"
            @change="handleSourceTableChange"
          >
            <el-option
              v-for="t in sourceTables"
              :key="t.tableName"
              :label="t.tableName"
              :value="t.tableName"
            >
              <span>{{ t.tableName }}</span>
              <span v-if="t.comment" style="color: #999; margin-left: 8px; font-size: 12px">{{ t.comment }}</span>
            </el-option>
          </el-select>
        </el-form-item>
      </el-col>

      <!-- 目标端配置 -->
      <el-col :span="12">
        <el-divider content-position="left">目标端配置</el-divider>
        <el-form-item label="目标数据源">
          <el-select
            v-model="form.targetDatasourceId"
            placeholder="请选择目标数据源"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="ds in datasourceList"
              :key="ds.dataSourceId"
              :label="ds.dataSourceName"
              :value="ds.dataSourceId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标表">
          <el-input v-model="form.targetTable" placeholder="请输入目标表名" />
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 源表字段预览 -->
    <el-divider v-if="sourceColumns.length > 0" content-position="left">
      源表字段预览（{{ sourceColumns.length }} 个字段）
    </el-divider>
    <el-table
      v-if="sourceColumns.length > 0"
      :data="sourceColumns"
      border
      stripe
      max-height="300"
      size="small"
      v-loading="loadingColumns"
    >
      <el-table-column prop="name" label="字段名" min-width="150" />
      <el-table-column prop="type" label="数据类型" width="150" />
      <el-table-column prop="primary" label="主键" width="70" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.primary" type="success" size="small">是</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="notnull" label="非空" width="70" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.notnull" type="warning" size="small">是</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="comment" label="注释" min-width="200" show-overflow-tooltip />
    </el-table>
  </el-form>
</template>

<script setup>
import { ref, watch } from 'vue'
import { listDatabases, listTables, listColumns } from '@/api/data/asset'
import { ElMessage } from 'element-plus'

const props = defineProps({
  form: { type: Object, required: true },
  isEdit: { type: Boolean, default: false },
  datasourceList: { type: Array, default: () => [] }
})

const emit = defineEmits(['columns-loaded'])

const sourceDatabases = ref([])
const sourceTables = ref([])
const sourceColumns = ref([])
const loadingTables = ref(false)
const loadingColumns = ref(false)

// 选择源数据源后加载数据库列表
async function handleSourceDatasourceChange(dsId) {
  // 清空下游状态
  sourceDatabases.value = []
  sourceTables.value = []
  sourceColumns.value = []
  props.form.sourceDatabaseName = ''
  props.form.sourceTableName = ''
  emit('columns-loaded', [])

  if (!dsId) return

  try {
    const res = await listDatabases({ dataSourceId: dsId })
    const dbs = res.data
    if (Array.isArray(dbs) && dbs.length > 0) {
      sourceDatabases.value = dbs
    } else {
      // 单库类型（PostgreSQL/SQLite），直接加载表
      await loadSourceTables(dsId, '')
    }
  } catch (error) {
    // 降级：直接加载表
    await loadSourceTables(dsId, '')
  }
}

// 选择数据库后加载表列表
async function handleSourceDatabaseChange(dbName) {
  sourceTables.value = []
  sourceColumns.value = []
  props.form.sourceTableName = ''
  emit('columns-loaded', [])

  if (!dbName) return
  await loadSourceTables(props.form.sourceDatasourceId, dbName)
}

async function loadSourceTables(dsId, dbName) {
  loadingTables.value = true
  try {
    const params = { dataSourceId: dsId }
    if (dbName) params.databaseName = dbName
    const res = await listTables(params)
    sourceTables.value = res.rows || []
  } catch (error) {
    ElMessage.error('加载表列表失败: ' + (error.message || error))
  } finally {
    loadingTables.value = false
  }
}

// 选择表后加载字段列表并自动填充目标表名
async function handleSourceTableChange(tableName) {
  sourceColumns.value = []
  emit('columns-loaded', [])

  if (!tableName) return

  // 自动填充目标表名
  const dbPart = props.form.sourceDatabaseName || ''
  props.form.targetTable = dbPart ? `stg_${dbPart}_${tableName}` : `stg_${tableName}`

  loadingColumns.value = true
  try {
    const params = {
      dataSourceId: props.form.sourceDatasourceId,
      tableName
    }
    if (props.form.sourceDatabaseName) {
      params.databaseName = props.form.sourceDatabaseName
    }
    const res = await listColumns(params)
    sourceColumns.value = res.rows || []
    emit('columns-loaded', sourceColumns.value)
  } catch (error) {
    ElMessage.error('加载字段列表失败: ' + (error.message || error))
  } finally {
    loadingColumns.value = false
  }
}

// 编辑已有任务时，如果已有源数据源和源表，需要重新加载上下文
watch(
  () => [props.form.sourceDatasourceId, props.form.sourceTableName],
  async ([dsId, tableName]) => {
    if (dsId && tableName && sourceColumns.value.length === 0) {
      // 加载数据库列表
      try {
        const res = await listDatabases({ dataSourceId: dsId })
        const dbs = res.data
        if (Array.isArray(dbs) && dbs.length > 0) {
          sourceDatabases.value = dbs
        }
      } catch { /* ignore */ }

      // 加载表列表
      await loadSourceTables(dsId, props.form.sourceDatabaseName || '')

      // 加载字段
      loadingColumns.value = true
      try {
        const params = { dataSourceId: dsId, tableName }
        if (props.form.sourceDatabaseName) {
          params.databaseName = props.form.sourceDatabaseName
        }
        const res = await listColumns(params)
        sourceColumns.value = res.rows || []
        emit('columns-loaded', sourceColumns.value)
      } catch { /* ignore */ } finally {
        loadingColumns.value = false
      }
    }
  },
  { immediate: true }
)
</script>
