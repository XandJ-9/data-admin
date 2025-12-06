<template>
  <div class="app-container">
    <div style="display:flex; justify-content: space-between; align-items:center;">
      <h3 style="margin:0;">同步任务列表</h3>
      <div>
        <el-button type="primary" @click="newTask">新增同步任务</el-button>
        <el-button @click="goHome">返回首页</el-button>
      </div>
    </div>

    <el-table :data="tasks" style="width:100%; margin-top:10px;" border>
      <el-table-column prop="syncTypeLabel" label="同步类型" min-width="160" />
      <el-table-column prop="name" label="任务名称" min-width="160" />
      <el-table-column prop="scope" label="范围" min-width="120" />
      <el-table-column prop="mode" label="方式" min-width="100" />
      <el-table-column prop="frequency" label="频率" min-width="160" />
      <el-table-column prop="sourceBrief" label="源" min-width="200" />
      <el-table-column prop="targetBrief" label="目标" min-width="200" />
      <el-table-column prop="status" label="状态" min-width="100" />
      <el-table-column label="操作" width="260">
        <template #default="scope">
          <el-button link size="small" type="primary" @click="viewTask(scope.row)">详情</el-button>
          <el-button link size="small" type="success" @click="startTask(scope.row)">启动</el-button>
          <el-button link size="small" type="warning" @click="pauseTask(scope.row)">暂停</el-button>
          <el-button link size="small" type="danger" @click="deleteTask(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="tasks.length > 0" :total="tasks.length" :page="pageNum" :limit="pageSize" @update:page="val => pageNum = val" @update:limit="val => pageSize = val" />
  </div>
</template>

<script setup name="DataIntegrationTaskList">
import { useRouter } from 'vue-router'

const router = useRouter()
const pageNum = ref(1)
const pageSize = ref(10)
const tasks = ref([])

function goHome() { router.push('/dataintegration') }
function newTask() { router.push('/dataintegration/task/new') }
function viewTask(row) { router.push(`/dataintegration/task/${row.id}`) }

function loadTasks() {
  try {
    const raw = localStorage.getItem('di_tasks')
    const arr = raw ? JSON.parse(raw) : []
    tasks.value = arr.map(addLabels)
  } catch (e) {
    tasks.value = []
  }
  if (!tasks.value || tasks.value.length === 0) {
    const samples = [
      { id: 1, name: 'DB→DB 单表-用户', syncType: 'dbToDb', scope: 'single', mode: 'incremental', frequency: '手动', status: 'paused', sourceBrief: 'MySQL_A.sales', targetBrief: 'Postgres_B.analytics' },
      { id: 2, name: 'DB→Cluster 整库-CRM', syncType: 'dbToCluster', scope: 'full', mode: 'full', frequency: '0 */6 * * *', status: 'running', sourceBrief: 'MySQL_A.crm', targetBrief: 'Hive_1.warehouse' },
      { id: 3, name: 'Cluster→DB 单表-事件', syncType: 'clusterToDb', scope: 'single', mode: 'incremental', frequency: '0 0 * * *', status: 'paused', sourceBrief: 'Hive_1.default.events', targetBrief: 'MySQL_A.logs' }
    ]
    tasks.value = samples.map(addLabels)
    localStorage.setItem('di_tasks', JSON.stringify(tasks.value))
  }
}

function persist() { localStorage.setItem('di_tasks', JSON.stringify(tasks.value)) }
function startTask(row) { row.status = 'running'; persist() }
function pauseTask(row) { row.status = 'paused'; persist() }
function deleteTask(row) { tasks.value = tasks.value.filter(t => t.id !== row.id); persist() }

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