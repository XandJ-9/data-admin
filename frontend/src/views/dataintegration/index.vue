<template>
  <div class="app-container">
    <el-page-header @back="goTaskList" content="数据集成首页" />

    <el-row :gutter="20" style="margin-top: 10px;">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>数据库 → 数据库</template>
          <div>支持单表、整库、分库分表同步；用于不同数据库之间的数据迁移与集成。</div>
          <div style="margin-top: 12px; display:flex; gap:8px; flex-wrap:wrap;">
            <el-button type="primary" @click="createTask('dbToDb')">创建任务</el-button>
            <!-- <el-button type="primary" @click="createTask('dbToDb','single')">新建单表任务</el-button>
            <el-button type="primary" @click="createTask('dbToDb','full')">新建整库任务</el-button>
            <el-button type="primary" @click="createTask('dbToDb','sharded')">新建分库分表任务</el-button> -->
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>数据库 → 集群</template>
          <div>将数据库数据同步到 Hive 等分布式存储，便于数据湖或数仓建设。</div>
          <div style="margin-top: 12px; display:flex; gap:8px; flex-wrap:wrap;">
            <el-button type="primary" @click="createTask('dbToCluster')">创建任务</el-button>
            <!-- <el-button type="primary" @click="createTask('dbToCluster','single')">新建单表任务</el-button>
            <el-button type="primary" @click="createTask('dbToCluster','full')">新建整库任务</el-button> -->
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>集群 → 数据库</template>
          <div>将 Hive 等集群数据同步到数据库（如 MySQL），用于数据回流与应用查询。</div>
          <div style="margin-top: 12px; display:flex; gap:8px; flex-wrap:wrap;">
            <el-button type="primary" @click="createTask('clusterToDb')">创建任务</el-button>
            <!-- <el-button type="primary" @click="createTask('clusterToDb','single')">新建单表任务</el-button>
            <el-button type="primary" @click="createTask('clusterToDb','full')">新建整库任务</el-button> -->
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-divider />
    <div style="display:flex; justify-content: space-between; align-items:center;">
      <h3 style="margin:0;">同步任务列表</h3>
      <div>
        <el-button type="primary" @click="createTask('dbToDb','single')">快速新建任务</el-button>
        <el-button @click="goTaskList">打开列表页</el-button>
      </div>
    </div>

    <el-table :data="tasks" style="width:100%; margin-top:10px;" border>
      <el-table-column prop="syncTypeLabel" label="同步类型" min-width="150" />
      <el-table-column prop="name" label="任务名称" min-width="140" />
      <el-table-column prop="scope" label="范围" min-width="120" />
      <el-table-column prop="mode" label="方式" min-width="90" />
      <el-table-column prop="frequency" label="频率" min-width="140" />
      <el-table-column prop="status" label="状态" min-width="90" />
      <el-table-column label="操作" width="240">
        <template #default="scope">
          <el-button link size="small" type="primary" @click="viewTask(scope.row)">详情</el-button>
          <el-button link size="small" type="success" @click="startTask(scope.row)">启动</el-button>
          <el-button link size="small" type="warning" @click="pauseTask(scope.row)">暂停</el-button>
          <el-button link size="small" type="danger" @click="deleteTask(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
  
</template>

<script setup name="DataIntegrationHome">
import { useRouter } from 'vue-router'

const router = useRouter()

function goTaskList() {
  router.push('/dataintegration/tasks')
}

function createTask(syncType, scope) {
  const q = {}
  if (syncType) q.syncType = syncType
  if (scope) q.scope = scope
  router.push({ path: '/dataintegration/task/new', query: q })
}

function viewTask(row) {
  router.push({ path: `/dataintegration/task/${row.id}` })
}

const tasks = ref([])

function loadTasks() {
  try {
    const raw = localStorage.getItem('di_tasks')
    const arr = raw ? JSON.parse(raw) : []
    tasks.value = arr.map(addLabels)
  } catch (e) {
    tasks.value = []
  }
  // 如果没有数据，造一些样例
  if (!tasks.value || tasks.value.length === 0) {
    const samples = [
      { id: 1, name: 'DB→DB 单表-用户', syncType: 'dbToDb', scope: 'single', mode: 'incremental', frequency: '手动', status: 'paused' },
      { id: 2, name: 'DB→Cluster 整库-CRM', syncType: 'dbToCluster', scope: 'full', mode: 'full', frequency: '0 */6 * * *', status: 'running' },
      { id: 3, name: 'Cluster→DB 单表-事件', syncType: 'clusterToDb', scope: 'single', mode: 'incremental', frequency: '0 0 * * *', status: 'paused' }
    ]
    tasks.value = samples.map(addLabels)
    localStorage.setItem('di_tasks', JSON.stringify(tasks.value))
  }
}

function persist() {
  localStorage.setItem('di_tasks', JSON.stringify(tasks.value))
}

function startTask(row) {
  row.status = 'running'
  persist()
}

function pauseTask(row) {
  row.status = 'paused'
  persist()
}

function deleteTask(row) {
  tasks.value = tasks.value.filter(t => t.id !== row.id)
  persist()
}

onMounted(loadTasks)

function addLabels(t) {
  return {
    ...t,
    syncTypeLabel: t.syncType === 'dbToDb' ? '数据库 → 数据库'
      : t.syncType === 'dbToCluster' ? '数据库 → 集群'
      : t.syncType === 'clusterToDb' ? '集群 → 数据库'
      : '未知',
  }
}
</script>

<style scoped>
</style>