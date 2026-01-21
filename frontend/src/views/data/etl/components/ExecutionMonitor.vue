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
              <div class="stat-value">{{ execution.duration }} <span class="unit">秒</span></div>
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
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Download, Upload, Timer, Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'

const props = defineProps({
  taskId: {
    type: String,
    required: true
  },
  executionId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['back', 'view-task'])

const execution = reactive({
  status: 'running', // running, success, failed
  progress: 0,
  currentStage: '初始化中...',
  estimatedTime: '计算中...',
  rowsRead: 0,
  rowsWritten: 0,
  duration: 0,
  logs: []
})

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
  try {
    // TODO: 调用后端API获取执行状态
    // const res = await getTaskExecutionLog(props.taskId, props.executionId)
    // 更新状态

    // 模拟进度更新（实际应该从后端获取）
    if (execution.status === 'running') {
      execution.progress = Math.min(execution.progress + 5, 100)
      execution.rowsRead = execution.progress * 1000
      execution.rowsWritten = execution.progress * 980
      execution.duration += 3

      if (execution.progress >= 100) {
        execution.status = 'success'
        stopMonitoring()
      }
    }
  } catch (error) {
    console.error('刷新执行状态失败:', error)
  }
}

async function refreshLog() {
  await refreshStatus()
}

function stopExecution() {
  // TODO: 调用后端API停止执行
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
    pending: '等待中'
  }
  return statusMap[execution.status] || '未知'
})

function getStatusIcon(status) {
  const iconMap = {
    running: Loading,
    success: CircleCheck,
    failed: CircleClose,
    pending: Timer
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
