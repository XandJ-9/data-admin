<template>
  <div class="app-container task-detail-page" v-loading="loading">
    <div class="page-head">
      <div>
        <div class="page-path">任务运维 / 任务详情</div>
        <h1>{{ taskDetail.taskName || '任务详情' }}</h1>
        <p>{{ taskDetail.remark || '这里展示任务运维视角下的数据集成 / 建模与加工任务配置、来源和运行概况。' }}</p>
      </div>
      <div class="page-actions">
        <el-button :icon="ArrowLeft" @click="goBack">返回任务运维</el-button>
        <el-button
          type="primary"
          plain
          :icon="VideoPlay"
          @click="handleExecuteTask"
          :loading="executing"
          v-hasPermi="['datatask:task:execute']"
        >立即执行</el-button>
        <el-button
          v-if="canOpenSourceDetail && canViewSourceDetail"
          type="primary"
          :icon="Right"
          @click="openSourceDetail"
        >{{ sourceDetailText }}</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="16">
        <el-card shadow="hover" class="detail-card">
          <template #header><span>任务概况</span></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="任务编码">{{ taskDetail.taskCode || '-' }}</el-descriptions-item>
            <el-descriptions-item label="任务状态">
              <el-tag :type="statusTag(taskDetail.status)">{{ statusLabel(taskDetail.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="任务类型">
              <el-tag :type="taskTypeTag(taskDetail.taskType)" effect="plain">{{ taskTypeLabel(taskDetail.taskType) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="调度方式">{{ scheduleTypeLabel(taskDetail.scheduleType) }}</el-descriptions-item>
            <el-descriptions-item label="来源模块">
              <el-tag :type="sourceModuleTag(taskDetail.sourceModule)" effect="plain">{{ sourceModuleLabel(taskDetail.sourceModule) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="来源记录">{{ taskDetail.sourceRecordId || '-' }}</el-descriptions-item>
            <el-descriptions-item label="负责人">{{ taskDetail.owner || '-' }}</el-descriptions-item>
            <el-descriptions-item label="最近运行">{{ formatLastRun(taskDetail) }}</el-descriptions-item>
            <el-descriptions-item label="Cron" :span="2">{{ taskDetail.cronExpression || '未配置' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card v-if="canViewInstances" shadow="hover" class="detail-card">
          <template #header>
            <div class="section-head">
              <div>
                <span>最近执行记录</span>
              </div>
              <el-button text type="primary" @click="loadTaskInstances">刷新记录</el-button>
            </div>
          </template>
          <el-table :data="instanceList" border>
            <el-table-column label="实例ID" prop="instanceId" min-width="220" show-overflow-tooltip />
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="executionStatusTag(row.status)">{{ executionStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="触发方式" prop="triggerMode" width="110" />
            <el-table-column label="触发人" prop="triggeredBy" width="120" />
            <el-table-column label="开始时间" prop="startedAt" width="180" />
            <el-table-column label="结束时间" prop="finishedAt" width="180" />
            <el-table-column label="执行情况" min-width="260">
              <template #default="{ row }">
                <div class="execution-result-cell">
                  <strong>{{ formatExecutionOutcome(row) }}</strong>
                  <span v-if="row.errorMessage">{{ row.errorMessage }}</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card v-if="canViewDependencies" shadow="hover" class="detail-card">
          <template #header><span>依赖关系</span></template>
          <div class="dependency-section">
            <h4>上游任务</h4>
            <el-empty v-if="!upstreamDependencies.length" description="暂无上游依赖" :image-size="64" />
            <div v-else class="dependency-list">
              <button v-for="item in upstreamDependencies" :key="item.dependencyId" type="button" class="dependency-item" @click="openOtherTask(item.upstreamTaskId)">
                <strong>{{ item.upstreamTaskName }}</strong>
                <span>{{ item.upstreamTaskCode }}</span>
              </button>
            </div>
          </div>
          <div class="dependency-section">
            <h4>下游任务</h4>
            <el-empty v-if="!downstreamDependencies.length" description="暂无下游依赖" :image-size="64" />
            <div v-else class="dependency-list">
              <button v-for="item in downstreamDependencies" :key="item.dependencyId" type="button" class="dependency-item" @click="openOtherTask(item.downstreamTaskId)">
                <strong>{{ item.downstreamTaskName }}</strong>
                <span>{{ item.downstreamTaskCode }}</span>
              </button>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover" class="detail-card">
          <template #header><span>任务配置</span></template>
          <pre class="json-preview">{{ formatJson(taskDetail.taskConfig) }}</pre>
        </el-card>

        <el-card shadow="hover" class="detail-card">
          <template #header><span>治理配置</span></template>
          <el-alert
            v-if="taskDetail.scheduleType === 'dependency'"
            type="info"
            :closable="false"
            title="当前任务已被编排为依赖触发，调度方式请前往任务编排维护。"
            class="governance-alert"
          />
          <el-form ref="manageFormRef" :model="manageForm" label-position="top" class="governance-form">
            <el-form-item label="任务状态">
              <el-segmented
                v-model="manageForm.status"
                :options="statusOptions"
                block
              />
            </el-form-item>
            <el-form-item label="负责人">
              <el-input v-model="manageForm.owner" placeholder="填写负责人" clearable />
            </el-form-item>
            <el-form-item label="调度方式">
              <el-radio-group
                v-model="manageForm.scheduleType"
                :disabled="taskDetail.scheduleType === 'dependency'"
              >
                <el-radio-button label="manual">手动触发</el-radio-button>
                <el-radio-button label="cron">Cron 调度</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="manageForm.scheduleType === 'cron'" label="Cron 表达式">
              <el-input v-model="manageForm.cronExpression" placeholder="如：0 1 * * *" />
            </el-form-item>
            <el-form-item label="任务备注">
              <el-input v-model="manageForm.remark" type="textarea" :rows="4" placeholder="补充任务运维说明" />
            </el-form-item>
            <div class="governance-actions">
              <el-button
                type="primary"
                :loading="saving"
                @click="handleSaveTask"
                v-hasPermi="['datatask:task:edit']"
              >保存治理配置</el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="DataTaskDetail">
import { ArrowLeft, Right, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { executeTask, getTask, getTaskInstances, listTaskDependencies, updateTask } from '@/api/data/datatask'
import { checkPermi } from '@/utils/permission'
import {
  executionStatusLabel,
  executionStatusTag,
  formatExecutionOutcome,
  formatJson,
  formatLastRun,
  scheduleTypeLabel,
  sourceModuleLabel,
  sourceModuleTag,
  statusLabel,
  statusTag,
  taskTypeLabel,
  taskTypeTag,
} from '../taskMeta'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const executing = ref(false)
const taskDetail = ref({})
const instanceList = ref([])
const upstreamDependencies = ref([])
const downstreamDependencies = ref([])
const requestSerial = ref(0)
const instanceRequestSerial = ref(0)
const pollTimer = ref(null)
const pageActive = ref(true)
const manageFormRef = ref()
const manageForm = reactive({
  status: 'active',
  scheduleType: 'manual',
  cronExpression: '',
  owner: '',
  remark: '',
})
const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '启用', value: 'active' },
  { label: '暂停', value: 'paused' },
  { label: '归档', value: 'archived' },
]

const canOpenSourceDetail = computed(() => {
  if (taskDetail.value.sourceModule === 'datasource.collection') {
    return !!taskDetail.value.taskConfig?.dataSourceId
  }
  if (!taskDetail.value.sourceRecordId) {
    return false
  }
  if (['dataintegration.task', 'datadev.script'].includes(taskDetail.value.sourceModule)) {
    return true
  }
  return false
})

const sourceDetailText = computed(() => {
  if (taskDetail.value.sourceModule === 'dataintegration.task') {
    return '进入集成详情'
  }
  if (taskDetail.value.sourceModule === 'datadev.script') {
    return '进入加工作业'
  }
  if (taskDetail.value.sourceModule === 'datasource.collection') {
    return '进入数据源详情'
  }
  return '进入来源详情'
})

const canViewInstances = checkPermi(['datatask:instance:list'])
const canViewDependencies = checkPermi(['datatask:dependency:query'])
const canViewSourceDetail = computed(() => {
  if (taskDetail.value.sourceModule === 'dataintegration.task') {
    return checkPermi(['dataintegration:task:view'])
  }
  if (taskDetail.value.sourceModule === 'datadev.script') {
    return checkPermi(['datadev:ide:view'])
  }
  if (taskDetail.value.sourceModule === 'datasource.collection') {
    return checkPermi(['system:datasource:query'])
  }
  return false
})

function getErrorMessage(error, fallback = '加载任务详情失败') {
  return error?.response?.data?.msg || error?.response?.data?.message || error?.message || fallback
}

function notifyError(error, fallback = '加载任务详情失败') {
  if (error?.__handled) {
    return
  }
  ElMessage.error(getErrorMessage(error, fallback))
}

function updateInstanceList(rows = []) {
  instanceList.value = rows
  schedulePolling()
}

async function loadTaskInstances(options = {}) {
  const { silent = false } = options
  const requestId = instanceRequestSerial.value + 1
  instanceRequestSerial.value = requestId
  stopPolling()
  if (!canViewInstances) {
    instanceList.value = []
    return
  }
  try {
    const taskId = route.params.id
    const response = await getTaskInstances(taskId, { pageNum: 1, pageSize: 8 })
    if (!pageActive.value || requestId !== instanceRequestSerial.value || String(taskId) !== String(route.params.id)) {
      return
    }
    updateInstanceList(response.rows || [])
  } catch (error) {
    if (!pageActive.value || requestId !== instanceRequestSerial.value) {
      return
    }
    const shouldRetry = instanceList.value.some(item => ['pending', 'running'].includes(item.status))
    stopPolling()
    schedulePolling(5000, shouldRetry)
    if (!silent) {
      notifyError(error, '加载执行记录失败')
    }
  }
}

async function loadTaskDetail() {
  stopPolling()
  const requestId = requestSerial.value + 1
  const instanceRequestId = instanceRequestSerial.value + 1
  requestSerial.value = requestId
  instanceRequestSerial.value = instanceRequestId
  loading.value = true
  try {
    const taskId = route.params.id
    const [taskRes, instanceRes, upstreamRes, downstreamRes] = await Promise.all([
      getTask(taskId),
      canViewInstances ? getTaskInstances(taskId, { pageNum: 1, pageSize: 8 }) : Promise.resolve({ rows: [] }),
      canViewDependencies ? listTaskDependencies({ downstreamTaskId: taskId }) : Promise.resolve({ rows: [] }),
      canViewDependencies ? listTaskDependencies({ upstreamTaskId: taskId }) : Promise.resolve({ rows: [] }),
    ])
    if (
      !pageActive.value ||
      requestId !== requestSerial.value ||
      instanceRequestId !== instanceRequestSerial.value ||
      String(taskId) !== String(route.params.id)
    ) {
      return
    }
    taskDetail.value = taskRes.data || {}
    updateInstanceList(instanceRes.rows || [])
    upstreamDependencies.value = upstreamRes.rows || []
    downstreamDependencies.value = downstreamRes.rows || []
    syncManageForm(taskDetail.value)
  } catch (error) {
    if (!pageActive.value || requestId !== requestSerial.value || instanceRequestId !== instanceRequestSerial.value) {
      return
    }
    taskDetail.value = {}
    instanceList.value = []
    upstreamDependencies.value = []
    downstreamDependencies.value = []
    stopPolling()
    notifyError(error)
  } finally {
    if (requestId === requestSerial.value) {
      loading.value = false
    }
  }
}

function stopPolling() {
  if (pollTimer.value) {
    clearTimeout(pollTimer.value)
    pollTimer.value = null
  }
}

function schedulePolling(delay = 3000, force = false) {
  stopPolling()
  if (!pageActive.value) {
    return
  }
  if (!force && !instanceList.value.some(item => ['pending', 'running'].includes(item.status))) {
    return
  }
  pollTimer.value = setTimeout(() => {
    loadTaskInstances({ silent: true })
  }, delay)
}

function syncManageForm(task = {}) {
  manageForm.status = task.status || 'active'
  manageForm.scheduleType = task.scheduleType === 'dependency' ? 'manual' : (task.scheduleType || 'manual')
  manageForm.cronExpression = task.scheduleType === 'cron' ? (task.cronExpression || '') : ''
  manageForm.owner = task.owner || ''
  manageForm.remark = task.remark || ''
}

function goBack() {
  router.push({ name: 'DataTaskIndex' })
}

function openSourceDetail() {
  if (!canOpenSourceDetail.value) {
    return
  }
  if (taskDetail.value.sourceModule === 'dataintegration.task') {
    router.push({
      name: 'DataIntegrationTaskDetail',
      params: { taskId: taskDetail.value.sourceRecordId },
      query: { from: 'task-detail', returnTaskId: route.params.id },
    })
    return
  }
  if (taskDetail.value.sourceModule === 'datadev.script') {
    router.push(`/datadev/ide/detail/${taskDetail.value.sourceRecordId}`)
    return
  }
  if (taskDetail.value.sourceModule === 'datasource.collection' && taskDetail.value.taskConfig?.dataSourceId) {
    const latestInstanceId = taskDetail.value.taskConfig?.collectionScope === 'database'
      ? (instanceList.value[0]?.instanceId || '')
      : ''
    router.push({
      name: 'DataSourceDetail',
      params: { id: taskDetail.value.taskConfig.dataSourceId },
      query: {
        from: 'task-detail',
        returnTaskId: route.params.id,
        databaseName: taskDetail.value.taskConfig.databaseName || '',
        tableName: taskDetail.value.taskConfig.tableName || '',
        runId: latestInstanceId,
      },
    })
  }
}

function openOtherTask(taskId) {
  router.push({ name: 'DataTaskDetail', params: { id: taskId } })
}

async function handleSaveTask() {
  const taskId = route.params.id
  saving.value = true
  try {
    const payload = {
      status: manageForm.status,
      owner: manageForm.owner,
      remark: manageForm.remark,
    }
    if (taskDetail.value.scheduleType !== 'dependency') {
      payload.scheduleType = manageForm.scheduleType
      payload.cronExpression = manageForm.scheduleType === 'cron' ? manageForm.cronExpression : ''
    }
    await updateTask(taskId, payload)
    ElMessage.success('治理配置已更新')
    await loadTaskDetail()
  } catch (error) {
    notifyError(error, '更新任务治理配置失败')
  } finally {
    saving.value = false
  }
}

async function handleExecuteTask() {
  const taskId = route.params.id
  executing.value = true
  try {
    await executeTask(taskId)
    ElMessage.success('任务已触发执行')
    await loadTaskDetail()
  } catch (error) {
    notifyError(error, '触发任务执行失败')
  } finally {
    executing.value = false
  }
}

watch(
  () => route.params.id,
  () => {
    loadTaskDetail()
  }
)

onMounted(() => {
  loadTaskDetail()
})

onBeforeUnmount(() => {
  pageActive.value = false
  stopPolling()
})
</script>

<style scoped>
.task-detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-head,
.page-actions {
  display: flex;
  gap: 12px;
}

.page-head {
  justify-content: space-between;
  align-items: flex-start;
}

.page-head h1 {
  margin: 8px 0;
}

.page-head p,
.page-path,
.dependency-item span,
.execution-result-cell span {
  color: var(--el-text-color-secondary);
}

.page-actions {
  flex-wrap: wrap;
}

.detail-card {
  margin-bottom: 16px;
  border-radius: 18px;
}

.governance-alert {
  margin-bottom: 16px;
}

.dependency-section + .dependency-section {
  margin-top: 20px;
}

.dependency-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dependency-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 14px;
  background: var(--el-bg-color);
  text-align: left;
  cursor: pointer;
}

.execution-result-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.json-preview {
  margin: 0;
  padding: 12px;
  overflow: auto;
  border-radius: 12px;
  background: var(--el-fill-color-light);
  font-size: 12px;
  line-height: 1.6;
}

.governance-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.governance-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .page-head {
    flex-direction: column;
  }
}
</style>
