<template>
  <div class="target-step">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="140px"
      label-position="right"
    >
      <el-alert
        title="目标端配置"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 24px"
      >
        配置数据写入目标，包括目标数据源、表名和写入方式
      </el-alert>

      <!-- 目标数据源选择 -->
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="目标数据源" prop="targetDatasourceId">
            <el-select
              v-model="formData.targetDatasourceId"
              placeholder="请选择目标数据源"
              style="width: 100%"
              filterable
              @change="handleDatasourceChange"
            >
              <el-option-group
                v-for="group in groupedDatasources"
                :key="group.label"
                :label="group.label"
              >
                <el-option
                  v-for="item in group.options"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                >
                  <div class="datasource-option">
                    <span class="ds-name">{{ item.name }}</span>
                    <el-tag size="small" :type="getDsTypeTag(item.dsType)">
                      {{ getDsTypeLabel(item.dsType) }}
                    </el-tag>
                  </div>
                </el-option>
              </el-option-group>
            </el-select>
            <div class="form-tip">选择数据写入的目标数据源</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="目标数据库" prop="targetDatabase">
            <el-select
              v-model="formData.targetDatabase"
              placeholder="请先选择数据源"
              style="width: 100%"
              filterable
              :loading="loadingDatabases"
              :disabled="!formData.targetDatasourceId"
              @change="handleDatabaseChange"
            >
              <el-option
                v-for="db in databases"
                :key="db"
                :label="db"
                :value="db"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 目标表配置 -->
      <el-row :gutter="24">
        <el-col :span="24">
          <el-form-item label="目标表名称" prop="targetTableName">
            <el-select
              v-model="formData.targetTableName"
              placeholder="请选择或输入目标表名"
              style="width: 100%"
              filterable
              allow-create
              default-first-option
              :loading="loadingTables"
              :disabled="!formData.targetDatabase"
              @change="handleTableChange"
            >
              <el-option
                v-for="table in tables"
                :key="table"
                :label="table"
                :value="table"
              />
            </el-select>
            <template #suffix>
              <el-button
                :icon="View"
                size="small"
                :disabled="!formData.targetTableName"
                @click="handlePreviewTable"
              >
                查看表结构
              </el-button>
              <el-button
                :icon="Plus"
                size="small"
                type="primary"
                @click="handleAutoCreateTable"
              >
                自动建表
              </el-button>
            </template>
            <div class="form-tip">
              <el-icon><QuestionFilled /></el-icon>
              支持从列表选择或直接输入新表名（会自动创建）
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 写入模式 -->
      <el-divider content-position="left">写入方式配置</el-divider>

      <el-row :gutter="24">
        <el-col :span="24">
          <el-form-item label="写入模式" prop="writeMode">
            <el-radio-group v-model="formData.writeMode" @change="handleWriteModeChange">
              <el-radio label="append">
                <div class="radio-content">
                  <div class="radio-title">
                    <el-tag type="primary" size="small">追加</el-tag>
                    <span>Append</span>
                  </div>
                  <div class="radio-desc">
                    将数据追加到目标表，保留原有数据。适合增量同步场景。
                  </div>
                </div>
              </el-radio>
              <el-radio label="overwrite">
                <div class="radio-content">
                  <div class="radio-title">
                    <el-tag type="danger" size="small">覆盖</el-tag>
                    <span>Overwrite</span>
                  </div>
                  <div class="radio-desc">
                    清空目标表后写入新数据。适合全量同步场景，⚠️ 会删除原有数据。
                  </div>
                </div>
              </el-radio>
              <el-radio label="upsert">
                <div class="radio-content">
                  <div class="radio-title">
                    <el-tag type="success" size="small">更新</el-tag>
                    <span>Upsert</span>
                  </div>
                  <div class="radio-desc">
                    根据主键判断，存在则更新，不存在则插入。适合需要保持数据最新的场景。
                  </div>
                </div>
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- Upsert主键配置 -->
      <template v-if="formData.writeMode === 'upsert'">
        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="主键字段" prop="primaryKey">
              <el-select
                v-model="formData.primaryKey"
                placeholder="请选择主键字段（可多选）"
                style="width: 100%"
                multiple
                filterable
                :disabled="!formData.targetColumns || formData.targetColumns.length === 0"
              >
                <el-option
                  v-for="col in formData.targetColumns"
                  :key="col"
                  :label="col"
                  :value="col"
                />
              </el-select>
              <div class="form-tip">
                <el-icon><QuestionFilled /></el-icon>
                选择用于判断记录是否存在的唯一标识字段，支持组合主键
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- 分区配置 -->
      <el-divider content-position="left">分区配置</el-divider>

      <el-row :gutter="24">
        <el-col :span="24">
          <el-form-item label="分区字段">
            <el-select
              v-model="formData.partitionFields"
              placeholder="可选择分区字段（仅Hive等数仓支持）"
              style="width: 100%"
              multiple
              filterable
              allow-create
              clearable
            >
              <el-option
                v-for="col in formData.targetColumns"
                :key="col"
                :label="col"
                :value="col"
              />
            </el-select>
            <div class="form-tip">
              <el-icon><QuestionFilled /></el-icon>
              分区字段可提高查询性能，通常选择日期字段如 dt、biz_date 等
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24" v-if="formData.partitionFields.length > 0">
        <el-col :span="12">
          <el-form-item label="分区值">
            <el-input
              v-model="formData.partitionValue"
              placeholder="例如：${biz_date} 或 2024-01-15"
              clearable
            />
            <div class="form-tip">支持使用变量，如 ${biz_date} 表示业务日期</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="分区策略">
            <el-select
              v-model="formData.partitionStrategy"
              placeholder="请选择分区策略"
              style="width: 100%"
            >
              <el-option label="静态分区" value="static">
                <div class="option-content">
                  <span>每次写入固定分区值</span>
                  <span class="option-desc">适合定时任务，如每天写入dt=2024-01-15</span>
                </div>
              </el-option>
              <el-option label="动态分区" value="dynamic">
                <div class="option-content">
                  <span>根据数据自动分区</span>
                  <span class="option-desc">适合流式数据，自动根据字段值分配分区</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 前置/后置SQL -->
      <el-divider content-position="left">钩子脚本</el-divider>

      <el-row :gutter="24">
        <el-col :span="24">
          <el-form-item label="前置SQL">
            <el-input
              v-model="formData.preSql"
              type="textarea"
              :rows="3"
              placeholder="可选：写入数据前执行的SQL，例如清理临时数据&#10;DELETE FROM target_table WHERE dt = '${biz_date}';"
            />
            <div class="form-tip">
              <el-icon><QuestionFilled /></el-icon>
              在数据写入前执行，可用于清理历史数据、创建临时表等
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="24">
          <el-form-item label="后置SQL">
            <el-input
              v-model="formData.postSql"
              type="textarea"
              :rows="3"
              placeholder="可选：写入数据后执行的SQL，例如更新统计信息&#10;ANALYZE TABLE target_table COMPUTE STATISTICS;"
            />
            <div class="form-tip">
              <el-icon><QuestionFilled /></el-icon>
              在数据写入成功后执行，可用于刷新统计信息、发送通知等
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 目标表结构预览 -->
      <el-divider content-position="left">表结构预览</el-divider>

      <el-row :gutter="24">
        <el-col :span="24">
          <el-card shadow="never" class="structure-preview">
            <template #header>
              <div class="card-header">
                <span>目标表字段结构</span>
                <div class="header-actions">
                  <el-tag size="small" v-if="formData.targetColumns">
                    {{ formData.targetColumns.length }} 个字段
                  </el-tag>
                  <el-button
                    size="small"
                    :icon="Refresh"
                    @click="loadTableStructure"
                  >
                    刷新
                  </el-button>
                </div>
              </div>
            </template>

            <el-table
              :data="tableStructureData"
              border
              stripe
              size="small"
              max-height="400"
              v-loading="loadingStructure"
            >
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="name" label="字段名" min-width="150" />
              <el-table-column prop="type" label="类型" width="120" />
              <el-table-column prop="comment" label="说明" min-width="200" />
              <el-table-column label="映射源字段" width="150">
                <template #default="{ row }">
                  <el-tag v-if="getSourceMapping(row.name)" size="small" type="success">
                    {{ getSourceMapping(row.name) }}
                  </el-tag>
                  <span v-else style="color: #909399;">未映射</span>
                </template>
              </el-table-column>
            </el-table>

            <el-empty
              v-if="!tableStructureData.length && !loadingStructure"
              description="请先选择目标表，或自动创建表结构"
            />
          </el-card>
        </el-col>
      </el-row>
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { View, Plus, Refresh, QuestionFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  datasourceOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const formRef = ref()
const databases = ref([])
const tables = ref([])
const loadingDatabases = ref(false)
const loadingTables = ref(false)
const loadingStructure = ref(false)
const tableStructureData = ref([])

const formData = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 数据源类型分组
const groupedDatasources = computed(() => {
  const groups = {
    relational: {
      label: '关系型数据库',
      options: []
    },
    大数据: {
      label: '大数据存储',
      options: []
    },
    其他: {
      label: '其他',
      options: []
    }
  }

  props.datasourceOptions.forEach(ds => {
    const type = ds.dsType?.toLowerCase() || ''
    if (['mysql', 'postgresql', 'oracle', 'sqlserver'].includes(type)) {
      groups.relational.options.push(ds)
    } else if (['hive', 'clickhouse', 'doris'].includes(type)) {
      groups['大数据'].options.push(ds)
    } else {
      groups['其他'].options.push(ds)
    }
  })

  return Object.values(groups).filter(g => g.options.length > 0)
})

// 表单验证规则
const rules = ref({
  targetDatasourceId: [
    { required: true, message: '请选择目标数据源', trigger: 'change' }
  ],
  targetDatabase: [
    { required: true, message: '请选择目标数据库', trigger: 'change' }
  ],
  targetTableName: [
    { required: true, message: '请输入目标表名称', trigger: 'blur' }
  ],
  writeMode: [
    { required: true, message: '请选择写入模式', trigger: 'change' }
  ],
  primaryKey: [
    {
      validator: (rule, value, callback) => {
        if (formData.value.writeMode === 'upsert' && (!value || value.length === 0)) {
          callback(new Error('Upsert模式必须选择主键字段'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
})

// 获取数据源类型标签
function getDsTypeLabel(type) {
  const labels = {
    mysql: 'MySQL',
    postgresql: 'PostgreSQL',
    oracle: 'Oracle',
    sqlserver: 'SQL Server',
    hive: 'Hive',
    clickhouse: 'ClickHouse'
  }
  return labels[type?.toLowerCase()] || type || '未知'
}

function getDsTypeTag(type) {
  const tags = {
    mysql: 'primary',
    postgresql: 'success',
    oracle: 'warning',
    sqlserver: 'info',
    hive: 'danger',
    clickhouse: 'success'
  }
  return tags[type?.toLowerCase()] || 'info'
}

// 事件处理
async function handleDatasourceChange(datasourceId) {
  formData.value.targetDatabase = ''
  formData.value.targetTableName = ''
  formData.value.targetColumns = []
  databases.value = []
  tables.value = []
  tableStructureData.value = []

  if (datasourceId) {
    await loadDatabases(datasourceId)
  }
}

async function loadDatabases(datasourceId) {
  loadingDatabases.value = true
  try {
    // TODO: 调用API获取数据库列表
    await new Promise(resolve => setTimeout(resolve, 500))
    databases.value = ['dw_dwd', 'dw_dws', 'dw_ads']
  } catch (error) {
    console.error('加载数据库失败:', error)
  } finally {
    loadingDatabases.value = false
  }
}

function handleDatabaseChange() {
  formData.value.targetTableName = ''
  formData.value.targetColumns = []
  tables.value = []
  tableStructureData.value = []

  if (formData.value.targetDatabase) {
    loadTables()
  }
}

async function loadTables() {
  loadingTables.value = true
  try {
    // TODO: 调用API获取表列表
    await new Promise(resolve => setTimeout(resolve, 500))
    tables.value = ['dwd_order_info', 'dwd_user_info', 'dws_user_daily_summary']
  } catch (error) {
    console.error('加载表列表失败:', error)
  } finally {
    loadingTables.value = false
  }
}

function handleTableChange() {
  if (formData.value.targetTableName) {
    loadTableStructure()
    // 如果目标字段为空，从源字段复制
    if (!formData.value.targetColumns || formData.value.targetColumns.length === 0) {
      formData.value.targetColumns = [...(formData.value.sourceColumns || [])]
    }
  }
}

async function loadTableStructure() {
  loadingStructure.value = true
  try {
    // TODO: 调用API获取表结构
    await new Promise(resolve => setTimeout(resolve, 500))

    // 模拟数据
    tableStructureData.value = formData.value.targetColumns.map(col => ({
      name: col,
      type: 'STRING',
      comment: ''
    }))
  } catch (error) {
    console.error('加载表结构失败:', error)
  } finally {
    loadingStructure.value = false
  }
}

function handlePreviewTable() {
  // 打开表结构详情对话框
  loadTableStructure()
}

async function handleAutoCreateTable() {
  // TODO: 根据源表结构自动创建目标表
  console.log('Auto create table')

  // 自动填充目标字段
  if (formData.value.sourceColumns && formData.value.sourceColumns.length > 0) {
    formData.value.targetColumns = [...formData.value.sourceColumns]

    tableStructureData.value = formData.value.sourceColumns.map(col => ({
      name: col,
      type: 'STRING',
      comment: ''
    }))

    console.log('Table structure generated')
  }
}

function handleWriteModeChange() {
  if (formData.value.writeMode !== 'upsert') {
    formData.value.primaryKey = []
  }
}

function getSourceMapping(targetField) {
  const mapping = formData.value.fieldMappings?.find(m => m.target === targetField)
  return mapping?.source || null
}

// 表单验证
async function validate() {
  return await formRef.value?.validate()
}

function resetFields() {
  formRef.value?.resetFields()
}

defineExpose({
  validate,
  resetFields
})
</script>

<style scoped lang="scss">
.target-step {
  padding: 16px;
}

.datasource-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;

  .ds-name {
    flex: 1;
  }
}

.radio-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;

  .radio-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
  }

  .radio-desc {
    font-size: 12px;
    color: #909399;
    line-height: 1.5;
    padding-left: 36px;
  }
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .option-desc {
    font-size: 12px;
    color: #909399;
  }
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }
}

.structure-preview {
  :deep(.el-card__body) {
    padding: 0;
  }
}

:deep(.el-radio) {
  display: flex;
  white-space: normal;
  height: auto;
  margin-bottom: 16px;

  .el-radio__label {
    white-space: normal;
  }
}
</style>
