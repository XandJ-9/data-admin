<template>
  <div class="app-container etl-task-list">
    <!-- 顶部操作栏 -->
    <el-row :gutter="16" class="top-actions">
      <el-col :span="18">
        <el-form :inline="true" :model="queryParams" class="query-form">
          <el-form-item label="场景">
            <el-select
              v-model="queryParams.scenario"
              placeholder="全部场景"
              clearable
              style="width: 180px"
              @change="handleQuery"
            >
              <el-option label="业务库 → STG层" value="biz_to_stg" />
              <el-option label="STG层 → ODS层" value="stg_to_ods" />
              <el-option label="数仓层计算转换" value="warehouse_transform" />
              <el-option label="数仓层 → 业务库" value="warehouse_to_biz" />
              <el-option label="数据库互相同步" value="db_to_db" />
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
              <el-option label="正常" value="0" />
              <el-option label="停用" value="1" />
            </el-select>
          </el-form-item>
          <el-form-item label="执行方式">
            <el-select
              v-model="queryParams.schedule_type"
              placeholder="全部"
              clearable
              style="width: 120px"
              @change="handleQuery"
            >
              <el-option label="手动执行" value="manual" />
              <el-option label="定时执行" value="scheduled" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="queryParams.keyword"
              placeholder="任务名称"
              clearable
              style="width: 200px"
              @keyup.enter="handleQuery"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
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
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建任务
        </el-button>
      </el-col>
    </el-row>

    <!-- 任务列表 -->
    <el-table
      v-loading="loading"
      :data="taskList"
      stripe
      border
      style="width: 100%"
      @row-click="handleRowClick"
    >
      <el-table-column prop="name" label="任务名称" min-width="200">
        <template #default="{ row }">
          <div class="task-name-cell">
            <el-link type="primary" @click="handleView(row)">
              <strong>{{ row.name }}</strong>
            </el-link>
            <div class="task-meta">
              <el-tag size="small" :type="getScenarioColor(row.scenario)">
                {{ row.scenarioDisplay }}
              </el-tag>
              <span v-if="row.lastExecutionStatus" class="execution-status">
                <el-icon
                  :color="getExecutionStatusColor(row.lastExecutionStatus)"
                  :size="14"
                >
                  <component :is="getExecutionStatusIcon(row.lastExecutionStatus)" />
                </el-icon>
              </span>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="数据流向" min-width="180">
        <template #default="{ row }">
          <div class="data-flow">
            <span class="source">{{ row.sourceDatasourceName || row.sourceTable }}</span>
            <el-icon><Right /></el-icon>
            <span class="target">{{ row.targetDatasourceName || row.targetTable || row.targetLayer }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="同步方式" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.syncMode === 'full' ? 'success' : 'warning'" size="small">
            {{ row.syncModeDisplay }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="执行方式" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.scheduleType === 'manual' ? 'primary' : 'info'" size="small">
            {{ row.scheduleTypeDisplay }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === '0' ? 'success' : 'danger' " size="small">
            {{ row.statusDisplay }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="执行次数" width="90" align="center">
        <template #default="{ row }">
          <el-link type="primary" @click="handleViewExecutions(row)">
            {{ row.executionCount }}次
          </el-link>
        </template>
      </el-table-column>

      <el-table-column label="最后执行" width="160">
        <template #default="{ row }">
          <div v-if="row.lastExecutionTime">
            <div>{{ formatTime(row.lastExecutionTime) }}</div>
            <el-tag
              v-if="row.lastExecutionStatus"
              :type="getExecutionStatusTagType(row.lastExecutionStatus)"
              size="small"
            >
              {{ getExecutionStatusText(row.lastExecutionStatus) }}
            </el-tag>
          </div>
          <span v-else style="color: #909399">从未执行</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="220" align="center" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === '0'"
            link
            type="primary"
            @click.stop="handleExecute(row)"
          >
            <el-icon><VideoPlay /></el-icon>
            执行
          </el-button>
          <el-button link type="primary" @click.stop="handleView(row)">
            <el-icon><View /></el-icon>
            查看
          </el-button>
          <el-button link type="primary" @click.stop="handleEdit(row)">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button
            v-if="row.status === '1'"
            link
            type="success"
            @click.stop="handleEnable(row)"
          >
            启用
          </el-button>
          <el-button
            v-else
            link
            type="warning"
            @click.stop="handleDisable(row)"
          >
            停用
          </el-button>
          <el-popconfirm
            title="确定删除此任务吗?"
            confirm-button-text="确定"
            cancel-button-text="取消"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button link type="danger" @click.stop>
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-popconfirm>
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

    <!-- 执行历史对话框 -->
    <el-dialog
      v-model="executionsDialogVisible"
      title="执行历史"
      width="900px"
      append-to-body
    >
      <el-table :data="executions" stripe border>
        <el-table-column prop="id" label="执行ID" width="80" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getExecutionStatusTagType(row.status)" size="small">
              {{ getExecutionStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="读取/写入" width="150">
          <template #default="{ row }">
            {{ formatNumber(row.rowsRead) }} / {{ formatNumber(row.rowsWritten) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="80">
          <template #default="{ row }">
            {{ row.progress }}%
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="执行时间" min-width="160" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewExecution(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup name="ETLTaskList">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, Refresh, Plus, Right, VideoPlay, View, Edit, Delete,
  CircleCheck, CircleClose, Loading, Clock
} from '@element-plus/icons-vue'
import { listTasks, executeTask, deleteTask, getTaskExecutions, updateTask } from '@/api/data/etl'

const router = useRouter()

const loading = ref(false)
const taskList = ref([])
const total = ref(0)
const executionsDialogVisible = ref(false)
const executions = ref([])

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  scenario: '',
  status: '',
  schedule_type: '',
  keyword: ''
})

onMounted(() => {
  getList()
})

function getList() {
  loading.value = true
  listTasks(queryParams).then(res => {
    taskList.value = res.rows || []
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
  queryParams.scenario = ''
  queryParams.status = ''
  queryParams.schedule_type = ''
  queryParams.keyword = ''
  handleQuery()
}

function handleCreate() {
  router.push({ name: 'ETLTaskSimpleCreate' })
}

function handleView(row) {
  router.push({ name: 'ETLTaskDetail', params: { id: row.id } })
}

function handleEdit(row) {
  router.push({ name: 'ETLTaskDetail', params: { id: row.id } })
}

function handleRowClick(row) {
  handleView(row)
}

async function handleExecute(row) {
  try {
    await executeTask(row.id)
    await getList()
  } catch (error) {
    console.error('执行任务失败:', error)
  }
}

async function handleEnable(row) {
  try {
    await updateTask(row.id, { status: '0' })
    await getList()
  } catch (error) {
    console.error('启用任务失败:', error)
  }
}

async function handleDisable(row) {
  try {
    await updateTask(row.id, { status: '1' })
    await getList()
  } catch (error) {
    console.error('停用任务失败:', error)
  }
}

async function handleDelete(row) {
  try {
    await deleteTask(row.id)
    await getList()
  } catch (error) {
    console.error('删除任务失败:', error)
  }
}

async function handleViewExecutions(row) {
  try {
    const res = await getTaskExecutions(row.id)
    executions.value = res.rows || []
    executionsDialogVisible.value = true
  } catch (error) {
    console.error('获取执行历史失败:', error)
  }
}

function handleViewExecution(row) {
  // 跳转到执行详情页面
  console.log('查看执行详情:', row)
}

// 辅助函数
function getScenarioColor(scenario) {
  const colors = {
    biz_to_stg: '',
    stg_to_ods: 'success',
    warehouse_transform: 'danger',
    warehouse_to_biz: 'warning',
    db_to_db: 'info'
  }
  return colors[scenario] || ''
}

function getExecutionStatusIcon(status) {
  const icons = {
    success: CircleCheck,
    failed: CircleClose,
    running: Loading,
    pending: Clock
  }
  return icons[status] || Clock
}

function getExecutionStatusColor(status) {
  const colors = {
    success: '#67C23A',
    failed: '#F56C6C',
    running: '#409EFF',
    pending: '#909399'
  }
  return colors[status] || '#909399'
}

function getExecutionStatusTagType(status) {
  const types = {
    success: 'success',
    failed: 'danger',
    running: 'primary',
    pending: 'info'
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

function formatTime(time) {
  if (!time) return '-'
  const date = new Date(time)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString()
}

function formatNumber(num) {
  if (!num) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

function formatDuration(seconds) {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}小时${minutes}分`
}
</script>

<style scoped lang="scss">
.etl-task-list {
  padding: 20px;
}

.top-actions {
  margin-bottom: 16px;
}

.query-form {
  margin: 0;
}

.task-name-cell {
  .task-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 4px;
  }

  .execution-status {
    display: flex;
    align-items: center;
  }
}

.data-flow {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;

  .source, .target {
    max-width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
