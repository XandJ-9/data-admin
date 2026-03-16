<template>
  <div class="app-container task-execution-list">
    <!-- 顶部操作栏 -->
    <el-row :gutter="16" class="top-actions">
      <el-col :span="18">
        <el-form :inline="true" :model="queryParams" class="query-form">
          <el-form-item label="任务类型">
            <el-select
              v-model="queryParams.taskType"
              placeholder="全部类型"
              clearable
              style="width: 150px"
              @change="handleQuery"
            >
              <el-option label="ETL任务" value="etl" />
              <el-option label="元数据采集" value="metadata_collection" />
              <el-option label="质量检查" value="quality_check" />
              <el-option label="数据同步" value="data_sync" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select
              v-model="queryParams.status"
              placeholder="全部状态"
              clearable
              style="width: 120px"
              @change="handleQuery"
            >
              <el-option label="运行中" value="running" />
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
              <el-option label="已取消" value="cancelled" />
              <el-option label="等待中" value="pending" />
            </el-select>
          </el-form-item>
          <el-form-item label="任务ID">
            <el-input
              v-model="queryParams.taskId"
              placeholder="任务ID"
              clearable
              style="width: 120px"
              @keyup.enter="handleQuery"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleQuery">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetQuery">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </el-col>
      <el-col :span="6" style="text-align: right">
        <el-button @click="autoRefresh = !autoRefresh" :type="autoRefresh ? 'primary' : 'default'">
          <el-icon><Timer /></el-icon>
          {{ autoRefresh ? '自动刷新开启' : '自动刷新关闭' }}
        </el-button>
      </el-col>
    </el-row>

    <!-- 执行记录列表 -->
    <el-table
      v-loading="loading"
      :data="executionList"
      stripe
      border
      style="width: 100%"
    >
      <el-table-column prop="id" label="执行ID" width="80" />

      <el-table-column prop="taskType" label="任务类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getTaskTypeColor(row.taskType)" size="small">
            {{ getTaskTypeLabel(row.taskType) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="taskId" label="任务ID" width="80" />

      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="getExecutionStatusTagType(row.status)" size="small">
            <el-icon v-if="row.status === 'running'" class="is-loading"><Loading /></el-icon>
            {{ getExecutionStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="进度" width="120">
        <template #default="{ row }">
          <el-progress
            :percentage="row.progress || 0"
            :status="row.status === 'success' ? 'success' : row.status === 'failed' ? 'exception' : ''"
            :stroke-width="12"
          />
        </template>
      </el-table-column>

      <el-table-column label="读取/写入" width="150">
        <template #default="{ row }">
          {{ formatNumber(row.rowsRead) }} / {{ formatNumber(row.rowsWritten) }}
        </template>
      </el-table-column>

      <el-table-column prop="durationFormatted" label="执行时长" width="100">
        <template #default="{ row }">
          {{ row.durationFormatted || '-' }}
        </template>
      </el-table-column>

      <el-table-column prop="startTime" label="开始时间" width="160" />

      <el-table-column prop="executorType" label="执行器" width="100">
        <template #default="{ row }">
          {{ row.executorType || '-' }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="180" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleViewLogs(row)">
            <el-icon><Document /></el-icon>
            日志
          </el-button>
          <el-button
            v-if="row.status === 'running'"
            link
            type="danger"
            @click="handleCancel(row)"
          >
            <el-icon><CircleClose /></el-icon>
            取消
          </el-button>
          <el-button
            v-if="row.taskType === 'etl'"
            link
            type="primary"
            @click="handleViewETLDetails(row)"
          >
            <el-icon><View /></el-icon>
            详情
          </el-button>
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

    <!-- 日志对话框 -->
    <el-dialog
      v-model="logsDialogVisible"
      title="执行日志"
      width="900px"
      append-to-body
    >
      <div class="log-content">
        <div v-for="(log, index) in logs" :key="index" class="log-item" :class="`log-${log.level.toLowerCase()}`">
          <span class="log-time">{{ log.timestamp }}</span>
          <span class="log-level">[{{ log.level }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <el-empty v-if="logs.length === 0" description="暂无日志" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup name="TaskExecutionList">
import { ref, reactive, watch, onMounted, onUnmounted } from 'vue'
import {
  Search, Refresh, Timer, Loading, Document, CircleClose, View
} from '@element-plus/icons-vue'
import { listTaskExecutions, getTaskExecutionLogs, cancelExecution, getETLExecutionDetails } from '@/api/taskMonitor'

const loading = ref(false)
const executionList = ref([])
const total = ref(0)
const logsDialogVisible = ref(false)
const logs = ref([])
const autoRefresh = ref(false)

const queryParams = reactive({
  pageNum: 1,
  pageSize: 20,
  taskType: '',
  status: '',
  taskId: ''
})

let refreshTimer = null

onMounted(() => {
  getList()
})

onUnmounted(() => {
  stopAutoRefresh()
})

function getList() {
  loading.value = true
  listTaskExecutions(queryParams).then(res => {
    executionList.value = res.rows || []
    total.value = res.total || 0
  }).finally(() => {
    loading.value = false
  })
}

function handleQuery() {
  queryParams.pageNum = 1
  getList()
}

function resetQuery() {
  queryParams.taskType = ''
  queryParams.status = ''
  queryParams.taskId = ''
  handleQuery()
}

// 自动刷新
watch(autoRefresh, (val) => {
  if (val) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

function startAutoRefresh() {
  refreshTimer = setInterval(() => {
    getList()
  }, 5000) // 每5秒刷新一次
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

async function handleViewLogs(row) {
  logsDialogVisible.value = true
  logs.value = []
  try {
    const res = await getTaskExecutionLogs(row.id, { limit: 200 })
    logs.value = res.rows || []
  } catch (error) {
    console.error('获取日志失败:', error)
  }
}

async function handleCancel(row) {
  try {
    await cancelExecution(row.id)
    await getList()
  } catch (error) {
    console.error('取消执行失败:', error)
  }
}

async function handleViewETLDetails(row) {
  try {
    const res = await getETLExecutionDetails(row.id)
    console.log('ETL详情:', res)
    // TODO: 显示ETL详情对话框
  } catch (error) {
    console.error('获取ETL详情失败:', error)
  }
}

// 辅助函数
function getTaskTypeColor(taskType) {
  const colors = {
    etl: '',
    metadata_collection: 'success',
    quality_check: 'warning',
    data_sync: 'info'
  }
  return colors[taskType] || ''
}

function getTaskTypeLabel(taskType) {
  const labels = {
    etl: 'ETL任务',
    metadata_collection: '元数据采集',
    quality_check: '质量检查',
    data_sync: '数据同步'
  }
  return labels[taskType] || taskType
}

function getExecutionStatusTagType(status) {
  const types = {
    success: 'success',
    failed: 'danger',
    running: 'primary',
    pending: 'info',
    cancelled: 'warning'
  }
  return types[status] || 'info'
}

function getExecutionStatusText(status) {
  const texts = {
    success: '成功',
    failed: '失败',
    running: '运行中',
    pending: '等待中',
    cancelled: '已取消'
  }
  return texts[status] || status
}

function formatNumber(num) {
  if (!num) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}
</script>

<style scoped lang="scss">
.task-execution-list {
  padding: 20px;
}

.top-actions {
  margin-bottom: 16px;
}

.query-form {
  margin: 0;
}

.log-content {
  max-height: 500px;
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
  min-width: 160px;
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

.log-item.log-debug .log-level {
  color: #2196F3;
}

.log-message {
  flex: 1;
  color: #d4d4d4;
}
</style>
