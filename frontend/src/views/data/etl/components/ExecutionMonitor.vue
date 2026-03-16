<template>
  <div class="execution-monitor">
    <el-card>
      <template #header>
        <div class="monitor-header">
          <span>执行监控</span>
          <div class="header-actions">
            <el-button v-if="execution.status === 'running'" type="danger" size="small" @click="stopExecution">
              停止任务
            </el-button>
            <el-button size="small" @click="refreshStatus">刷新</el-button>
          </div>
        </div>
      </template>

      <!-- 状态卡片 -->
      <el-row :gutter="24" class="status-cards">
        <el-col :span="6">
          <div class="stat-card" :class="`status-${execution.status}`">
            <div class="stat-icon">
              <el-icon :size="32">
                <component :is="getStatusIcon(execution.status)" />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">当前状态</div>
              <div class="stat-value">{{ statusText }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon :size="32"><Download /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">已读取</div>
              <div class="stat-value">{{ formatNumber(execution.rowsRead) }} <span class="unit">行</span></div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon :size="32"><Upload /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">已写入</div>
              <div class="stat-value">{{ formatNumber(execution.rowsWritten) }} <span class="unit">行</span></div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon :size="32"><Timer /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">运行时长</div>
              <div class="stat-value">{{ execution.durationFormatted || execution.duration + '秒' }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 进度条 -->
      <div v-if="execution.status === 'running'" class="progress-section">
        <div class="progress-header">
          <span class="progress-label">同步进度</span>
          <span class="progress-value">{{ execution.progress }}%</span>
        </div>
        <el-progress
          :percentage="execution.progress"
          :status="execution.status"
          :stroke-width="20"
        />
        <div class="progress-detail">
          <span>{{ execution.currentStage }}</span>
          <span>预计剩余：{{ execution.estimatedTime }}</span>
        </div>
      </div>

      <!-- 执行日志 -->
      <div class="log-section">
        <div class="log-header">
          <span>执行日志</span>
          <el-button size="small" @click="refreshLog">刷新日志</el-button>
        </div>
        <div class="log-content">
          <div v-for="(log, index) in execution.logs" :key="index" class="log-item" :class="`log-${log.level}`">
            <span class="log-time">{{ log.timestamp }}</span>
            <span class="log-level">{{ log.level }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
          <el-empty v-if="execution.logs.length === 0" description="暂无日志" />
        </div>
      </div>

      <!-- 底部操作按钮 -->
      <div class="footer-actions">
        <el-button v-if="execution.status === 'success'" type="primary" @click="$emit('view-task')">
          查看任务详情
        </el-button>
        <el-button v-if="execution.status !== 'running'" @click="$emit('back')">
          返回任务列表
        </el-button>
        <el-button v-else @click="$emit('back')">
          在后台运行
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { Download, Upload, Timer, Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { getTaskExecution, getTaskExecutionLogs, cancelExecution } from '@/api/taskMonitor'

const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  },
  executionId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['back', 'view-task'])

const execution = reactive({
  status: 'running', // running, success, failed, cancelled
  progress: 0,
  currentStage: '初始化中...',
  estimatedTime: '计算中...',
  rowsRead: 0,
  rowsWritten: 0,
  duration: 0,
  durationFormatted: '',
  logs: []
})

const loading = ref(false)
const logLoading = ref(false)

let refreshTimer = null

onMounted(() => {
  startMonitoring()
})

onUnmounted(() => {
  stopMonitoring()
})

function startMonitoring() {
  refreshStatus()
  refreshTimer = setInterval(refreshStatus, 3000) // 每3秒刷新一次
}

function stopMonitoring() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

async function refreshStatus() {
  if (loading.value) return

  loading.value = true
  try {
    const res = await getTaskExecution(props.executionId)

    // 更新执行状态
    execution.status = res.status || 'running'
    execution.progress = res.progress || 0
    execution.rowsRead = res.rowsRead || 0
    execution.rowsWritten = res.rowsWritten || 0
    execution.duration = res.durationSeconds || 0
    execution.durationFormatted = res.durationFormatted || '0秒'

    // 如果任务已完成，停止轮询
    if (['success', 'failed', 'cancelled'].includes(execution.status)) {
      stopMonitoring()
      // 加载完整日志
      await refreshLog()
    }
  } catch (error) {
    console.error('刷新执行状态失败:', error)
  } finally {
    loading.value = false
  }
}

async function refreshLog() {
  if (logLoading.value) return

  logLoading.value = true
  try {
    const res = await getTaskExecutionLogs(props.executionId, { limit: 100 })
    execution.logs = (res.rows || []).map(log => ({
      timestamp: log.timestamp,
      level: log.logLevel || 'INFO',
      message: log.message
    }))
  } catch (error) {
    console.error('刷新执行日志失败:', error)
  } finally {
    logLoading.value = false
  }
}

async function stopExecution() {
  try {
    await cancelExecution(props.executionId)
    await refreshStatus()
  } catch (error) {
    console.error('停止执行失败:', error)
  }
}

function formatNumber(num) {
  if (!num) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const statusText = computed(() => {
  const statusMap = {
    running: '运行中',
    success: '执行成功',
    failed: '执行失败',
    pending: '等待中',
    cancelled: '已取消'
  }
  return statusMap[execution.status] || '未知'
})

function getStatusIcon(status) {
  const iconMap = {
    running: Loading,
    success: CircleCheck,
    failed: CircleClose,
    pending: Timer,
    cancelled: CircleClose
  }
  return iconMap[status] || Timer
}
</script>

<style scoped>
.execution-monitor {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.status-cards {
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 8px;
  border: 1px solid #ebeef5;
  transition: all 0.3s;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-card.status-running {
  background: linear-gradient(135deg, #e6f7ff 0%, #ffffff 100%);
  border-color: #409EFF;
}

.stat-card.status-success {
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
  border-color: #67C23A;
}

.stat-card.status-failed {
  background: linear-gradient(135deg, #fef0f0 0%, #ffffff 100%);
  border-color: #F56C6C;
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: #fff;
  color: #409EFF;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-value .unit {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
  margin-left: 4px;
}

.progress-section {
  margin-bottom: 24px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.progress-value {
  font-size: 16px;
  font-weight: 600;
  color: #409EFF;
}

.progress-detail {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
}

.log-section {
  margin-bottom: 24px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.log-content {
  max-height: 300px;
  overflow-y: auto;
  background-color: #1e1e1e;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.log-item {
  display: flex;
  gap: 8px;
  line-height: 1.6;
  color: #d4d4d4;
}

.log-time {
  color: #858585;
  min-width: 140px;
}

.log-level {
  min-width: 60px;
  font-weight: 600;
}

.log-item.log-info .log-level {
  color: #4CAF50;
}

.log-item.log-warn .log-level {
  color: #FFC107;
}

.log-item.log-error .log-level {
  color: #F44336;
}

.log-message {
  flex: 1;
  color: #d4d4d4;
}

.footer-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
</style>
