<template>
  <div class="app-container etl-home">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32" color="#409EFF"><Files /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.totalTasks }}</div>
              <div class="stat-label">总任务数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32" color="#67C23A"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.enabledTasks }}</div>
              <div class="stat-label">启用任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32" color="#E6A23C"><VideoPlay /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.todayExecutions }}</div>
              <div class="stat-label">今日执行</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32" color="#F56C6C"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.failedExecutions }}</div>
              <div class="stat-label">失败任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作 -->
    <el-card class="quick-actions-card">
      <template #header>
        <div class="card-header">
          <span>快速操作</span>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card shadow="hover" class="action-card" @click="handleCreateTask('extract')">
            <div class="action-content">
              <el-icon :size="40" color="#409EFF"><Download /></el-icon>
              <div class="action-title">STG采集</div>
              <div class="action-desc">从业务库采集数据到STG层</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="action-card" @click="handleCreateTask('transform')">
            <div class="action-content">
              <el-icon :size="40" color="#67C23A"><MagicStick /></el-icon>
              <div class="action-title">DWD转换</div>
              <div class="action-desc">数据清洗和转换处理</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="action-card" @click="handleCreateTask('load')">
            <div class="action-content">
              <el-icon :size="40" color="#E6A23C"><Upload /></el-icon>
              <div class="action-title">ODS加载</div>
              <div class="action-desc">数据加载到ODS层</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="action-card" @click="handleCreateTask('full')">
            <div class="action-content">
              <el-icon :size="40" color="#F56C6C"><Connection /></el-icon>
              <div class="action-title">全量ETL</div>
              <div class="action-desc">自定义全量数据同步</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 最近任务 -->
    <el-card class="recent-tasks-card">
      <template #header>
        <div class="card-header">
          <span>最近任务</span>
          <el-button text @click="handleViewAllTasks">查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentTasks" stripe border>
        <el-table-column prop="taskName" label="任务名称" min-width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewTask(row)">
              {{ row.taskName }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="etlType" label="ETL类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getEtlTypeColor(row.etlType)" size="small">
              {{ getEtlTypeText(row.etlType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="executorType" label="执行器" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getExecutorTypeText(row.executorType) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '0' ? 'success' : 'danger'" size="small">
              {{ row.status === '0' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updateTime" label="更新时间" width="180" />
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleExecute(row)" :disabled="row.status !== '0'">
              <el-icon><VideoPlay /></el-icon> 执行
            </el-button>
            <el-button link type="primary" @click="handleViewTask(row)">
              <el-icon><View /></el-icon> 查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup name="ETLHome">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Files, CircleCheck, VideoPlay, Warning, Download, MagicStick,
  Upload, Connection, View
} from '@element-plus/icons-vue'
import { listETLTask, executeETLTask } from '@/api/data/etl'

const router = useRouter()

const statistics = reactive({
  totalTasks: 0,
  enabledTasks: 0,
  todayExecutions: 0,
  failedExecutions: 0
})

const recentTasks = ref([])

onMounted(() => {
  loadStatistics()
  loadRecentTasks()
})

async function loadStatistics() {
  try {
    const res = await listETLTask({ pageNum: 1, pageSize: 1000 })
    const tasks = res.rows || []
    statistics.totalTasks = tasks.length
    statistics.enabledTasks = tasks.filter(t => t.status === '0').length

    // TODO: 从执行日志获取今日执行和失败数量
    statistics.todayExecutions = 0
    statistics.failedExecutions = 0
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

async function loadRecentTasks() {
  try {
    const res = await listETLTask({ pageNum: 1, pageSize: 5 })
    recentTasks.value = res.rows || []
  } catch (error) {
    console.error('加载最近任务失败:', error)
  }
}

function handleCreateTask(etlType) {
  router.push({
    name: 'ETLTaskDetail',
    params: { id: 'new' },
    query: { etlType }
  })
}

function handleViewTask(row) {
  router.push({
    name: 'ETLTaskDetail',
    params: { id: row.id }
  })
}

function handleViewAllTasks() {
  router.push({ name: 'ETLTaskList' })
}

async function handleExecute(row) {
  try {
    await executeETLTask(row.id)
    loadRecentTasks()
  } catch (error) {
    console.error('执行任务失败:', error)
  }
}

// 辅助函数
function getEtlTypeColor(etlType) {
  const colors = {
    extract: '',
    transform: 'success',
    load: 'warning',
    full: 'danger'
  }
  return colors[etlType] || ''
}

function getEtlTypeText(etlType) {
  const texts = {
    extract: 'STG采集',
    transform: 'DWD转换',
    load: 'ODS加载',
    full: '全量ETL'
  }
  return texts[etlType] || etlType
}

function getExecutorTypeText(executorType) {
  const texts = {
    mock: '模拟',
    datax: 'DataX',
    spark: 'Spark',
    python: 'Python'
  }
  return texts[executorType] || executorType
}
</script>

<style scoped lang="scss">
.etl-home {
  padding: 20px;

  .stats-cards {
    margin-bottom: 20px;

    .stat-card {
      .stat-content {
        display: flex;
        align-items: center;

        .stat-icon {
          margin-right: 16px;
        }

        .stat-info {
          .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #303133;
            line-height: 1;
          }

          .stat-label {
            margin-top: 8px;
            font-size: 14px;
            color: #909399;
          }
        }
      }
    }
  }

  .quick-actions-card {
    margin-bottom: 20px;

    .action-card {
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-4px);
      }

      .action-content {
        text-align: center;
        padding: 20px 0;

        .action-title {
          margin-top: 12px;
          font-size: 16px;
          font-weight: bold;
          color: #303133;
        }

        .action-desc {
          margin-top: 8px;
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }

  .recent-tasks-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
}
</style>
