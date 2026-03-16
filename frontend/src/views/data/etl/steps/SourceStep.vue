<template>
  <div class="source-step">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="140px"
      label-position="right"
    >
      <el-alert
        title="源端数据源配置"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 24px"
      >
        配置数据来源信息，选择数据源、数据库和表，并设置数据抽取方式
      </el-alert>

      <!-- 数据源选择 -->
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="数据源" prop="sourceDatasourceId">
            <el-select
              v-model="formData.sourceDatasourceId"
              placeholder="请选择数据源"
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
            <div class="form-tip">选择已配置的数据源连接</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="数据库名称" prop="sourceDatabase">
            <el-select
              v-model="formData.sourceDatabase"
              placeholder="请先选择数据源"
              style="width: 100%"
              filterable
              :loading="loadingDatabases"
              :disabled="!formData.sourceDatasourceId"
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

      <!-- 查询类型选择 -->
      <el-row :gutter="24">
        <el-col :span="24">
          <el-form-item label="查询类型" prop="sourceQueryType">
            <el-radio-group v-model="formData.sourceQueryType" @change="handleQueryTypeChange">
              <el-radio label="table">
                <div class="radio-content">
                  <div class="radio-title">表查询</div>
                  <div class="radio-desc">直接选择整张表作为数据来源</div>
                </div>
              </el-radio>
              <el-radio label="query">
                <div class="radio-content">
                  <div class="radio-title">SQL查询</div>
                  <div class="radio-desc">通过自定义SQL查询获取数据</div>
                </div>
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 表选择 -->
      <template v-if="formData.sourceQueryType === 'table'">
        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="源表名称" prop="sourceTableName">
              <el-select
                v-model="formData.sourceTableName"
                placeholder="请先选择数据库"
                style="width: 100%"
                filterable
                :loading="loadingTables"
                :disabled="!formData.sourceDatabase"
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
                  :disabled="!formData.sourceTableName"
                  @click="handlePreviewTable"
                >
                  预览数据
                </el-button>
              </template>
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- SQL查询 -->
      <template v-if="formData.sourceQueryType === 'query'">
        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="SQL查询" prop="sourceQuery">
              <div class="sql-editor-wrapper">
                <SqlEditor
                  v-model="formData.sourceQuery"
                  :language="getSqlLanguage()"
                  :height="200"
                  placeholder="请输入SQL查询语句，例如：SELECT * FROM user WHERE create_time > '${last_run_time}'"
                />
                <div class="editor-actions">
                  <el-button size="small" :icon="MagicStick" @click="handleFormatSql">
                    格式化
                  </el-button>
                  <el-button size="small" :icon="View" @click="handlePreviewQuery">
                    预览结果
                  </el-button>
                </div>
              </div>
              <div class="form-tip">
                <el-icon><QuestionFilled /></el-icon>
                支持变量：${last_run_time}（上次运行时间）、${biz_date}（业务日期）
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- 抽取方式 -->
      <template v-if="formData.sourceQueryType === 'table'">
        <el-divider content-position="left">抽取方式配置</el-divider>

        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="抽取模式" prop="extractMode">
              <el-radio-group v-model="formData.extractMode" @change="handleExtractModeChange">
                <el-radio label="full">
                  <div class="radio-content">
                    <div class="radio-title">
                      <el-tag type="success" size="small">全量抽取</el-tag>
                    </div>
                    <div class="radio-desc">每次抽取全部数据，适合小表或初始化</div>
                  </div>
                </el-radio>
                <el-radio label="increment">
                  <div class="radio-content">
                    <div class="radio-title">
                      <el-tag type="warning" size="small">增量抽取</el-tag>
                    </div>
                    <div class="radio-desc">只抽取新增或变更的数据，更高效</div>
                  </div>
                </el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 增量配置 -->
        <template v-if="formData.extractMode === 'increment'">
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="增量字段" prop="incrementField">
                <el-select
                  v-model="formData.incrementField"
                  placeholder="请选择增量字段"
                  style="width: 100%"
                  filterable
                  :disabled="!formData.sourceColumns || formData.sourceColumns.length === 0"
                >
                  <el-option
                    v-for="col in suggestedIncrementColumns"
                    :key="col.name"
                    :label="col.name"
                    :value="col.name"
                  >
                    <div class="column-option">
                      <span>{{ col.name }}</span>
                      <el-tag size="small" type="info">{{ col.type }}</el-tag>
                      <el-tag v-if="col.isRecommended" size="small" type="success">推荐</el-tag>
                    </div>
                  </el-option>
                </el-select>
                <div class="form-tip">
                  <el-icon><QuestionFilled /></el-icon>
                  系统会记录该字段的最大值，下次只同步大于该值的数据
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="增量策略" prop="incrementStrategy">
                <el-select
                  v-model="formData.incrementStrategy"
                  placeholder="请选择增量策略"
                  style="width: 100%"
                >
                  <el-option label="时间戳" value="timestamp">
                    <div class="option-content">
                      <span>基于时间字段递增</span>
                      <span class="option-desc">适合 updated_at、create_time 等时间字段</span>
                    </div>
                  </el-option>
                  <el-option label="自增ID" value="auto_increment">
                    <div class="option-content">
                      <span>基于自增ID递增</span>
                      <span class="option-desc">适合 id、seq_id 等自增字段</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </template>
      </template>

      <!-- 数据预览 -->
      <el-divider content-position="left">数据预览（前10条）</el-divider>
      <el-row :gutter="24">
        <el-col :span="24">
          <div v-if="previewData.length > 0" class="preview-table-wrapper">
            <el-table
              :data="previewData"
              border
              stripe
              size="small"
              max-height="400"
            >
              <el-table-column
                v-for="col in previewColumns"
                :key="col"
                :prop="col"
                :label="col"
                min-width="120"
                show-overflow-tooltip
              />
            </el-table>
            <div class="preview-tip">
              <el-icon><InfoFilled /></el-icon>
              仅展示前10条数据用于预览，实际同步时会处理全部数据
            </div>
          </div>
          <el-empty
            v-else
            description="请先配置数据源和表信息，然后点击"预览数据"查看数据样例"
          />
        </el-col>
      </el-row>
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { View, MagicStick, QuestionFilled, InfoFilled } from '@element-plus/icons-vue'
import SqlEditor from '../components/SqlEditor.vue'

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

