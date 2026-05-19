<template>
  <div class="app-container task-instance-page" v-loading="loading">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-layout">
        <div>
          <span class="hero-eyebrow">任务运维实例</span>
          <h1>集中查看数据集成、建模加工与源数据采集的执行记录</h1>
          <p>这里聚焦实例层：谁触发、什么时候跑、跑得怎么样。需要改配置时回到对应任务详情页。</p>
        </div>
        <div class="hero-actions">
          <el-button :icon="ArrowLeft" @click="goBack">返回任务运维</el-button>
          <el-button :icon="Refresh" @click="getList">刷新记录</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="filter-card">
      <div class="filter-layout">
        <el-input v-model="queryParams.taskId" placeholder="任务 ID" clearable class="filter-input" />
        <el-select v-model="queryParams.status" clearable placeholder="实例状态" class="filter-input">
          <el-option label="等待执行" value="pending" />
          <el-option label="执行中" value="running" />
          <el-option label="执行成功" value="success" />
          <el-option label="执行失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        <el-select v-model="queryParams.triggerMode" clearable placeholder="触发方式" class="filter-input">
          <el-option label="手动触发" value="manual" />
          <el-option label="定时触发" value="schedule" />
          <el-option label="依赖触发" value="dependency" />
        </el-select>
        <el-input v-model="queryParams.triggeredBy" placeholder="触发人" clearable class="filter-input" @keyup.enter="handleQuery" />
        <div class="filter-actions">
          <el-button type="primary" :icon="Search" @click="handleQuery">筛选</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="table-card">
      <template #header>
        <div class="table-head">
          <div>
            <h3>执行记录</h3>
            <p>{{ route.query.taskName ? `当前聚焦：${route.query.taskName}` : '查看所有纳管任务实例' }}</p>
          </div>
          <span>共 {{ total }} 条</span>
        </div>
      </template>

        <el-table :data="instanceList" border row-key="taskInstanceId">
          <el-table-column label="任务名称" min-width="300">
            <template #default="{ row }">
              <div class="task-card-cell">
                <strong>{{ row.taskName }}</strong>
                <div class="meta-inline meta-inline-wrap">
                  <span class="mono-text">{{ row.taskCode }}</span>
                  <span class="mono-text">实例 {{ row.instanceId }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="所属模块 / 类型" min-width="190">
            <template #default="{ row }">
              <div class="module-type-cell">
                <div class="meta-inline meta-inline-wrap">
                  <el-tag size="small" effect="plain" :type="sourceModuleTag(row.sourceModule)">
                    {{ sourceModuleLabel(row.sourceModule) }}
                  </el-tag>
                  <el-tag size="small" effect="plain" :type="taskTypeTag(row.taskType)">
                    {{ taskTypeLabel(row.taskType) }}
                  </el-tag>
                </div>
                <span>{{ triggerModeLabel(row.triggerMode) }} · {{ formatTriggeredBy(row.triggeredBy, row.triggerMode) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="执行时间" min-width="220">
            <template #default="{ row }">
              <div class="timeline-cell">
                <div>
                  <span class="meta-label">开始</span>
                  <strong>{{ row.startedAt || row.createTime || '--' }}</strong>
                </div>
                <div>
                  <span class="meta-label">结束</span>
                  <strong>{{ row.finishedAt || '--' }}</strong>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="耗时" width="110" align="center">
            <template #default="{ row }">
              <span>{{ formatDuration(row.durationSeconds) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="执行结果" min-width="260">
            <template #default="{ row }">
              <div class="execution-result-cell">
                <div class="meta-inline meta-inline-wrap">
                  <el-tag :type="executionStatusTag(row.status)">{{ executionStatusLabel(row.status) }}</el-tag>
                  <el-tag size="small" effect="plain" type="info">
                    {{ formatExecutorType(row.executorType) }}
                  </el-tag>
                </div>
                <div class="execution-summary">{{ formatExecutionOutcome(row) }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="执行情况" min-width="220">
            <template #default="{ row }">
              <div class="execution-detail-cell">
                <span v-if="row.errorMessage" class="execution-error-preview">{{ row.errorMessage }}</span>
                <span v-else class="execution-normal-text">无错误信息</span>
                <el-button
                  v-if="row.errorMessage"
                  link
                  type="danger"
                  @click="openErrorDialog(row)"
                >
                  查看完整错误
                </el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openTaskDetail(row.taskId)">查看任务</el-button>
            </template>
          </el-table-column>
      </el-table>

      <pagination
        v-show="total > 0"
        :total="total"
        v-model:page="queryParams.pageNum"
        v-model:limit="queryParams.pageSize"
        @pagination="getList"
      />
    </el-card>

    <el-dialog
      v-model="errorDialogVisible"
      title="执行错误详情"
      width="720px"
      append-to-body
    >
      <el-descriptions :column="2" border class="error-dialog-meta">
        <el-descriptions-item label="任务名称">{{ errorDialog.taskName || '--' }}</el-descriptions-item>
        <el-descriptions-item label="执行结果">{{ executionStatusLabel(errorDialog.status) }}</el-descriptions-item>
        <el-descriptions-item label="所属模块">{{ sourceModuleLabel(errorDialog.sourceModule) }}</el-descriptions-item>
        <el-descriptions-item label="作业类型">{{ taskTypeLabel(errorDialog.taskType) }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ errorDialog.startedAt || errorDialog.createTime || '--' }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ formatDuration(errorDialog.durationSeconds) }}</el-descriptions-item>
      </el-descriptions>
      <pre class="error-dialog-content">{{ errorDialog.errorMessage || '无错误信息' }}</pre>
    </el-dialog>
  </div>
</template>

<script setup name="DataTaskInstances">
import { ArrowLeft, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { listTaskInstances } from '@/api/data/datatask'
import {
  executionStatusLabel,
  executionStatusTag,
  formatDuration,
  formatExecutorType,
  formatExecutionOutcome,
  formatTriggeredBy,
  sourceModuleLabel,
  sourceModuleTag,
  taskTypeLabel,
  taskTypeTag,
  triggerModeLabel,
} from '../taskMeta'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const instanceList = ref([])
const total = ref(0)
const pollTimer = ref(null)
const pageActive = ref(true)
const instanceRequestSerial = ref(0)
const errorDialogVisible = ref(false)
const errorDialog = ref({})
const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  taskId: route.query.taskId || '',
  status: '',
  triggerMode: '',
  triggeredBy: '',
})

function getErrorMessage(error, fallback = '加载执行记录失败') {
  return error?.response?.data?.msg || error?.response?.data?.message || error?.message || fallback
}

function notifyError(error, fallback = '加载执行记录失败') {
  if (error?.__handled) {
    return
  }
  ElMessage.error(getErrorMessage(error, fallback))
}

async function getList(options = {}) {
  const { silent = false } = options
  const requestId = instanceRequestSerial.value + 1
  instanceRequestSerial.value = requestId
  if (!silent) {
    loading.value = true
  }
  try {
    const params = { ...queryParams.value }
    const res = await listTaskInstances(params)
    if (!pageActive.value || requestId !== instanceRequestSerial.value) {
      return
    }
    instanceList.value = res.rows || []
    total.value = res.total || 0
    schedulePolling()
  } catch (error) {
    if (!pageActive.value || requestId !== instanceRequestSerial.value) {
      return
    }
    const shouldRetry = instanceList.value.some(item => ['pending', 'running'].includes(item.status))
    if (!silent) {
      instanceList.value = []
      total.value = 0
    }
    schedulePolling(5000, shouldRetry)
    if (!silent) {
      notifyError(error)
    }
  } finally {
    if (!silent && pageActive.value && requestId === instanceRequestSerial.value) {
      loading.value = false
    }
  }
}

function handleQuery() {
  queryParams.value.pageNum = 1
  stopPolling()
  getList()
}

function resetQuery() {
  queryParams.value = {
    pageNum: 1,
    pageSize: 10,
    taskId: '',
    status: '',
    triggerMode: '',
    triggeredBy: '',
  }
  stopPolling()
  getList()
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
    getList({ silent: true })
  }, delay)
}

function goBack() {
  router.push({ name: 'DataTaskIndex' })
}

function openTaskDetail(taskId) {
  router.push({ name: 'DataTaskDetail', params: { id: taskId } })
}

function openErrorDialog(row) {
  errorDialog.value = { ...row }
  errorDialogVisible.value = true
}

onMounted(() => {
  getList()
})

onBeforeUnmount(() => {
  pageActive.value = false
  stopPolling()
})
</script>

<style scoped>
.task-instance-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card,
.filter-card,
.table-card {
  border-radius: 18px;
}

.hero-layout,
.hero-actions,
.table-head,
.filter-actions,
.meta-inline {
  display: flex;
  gap: 12px;
}

.hero-layout,
.table-head {
  justify-content: space-between;
}

.hero-layout {
  align-items: flex-start;
}

.hero-eyebrow,
.table-head p,
.task-card-cell span,
.module-type-cell span,
.timeline-cell span,
.execution-result-cell span,
.execution-detail-cell span {
  color: var(--el-text-color-secondary);
}

.hero-layout h1,
.table-head h3 {
  margin: 6px 0;
}

.hero-layout p,
.table-head p {
  margin: 0;
  line-height: 1.7;
}

.hero-actions,
.filter-actions {
  flex-wrap: wrap;
}

.filter-layout {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) auto;
  gap: 12px;
  align-items: center;
}

