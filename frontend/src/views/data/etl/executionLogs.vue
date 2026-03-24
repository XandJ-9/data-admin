<template>
  <div class="app-container etl-execution-logs">
    <!-- 查询表单 -->
    <el-form :model="queryParams" :inline="true" class="query-form">
      <el-form-item label="任务ID">
        <el-select
          v-model="queryParams.taskId"
          placeholder="全部任务"
          clearable
          filterable
          style="width: 200px"
        >
          <el-option
            v-for="task in taskList"
            :key="task.id"
            :label="task.taskName"
            :value="task.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="执行状态">
        <el-select
          v-model="queryParams.status"
          placeholder="全部状态"
          clearable
          style="width: 120px"
        >
          <el-option label="等待执行" value="pending" />
          <el-option label="执行中" value="running" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
      </el-form-item>
      <el-form-item label="执行者">
        <el-input
          v-model="queryParams.executedBy"
          placeholder="请输入执行者"
          clearable
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item label="执行时间">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 240px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 统计信息 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-statistic title="总执行次数" :value="statistics.total" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="成功次数" :value="statistics.success">
          <template #suffix>
            <span style="color: #67C23A">({{ statistics.successRate }}%)</span>
          </template>
        </el-statistic>
      </el-col>
      <el-col :span="6">
        <el-statistic title="失败次数" :value="statistics.failed">
          <template #suffix>
            <span style="color: #F56C6C">({{ statistics.failedRate }}%)</span>
          </template>
        </el-statistic>
      </el-col>
      <el-col :span="6">
        <el-statistic title="平均耗时" :value="statistics.avgDuration" suffix="秒" />
      </el-col>
    </el-row>

    <!-- 日志列表 -->
    <el-table
      v-loading="loading"
      :data="logList"
      stripe
      border
      style="margin-top: 16px"
    >
      <el-table-column prop="logId" label="日志ID" width="80" align="center" />
      <el-table-column prop="taskName" label="任务名称" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          <el-link type="primary" @click="handleViewTask(row)">
            {{ row.taskName }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="taskCode" label="任务编码" width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getExecutionStatusColor(row.status)" size="small">
            {{ getExecutionStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="读取/写入" width="140" align="center">
        <template #default="{ row }">
          <span>{{ formatNumber(row.totalRows) }} / {{ formatNumber(row.successRows) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="durationSeconds" label="耗时" width="90" align="center">
        <template #default="{ row }">
          {{ formatDuration(row.durationSeconds) }}
        </template>
      </el-table-column>
      <el-table-column prop="startTime" label="开始时间" width="160" />
      <el-table-column prop="endTime" label="结束时间" width="160" />
      <el-table-column prop="executedBy" label="执行者" width="100" />
      <el-table-column label="操作" width="150" align="center" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            icon="View"
            @click="handleViewDetail(row)"
          >详情</el-button>
          <el-button
            v-if="row.status === 'running'"
            link
            type="danger"
            icon="VideoPause"
            @click="handleCancel(row)"
          >取消</el-button>
          <el-button
            v-if="row.status === 'failed'"
            link
            type="warning"
            icon="Refresh"
            @click="handleRetry(row)"
          >重试</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 执行详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="执行详情"
      width="1000px"
      append-to-body
    >
      <el-tabs v-model="detailActiveTab">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="日志ID">{{ currentDetail.logId }}</el-descriptions-item>
            <el-descriptions-item label="任务名称">{{ currentDetail.taskName }}</el-descriptions-item>
            <el-descriptions-item label="任务编码">{{ currentDetail.taskCode }}</el-descriptions-item>
            <el-descriptions-item label="执行状态">
              <el-tag :type="getExecutionStatusColor(currentDetail.status)">
                {{ getExecutionStatusText(currentDetail.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="总行数">{{ formatNumber(currentDetail.totalRows) }}</el-descriptions-item>
            <el-descriptions-item label="成功行数">{{ formatNumber(currentDetail.successRows) }}</el-descriptions-item>
            <el-descriptions-item label="失败行数">{{ formatNumber(currentDetail.failedRows) }}</el-descriptions-item>
            <el-descriptions-item label="执行耗时">{{ formatDuration(currentDetail.durationSeconds) }}</el-descriptions-item>
            <el-descriptions-item label="开始时间">{{ currentDetail.startTime }}</el-descriptions-item>
            <el-descriptions-item label="结束时间">{{ currentDetail.endTime }}</el-descriptions-item>
            <el-descriptions-item label="执行者">{{ currentDetail.executedBy }}</el-descriptions-item>
            <el-descriptions-item label="触发方式">{{ currentDetail.triggerType || '-' }}</el-descriptions-item>
            <el-descriptions-item label="错误信息" :span="2">
              <span v-if="currentDetail.errorMessage" style="color: #F56C6C">
                {{ currentDetail.errorMessage }}
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <!-- 执行日志 -->
        <el-tab-pane label="执行日志" name="logs">
          <div class="log-container">
            <pre class="log-content">{{ currentDetail.logFile || '暂无日志' }}</pre>
          </div>
        </el-tab-pane>

        <!-- 执行参数 -->
        <el-tab-pane label="执行参数" name="params">
          <div class="json-container">
            <pre class="json-content">{{ currentDetail.executorParams ? JSON.stringify(currentDetail.executorParams, null, 2) : '暂无参数' }}</pre>
          </div>
        </el-tab-pane>

        <!-- 质检结果 -->
        <el-tab-pane label="质检结果" name="quality">
          <el-table :data="currentDetail.qualityResults || []" border stripe>
            <el-table-column prop="ruleName" label="规则名称" min-width="150" />
            <el-table-column prop="ruleType" label="规则类型" width="100" />
            <el-table-column prop="checkedCount" label="检查数量" width="100" align="center" />
            <el-table-column prop="failedCount" label="失败数量" width="100" align="center" />
            <el-table-column prop="passedRate" label="通过率" width="100" align="center" />
            <el-table-column prop="status" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'passed' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'passed' ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="errorMessage" label="错误信息" min-width="200" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <!-- 执行进度 -->
        <el-tab-pane label="执行进度" name="progress">
          <div v-if="currentDetail.status === 'running' || currentDetail.status === 'success'" class="progress-container">
            <el-progress
              :percentage="currentDetail.progress"
              :status="currentDetail.status === 'running' ? undefined : 'success'"
            />
            <div class="progress-info">
              <p>总行数：{{ formatNumber(currentDetail.totalRows) }}</p>
              <p>成功行数：{{ formatNumber(currentDetail.successRows) }}</p>
              <p>失败行数：{{ formatNumber(currentDetail.failedRows) }}</p>
            </div>
          </div>
          <el-empty v-else description="暂无进度信息" />
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup name="ETLExecutionLogs">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  listETLExecutionLog,
  getETLExecutionLogDetail,
  getExecutionLogStatistics,
  cancelETLExecution,
  executeETLTask
} from '@/api/data/etl'
import { listETLTaskSimple } from '@/api/data/etl'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const logList = ref([])
const total = ref(0)
const taskList = ref([])
const dateRange = ref([])
const detailDialogVisible = ref(false)
const detailActiveTab = ref('basic')
const currentDetail = ref({})

const statistics = reactive({
  total: 0,
  success: 0,
  successRate: 0,
  failed: 0,
  failedRate: 0,
  avgDuration: 0
})

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  taskId: '',
  status: '',
  executedBy: '',
  startTime: '',
  endTime: ''
})

onMounted(() => {
  loadTaskList()
  getList()
  loadStatistics()
})

async function loadTaskList() {
  try {
    const res = await listETLTaskSimple()
    taskList.value = res.data || []
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

async function getList() {
  loading.value = true

  // 处理日期范围
  if (dateRange.value && dateRange.value.length === 2) {
    queryParams.startTime = dateRange.value[0]
    queryParams.endTime = dateRange.value[1]
  } else {
    queryParams.startTime = ''
    queryParams.endTime = ''
  }

  try {
    const res = await listETLExecutionLog(queryParams)
    logList.value = res.rows || []
    total.value = res.total || 0
  } catch (error) {
    console.error('加载执行日志失败:', error)
  } finally {
    loading.value = false
  }
}

async function loadStatistics() {
  try {
    const res = await getExecutionLogStatistics()
    const data = res.data || {}
    statistics.total = data.total || 0
    statistics.success = data.success || 0
    statistics.failed = data.failed || 0
    statistics.successRate = data.successRate || 0
    statistics.failedRate = data.failedRate || 0
    statistics.avgDuration = data.avgDuration || 0
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

function handleQuery() {
  queryParams.pageNum = 1
  getList()
}

function resetQuery() {
  queryParams.taskId = ''
  queryParams.status = ''
  queryParams.executedBy = ''
  dateRange.value = []
  handleQuery()
}

function handleViewTask(row) {
  router.push({
    name: 'ETLTaskDetail',
    params: { id: row.taskId }
  })
}

async function handleViewDetail(row) {
  try {
    const res = await getETLExecutionLogDetail(row.logId)
    currentDetail.value = res.data
    detailDialogVisible.value = true
  } catch (error) {
    console.error('加载执行详情失败:', error)
  }
}

async function handleCancel(row) {
  try {
    await ElMessageBox.confirm('确认要取消该执行吗？', '提示', {
      type: 'warning'
    })
    await cancelETLExecution(row.logId)
    ElMessage.success('已取消执行')
    getList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消执行失败:', error)
    }
  }
}

async function handleRetry(row) {
  try {
    await ElMessageBox.confirm('确认要重新执行该任务吗？', '提示', {
      type: 'warning'
    })
    await executeETLTask(row.taskId)
    ElMessage.success('任务已重新提交执行')
    getList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重试失败:', error)
    }
  }
}

// 辅助函数
function getExecutionStatusText(status) {
  const texts = {
    pending: '等待执行',
    running: '执行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

function getExecutionStatusColor(status) {
  const colors = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    cancelled: ''
  }
  return colors[status] || ''
}

function formatNumber(num) {
  if (!num) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}


function formatDuration(seconds) {
  if (!seconds) return '0秒'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}
</script>

<style scoped lang="scss">
.etl-execution-logs {
  .query-form {
    margin-bottom: 16px;
  }

  .stats-row {
    margin-bottom: 16px;
    padding: 16px;
    background: #fff;
    border-radius: 4px;
  }

  .log-container,
  .json-container {
    max-height: 500px;
    overflow-y: auto;
    background: #f5f5f5;
    padding: 16px;
    border-radius: 4px;

    .log-content,
    .json-content {
      margin: 0;
      white-space: pre-wrap;
      word-wrap: break-word;
      font-family: 'Courier New', Courier, monospace;
      font-size: 13px;
      line-height: 1.5;
    }
  }

  .progress-container {
    padding: 20px;

    .progress-info {
      margin-top: 20px;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;

      p {
        margin: 0;
        font-size: 14px;
        color: #606266;
      }
    }
  }
}
</style>