const emit = defineEmits(['update:modelValue', 'change', 'datasource-change'])

const formRef = ref()
const databases = ref([])
const tables = ref([])
const loadingDatabases = ref(false)
const loadingTables = ref(false)
const previewData = ref([])
const previewColumns = ref([])

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

// 推荐的增量字段
const suggestedIncrementColumns = computed(() => {
  if (!formData.value.sourceColumns) return []

  const keywords = {
    timestamp: ['time', 'date', 'updated', 'created', 'modified'],
    auto_increment: ['id', 'seq', 'no']
  }

  const strategy = formData.value.incrementStrategy || 'timestamp'
  const targetKeywords = keywords[strategy] || keywords.timestamp

  return formData.value.sourceColumns.map(col => ({
    name: col,
    type: '未知',
    isRecommended: targetKeywords.some(kw => col.toLowerCase().includes(kw))
  })).sort((a, b) => b.isRecommended - a.isRecommended)
})

// 表单验证规则
const rules = ref({
  sourceDatasourceId: [
    { required: true, message: '请选择数据源', trigger: 'change' }
  ],
  sourceDatabase: [
    { required: true, message: '请选择数据库', trigger: 'change' }
  ],
  sourceTableName: [
    {
      validator: (rule, value, callback) => {
        if (formData.value.sourceQueryType === 'table' && !value) {
          callback(new Error('请选择源表'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  sourceQuery: [
    {
      validator: (rule, value, callback) => {
        if (formData.value.sourceQueryType === 'query' && !value) {
          callback(new Error('请输入SQL查询'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  extractMode: [
    { required: true, message: '请选择抽取模式', trigger: 'change' }
  ],
  incrementField: [
    {
      validator: (rule, value, callback) => {
        if (formData.value.extractMode === 'increment' && !value) {
          callback(new Error('请选择增量字段'))
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

function getSqlLanguage() {
  const ds = props.datasourceOptions.find(d => d.id === formData.value.sourceDatasourceId)
  const type = ds?.dsType?.toLowerCase() || ''
  if (['mysql', 'postgresql', 'oracle', 'sqlserver'].includes(type)) {
    return type
  }
  return 'sql'
}

// 事件处理
async function handleDatasourceChange(datasourceId) {
  emit('datasource-change', datasourceId)
  formData.value.sourceDatabase = ''
  formData.value.sourceTableName = ''
  formData.value.sourceColumns = []
  databases.value = []
  tables.value = []

  if (datasourceId) {
    await loadDatabases(datasourceId)
  }
}

async function loadDatabases(datasourceId) {
  loadingDatabases.value = true
  try {
    // TODO: 调用API获取数据库列表
    // const res = await getDatasourceDatabases(datasourceId)
    // databases.value = res.data

    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 500))
    databases.value = ['db_business', 'db_log', 'db_analytics']
  } catch (error) {
    console.error('加载数据库失败:', error)
  } finally {
    loadingDatabases.value = false
  }
}

function handleDatabaseChange() {
  formData.value.sourceTableName = ''
  formData.value.sourceColumns = []
  tables.value = []

  if (formData.value.sourceDatabase) {
    loadTables()
  }
}

async function loadTables() {
  loadingTables.value = true
  try {
    // TODO: 调用API获取表列表
    // const res = await getDatasourceTables(formData.value.sourceDatasourceId, formData.value.sourceDatabase)
    // tables.value = res.data

    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 500))
    tables.value = ['users', 'orders', 'order_items', 'products']
  } catch (error) {
    console.error('加载表列表失败:', error)
  } finally {
    loadingTables.value = false
  }
}

function handleQueryTypeChange() {
  if (formData.value.sourceQueryType === 'query') {
    formData.value.extractMode = undefined
    formData.value.incrementField = undefined
  }
}

function handleTableChange() {
  if (formData.value.sourceTableName) {
    loadTableColumns()
    // 自动推荐增量字段
    autoSelectIncrementField()
  }
}

async function loadTableColumns() {
  try {
    // TODO: 调用API获取表字段
    // const res = await getTableColumns(formData.value.sourceDatasourceId, formData.value.sourceDatabase, formData.value.sourceTableName)
    // formData.value.sourceColumns = res.data

    // 模拟数据
    formData.value.sourceColumns = ['id', 'user_id', 'order_id', 'amount', 'status', 'created_at', 'updated_at']
  } catch (error) {
    console.error('加载表字段失败:', error)
  }
}

function autoSelectIncrementField() {
  const cols = formData.value.sourceColumns || []
  const timeFields = cols.filter(col =>
    col.toLowerCase().includes('updated') ||
    col.toLowerCase().includes('modified') ||
    col.toLowerCase().includes('time')
  )

  if (timeFields.length > 0) {
    formData.value.incrementField = timeFields[0]
    formData.value.incrementStrategy = 'timestamp'
  } else if (cols.includes('id')) {
    formData.value.incrementField = 'id'
    formData.value.incrementStrategy = 'auto_increment'
  }
}

function handleExtractModeChange() {
  if (formData.value.extractMode === 'full') {
    formData.value.incrementField = ''
  }
}

function handlePreviewTable() {
  // TODO: 调用API预览表数据
  previewData.value = [
    { id: 1, user_id: 100, amount: 99.99, status: 'paid', created_at: '2024-01-15 10:30:00' },
    { id: 2, user_id: 101, amount: 199.99, status: 'pending', created_at: '2024-01-15 11:00:00' }
  ]
  previewColumns.value = formData.value.sourceColumns || []
}

function handlePreviewQuery() {
  // TODO: 调用API预览查询结果
  previewData.value = []
  previewColumns.value = []
}

function handleFormatSql() {
  // SQL格式化逻辑
  const sql = formData.value.sourceQuery || ''
  // TODO: 使用sql-formatter库
  console.log('Format SQL:', sql)
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
.source-step {
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

.column-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.radio-content {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .radio-title {
    font-weight: 500;
  }

  .radio-desc {
    font-size: 12px;
    color: #909399;
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

.sql-editor-wrapper {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;

  .editor-actions {
    padding: 8px;
    background: #f5f7fa;
    border-top: 1px solid #dcdfe6;
    display: flex;
    gap: 8px;
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

.preview-table-wrapper {
  .preview-tip {
    margin-top: 12px;
    padding: 8px 12px;
    background: #f0f9ff;
    border-radius: 4px;
    color: #409EFF;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
}

:deep(.el-radio) {
  display: flex;
  white-space: normal;
  height: auto;
  margin-bottom: 12px;

  .el-radio__label {
    white-space: normal;
  }
}
</style>