.task-card-cell,
.module-type-cell,
.timeline-cell,
.execution-result-cell,
.execution-detail-cell {
  flex-direction: column;
}

.task-card-cell,
.module-type-cell,
.timeline-cell,
.execution-result-cell,
.execution-detail-cell {
  display: flex;
  gap: 3px;
}

.meta-inline {
  align-items: center;
}

.meta-inline-wrap {
  flex-wrap: wrap;
}

.mono-text {
  font-family: ui-monospace, SFMono-Regular, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 12px;
  word-break: break-all;
}

.timeline-cell strong,
.execution-summary {
  font-weight: 600;
}

.execution-result-cell {
  min-width: 0;
}

.execution-summary,
.execution-error-preview {
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.execution-error-preview {
  color: var(--el-color-danger);
  font-size: 12px;
}

.execution-normal-text {
  font-size: 12px;
}

.error-dialog-meta {
  margin-bottom: 16px;
}

.error-dialog-content {
  margin: 0;
  max-height: 360px;
  overflow: auto;
  padding: 12px;
  border-radius: 12px;
  background: var(--el-fill-color-light);
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.meta-label {
  display: inline-block;
  min-width: 32px;
  margin-right: 8px;
}

@media (max-width: 1200px) {
  .filter-layout {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .hero-layout,
  .table-head {
    flex-direction: column;
  }

  .filter-layout {
    grid-template-columns: 1fr;
  }
}
</style>
