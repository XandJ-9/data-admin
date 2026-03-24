<template>
  <div class="app-container etl-task-detail">
    <!-- 页面头部 -->
    <el-page-header @back="handleBack" class="page-header">
      <template #content>
        <div class="header-content">
          <span v-if="!isEdit">{{ taskForm.taskName || '新建ETL任务' }}</span>
          <el-input
            v-else
            v-model="taskForm.taskName"
            placeholder="请输入任务名称"
            style="width: 300px"
          />
        </div>
      </template>
      <template #extra>
        <div class="header-actions">
          <template v-if="isEdit">
            <el-button @click="isEdit = false">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
          </template>
          <template v-else>
            <el-button @click="handleExecute" :disabled="taskForm.status !== '0'">
              <el-icon><VideoPlay /></el-icon> 执行任务
            </el-button>
            <el-button @click="isEdit = true">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-dropdown @command="handleMoreCommand">
              <el-button>
                更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="clone">克隆任务</el-dropdown-item>
                  <el-dropdown-item command="version">版本管理</el-dropdown-item>
                  <el-dropdown-item command="validate">验证配置</el-dropdown-item>
                  <el-dropdown-item command="datx" divided>生成DataX配置</el-dropdown-item>
                  <el-dropdown-item command="dryRun">模拟执行</el-dropdown-item>
                  <el-dropdown-item command="delete" divided style="color: #f56c6c">删除任务</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </div>
      </template>
    </el-page-header>

    <!-- 任务状态标签 -->
    <div class="task-status-bar">
      <el-tag :type="taskForm.status === '0' ? 'success' : 'danger'" size="large">
        {{ taskForm.status === '0' ? '已启用' : '已停用' }}
      </el-tag>
      <el-tag v-if="taskForm.etlType" :type="getEtlTypeColor(taskForm.etlType)" size="large">
        {{ getEtlTypeText(taskForm.etlType) }}
      </el-tag>
      <el-tag size="large">{{ getExecutorTypeText(taskForm.executorType) }}</el-tag>
      <el-tag :type="taskForm.executeStrategy === 'full' ? 'success' : 'warning'" size="large">
        {{ taskForm.executeStrategy === 'full' ? '全量' : '增量' }}
      </el-tag>
    </div>

    <!-- 内容区域 -->
    <el-card class="detail-card">
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="基本信息" name="basic">
          <BasicInfoTab :form="taskForm" :is-edit="isEdit" />
        </el-tab-pane>

        <el-tab-pane label="数据源配置" name="datasource">
          <DatasourceTab
            :form="taskForm"
            :is-edit="isEdit"
            :datasource-list="datasourceList"
            @columns-loaded="handleColumnsLoaded"
          />
        </el-tab-pane>

        <el-tab-pane label="数据映射" name="mapping">
          <DataMappingTab
            :form="taskForm"
            :is-edit="isEdit"
            :source-columns="sourceColumns"
            :field-mappings="fieldMappings"
          />
        </el-tab-pane>

        <el-tab-pane label="执行配置" name="execution">
          <ExecutionConfigTab :form="taskForm" :is-edit="isEdit" />
        </el-tab-pane>

        <el-tab-pane label="质检规则" name="quality">
          <QualityRulesTab
            :rules="qualityRules"
            @add="handleAddQualityRule"
            @toggle="handleToggleQualityRule"
            @view="handleViewQualityRule"
            @delete="handleDeleteQualityRule"
          />
        </el-tab-pane>

        <el-tab-pane label="执行历史" name="history">
          <ExecutionHistoryTab
            :logs="executionLogs"
            :total="totalLogs"
            :query="logQuery"
            :loading="loadingLogs"
            @view="handleViewExecution"
            @load="loadExecutionLogs"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 执行详情对话框 -->
    <el-dialog
      v-model="executionDetailVisible"
      title="执行详情"
      width="900px"
      append-to-body
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="执行ID">{{ currentExecution.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getExecutionStatusColor(currentExecution.status)">
            {{ getExecutionStatusText(currentExecution.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="读取行数">{{ formatNumber(currentExecution.rowsRead) }}</el-descriptions-item>
        <el-descriptions-item label="写入行数">{{ formatNumber(currentExecution.rowsWritten) }}</el-descriptions-item>
        <el-descriptions-item label="数据大小">{{ formatBytes(currentExecution.dataSize) }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ formatDuration(currentExecution.duration) }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ currentExecution.startTime }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ currentExecution.endTime }}</el-descriptions-item>
        <el-descriptions-item label="执行者">{{ currentExecution.executedBy }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2">
          <span style="color: #f56c6c">{{ currentExecution.errorMessage || '-' }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup name="ETLTaskDetail">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { VideoPlay, Edit, ArrowDown } from '@element-plus/icons-vue'
import {
  getETLTask,
  addETLTask,
  updateETLTask,
  delETLTask,
  executeETLTask,
  cloneETLTask,
  validateETLConfig,
  generateDataXConfig,
  dryRunETLTask,
  listETLExecutionLog,
  getETLExecutionLogDetail,
  listETLFieldMapping,
  batchCreateFieldMapping,
  listETLQualityRule,
  delETLQualityRule
} from '@/api/data/etl'
import { listDatasource } from '@/api/data/datasource'
import { ElMessage, ElMessageBox } from 'element-plus'
import BasicInfoTab from './components/BasicInfoTab.vue'
import DatasourceTab from './components/DatasourceTab.vue'
import DataMappingTab from './components/DataMappingTab.vue'
import ExecutionConfigTab from './components/ExecutionConfigTab.vue'
import QualityRulesTab from './components/QualityRulesTab.vue'
import ExecutionHistoryTab from './components/ExecutionHistoryTab.vue'

const router = useRouter()
const route = useRoute()

const isEdit = ref(false)
const saving = ref(false)
const loadingLogs = ref(false)
const activeTab = ref('basic')
const executionDetailVisible = ref(false)

const taskId = computed(() => route.params.id)
const datasourceList = ref([])
const fieldMappings = ref([])
const sourceColumns = ref([])
const qualityRules = ref([])
const executionLogs = ref([])
const totalLogs = ref(0)
const currentExecution = ref({})

const taskForm = reactive({
  taskName: '',
  taskCode: '',
  description: '',
  category: '',
  etlType: 'full',
  executorType: 'mock',
  executeStrategy: 'full',
  status: '0',
  sourceDatasourceId: null,
  targetDatasourceId: null,
  sourceTableName: '',
  sourceDatabaseName: '',
  targetTable: '',
  sqlConfig: '',
  executorParams: null
})

const logQuery = reactive({
  pageNum: 1,
  pageSize: 10
})

function handleColumnsLoaded(columns) {
  sourceColumns.value = columns
}

onMounted(async () => {
  await loadDatasources()
  if (taskId.value !== 'new') {
    await loadTaskDetail()
    await loadFieldMappings()
    await loadQualityRules()
    await loadExecutionLogs()
  } else {
    isEdit.value = true
    if (route.query.etlType) {
      taskForm.etlType = route.query.etlType
    }
  }
})

watch(
  () => route.params.id,
  async (newId, oldId) => {
    if (route.name !== 'ETLTaskDetail') return
    if (newId === 'new' && oldId === 'new') return

    if (newId === 'new') {
      Object.assign(taskForm, {
        taskName: '',
        taskCode: '',
        description: '',
        category: '',
        etlType: route.query.etlType || 'full',
        executorType: 'mock',
        executeStrategy: 'full',
        status: '0',
        sourceDatasourceId: null,
        targetDatasourceId: null,
        sourceTableName: '',
        sourceDatabaseName: '',
        targetTable: '',
        sqlConfig: '',
        executorParams: null
      })
      isEdit.value = true
      fieldMappings.value = []
      sourceColumns.value = []
      qualityRules.value = []
      executionLogs.value = []
    } else {
      isEdit.value = false
      await loadTaskDetail()
      await loadFieldMappings()
      await loadQualityRules()
      await loadExecutionLogs()
    }
  },
  { immediate: false }
)

async function loadDatasources() {
  try {
    const res = await listDatasource({ pageNum: 1, pageSize: 1000 })
    datasourceList.value = res.rows || []
  } catch (error) {
    console.error('加载数据源列表失败:', error)
  }
}

async function loadTaskDetail() {
  try {
    const res = await getETLTask(taskId.value)
    Object.assign(taskForm, res.data)
  } catch (error) {
    console.error('加载任务详情失败:', error)
  }
}

async function loadFieldMappings() {
  try {
    const res = await listETLFieldMapping({ taskId: taskId.value })
    fieldMappings.value = res.rows || []
  } catch (error) {
    console.error('加载字段映射失败:', error)
  }
}

async function loadQualityRules() {
  try {
    const res = await listETLQualityRule({ taskId: taskId.value })
    qualityRules.value = res.rows || []
  } catch (error) {
    console.error('加载质检规则失败:', error)
  }
}

async function loadExecutionLogs() {
  loadingLogs.value = true
  try {
    const res = await listETLExecutionLog({
      taskId: taskId.value,
      ...logQuery
    })
    executionLogs.value = res.rows || []
    totalLogs.value = res.total || 0
  } catch (error) {
    console.error('加载执行历史失败:', error)
  } finally {
    loadingLogs.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    let savedTaskId
    if (taskId.value === 'new') {
      const res = await addETLTask(taskForm)
      savedTaskId = res.data.id
      ElMessage.success('创建成功')
    } else {
      await updateETLTask(taskForm)
      savedTaskId = taskId.value
      ElMessage.success('保存成功')
    }

    if (fieldMappings.value.length > 0) {
      await batchCreateFieldMapping({
        taskId: savedTaskId,
        mappings: fieldMappings.value
      })
    }

    if (taskId.value === 'new') {
      router.push({ name: 'ETLTaskDetail', params: { id: savedTaskId } })
    } else {
      isEdit.value = false
      await loadTaskDetail()
    }
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

async function handleExecute() {
  try {
    await ElMessageBox.confirm('确认要执行该任务吗？', '提示', { type: 'warning' })
    await executeETLTask(taskId.value)
    ElMessage.success('任务已提交执行')
    activeTab.value = 'history'
    await loadExecutionLogs()
  } catch (error) {
    if (error !== 'cancel') console.error('执行任务失败:', error)
  }
}

async function handleMoreCommand(command) {
  const actions = {
    clone: handleClone,
    validate: handleValidate,
    datx: handleGenerateDataX,
    dryRun: handleDryRun,
    delete: handleDelete
  }
  if (actions[command]) await actions[command]()
}

async function handleClone() {
  try {
    await cloneETLTask(taskId.value, {})
    ElMessage.success('克隆成功')
  } catch (error) {
    console.error('克隆失败:', error)
  }
}

async function handleValidate() {
  try {
    await validateETLConfig(taskId.value)
    ElMessage.success('配置验证通过')
  } catch (error) {
    console.error('验证失败:', error)
  }
}

async function handleGenerateDataX() {
  try {
    const res = await generateDataXConfig(taskId.value, {})
    ElMessageBox.alert(JSON.stringify(res.data, null, 2), 'DataX配置', {
      customClass: 'json-dialog'
    })
  } catch (error) {
    console.error('生成配置失败:', error)
  }
}

async function handleDryRun() {
  try {
    await ElMessageBox.confirm('模拟执行不会写入目标数据，确认继续？', '提示', { type: 'warning' })
    await dryRunETLTask(taskId.value)
    ElMessage.success('模拟执行已完成')
  } catch (error) {
    if (error !== 'cancel') console.error('模拟执行失败:', error)
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确认要删除该任务吗？删除后不可恢复！', '警告', { type: 'warning' })
    await delETLTask(taskId.value)
    ElMessage.success('删除成功')
    handleBack()
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

function handleBack() {
  router.back()
}

function handleAddQualityRule() {
  router.push({ name: 'QualityRuleCreate', query: { taskId: taskId.value } })
}

async function handleToggleQualityRule(row) {
  // 切换质检规则启用状态
}

function handleViewQualityRule(row) {
  // 查看质检规则详情
}

async function handleDeleteQualityRule(row) {
  try {
    await delETLQualityRule(row.id)
    await loadQualityRules()
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('删除失败:', error)
  }
}

async function handleViewExecution(row) {
  try {
    const res = await getETLExecutionLogDetail(row.id)
    currentExecution.value = res.data
    executionDetailVisible.value = true
  } catch (error) {
    console.error('加载执行详情失败:', error)
  }
}

// 辅助函数
function getEtlTypeColor(etlType) {
  const colors = { extract: 'info', transform: 'success', load: 'warning', full: 'danger' }
  return colors[etlType] || ''
}

function getEtlTypeText(etlType) {
  const texts = { extract: 'STG采集', transform: 'DWD转换', load: 'ODS加载', full: '全量ETL' }
  return texts[etlType] || etlType
}

function getExecutorTypeText(executorType) {
  const texts = { mock: '模拟', datax: 'DataX', spark: 'Spark', python: 'Python' }
  return texts[executorType] || executorType
}

function getExecutionStatusText(status) {
  const texts = { pending: '等待执行', running: '执行中', success: '成功', failed: '失败', cancelled: '已取消' }
  return texts[status] || status
}

function getExecutionStatusColor(status) {
  const colors = { pending: 'info', running: 'warning', success: 'success', failed: 'danger', cancelled: '' }
  return colors[status] || ''
}

function formatNumber(num) {
  if (!num) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

function formatDuration(seconds) {
  if (!seconds) return '0秒'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (hours > 0) return `${hours}小时${minutes}分${secs}秒`
  if (minutes > 0) return `${minutes}分${secs}秒`
  return `${secs}秒`
}
</script>

<style scoped lang="scss">
.etl-task-detail {
  .page-header {
    margin-bottom: 16px;

    .header-content {
      display: flex;
      align-items: center;
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .task-status-bar {
    margin-bottom: 16px;
    display: flex;
    gap: 12px;
  }
}

:deep(.json-dialog) {
  .el-message-box__content {
    text-align: left;
    pre {
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }
}
</style>
