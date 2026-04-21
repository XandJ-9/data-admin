<template>
  <div class="app-container task-instance-page" v-loading="loading">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-layout">
        <div>
          <span class="hero-eyebrow">任务运维实例</span>
          <h1>集中查看数据集成与建模加工任务的执行记录</h1>
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

      <el-table :data="instanceList" border>
        <el-table-column label="任务" min-width="240">
          <template #default="{ row }">
            <div class="task-cell">
              <strong>{{ row.taskName }}</strong>
              <span>{{ row.taskCode }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="实例ID" prop="instanceId" min-width="220" show-overflow-tooltip />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="executionStatusTag(row.status)">{{ executionStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="触发方式" prop="triggerMode" width="110" />
        <el-table-column label="触发人" prop="triggeredBy" width="120" />
        <el-table-column label="执行器" prop="executorType" width="120" />
        <el-table-column label="开始时间" prop="startedAt" width="180" />
        <el-table-column label="结束时间" prop="finishedAt" width="180" />
        <el-table-column label="耗时(s)" prop="durationSeconds" width="100" />
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
  </div>
</template>

<script setup name="DataTaskInstances">
import { ArrowLeft, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { listTaskInstances } from '@/api/data/datatask'
import { executionStatusLabel, executionStatusTag } from './taskMeta'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const instanceList = ref([])
const total = ref(0)
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

async function getList() {
  loading.value = true
  try {
    const params = { ...queryParams.value }
    const res = await listTaskInstances(params)
    instanceList.value = res.rows || []
    total.value = res.total || 0
  } catch (error) {
    instanceList.value = []
    total.value = 0
    notifyError(error)
  } finally {
    loading.value = false
  }
}

function handleQuery() {
  queryParams.value.pageNum = 1
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
  getList()
}

function goBack() {
  router.push({ name: 'DataTaskIndex' })
}

function openTaskDetail(taskId) {
  router.push({ name: 'DataTaskDetail', params: { id: taskId } })
}

onMounted(() => {
  getList()
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
.task-cell {
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
.task-cell span {
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

.task-cell {
  flex-direction: column;
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
