<template>
  <div class="app-container">
    <el-form v-if="showSearch" :model="queryParams" ref="queryRef" :inline="true">
      <el-form-item label="任务名称" prop="taskName">
        <el-input v-model="queryParams.taskName" placeholder="请输入任务名称" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="任务类型" prop="taskType">
        <el-select v-model="queryParams.taskType" placeholder="请选择任务类型" clearable style="width: 220px">
          <el-option label="数据库同步到数据库" value="dbToDb" />
          <el-option label="数据库同步到Hive" value="dbToHive" />
          <el-option label="Hive同步到数据库" value="hiveToDb" />
        </el-select>
      </el-form-item>
      <el-form-item label="目标层级" prop="targetLayer">
        <el-select v-model="queryParams.targetLayer" placeholder="请选择目标层级" clearable style="width: 150px">
          <el-option label="STG缓冲层" value="stg" />
          <el-option label="ODS原始层" value="ods" />
          <el-option label="DWD明细层" value="dwd" />
          <el-option label="DWS汇总层" value="dws" />
          <el-option label="ADS应用层" value="ads" />
        </el-select>
      </el-form-item>
      <el-form-item label="执行器" prop="executorType">
        <el-select v-model="queryParams.executorType" placeholder="请选择执行器" clearable style="width: 150px">
          <el-option label="DataX" value="datax" />
          <el-option label="Spark SQL" value="spark_sql" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="任务状态" clearable style="width: 120px">
          <el-option label="正常" value="0" />
          <el-option label="停用" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd">新增任务</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="taskList">
      <el-table-column label="任务名称" prop="taskName" min-width="200" :show-overflow-tooltip="true" />
      <el-table-column label="任务类型" prop="taskType" width="140">
        <template #default="scope">
          <el-tag v-if="scope.row.taskType==='dbToDb'" type="primary">数据库→数据库</el-tag>
          <el-tag v-else-if="scope.row.taskType==='dbToHive'" type="success">数据库→Hive</el-tag>
          <el-tag v-else-if="scope.row.taskType==='hiveToDb'" type="warning">Hive→数据库</el-tag>
          <el-tag v-else type="info">未知</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="目标层级" prop="targetLayer" width="100">
        <template #default="scope">
          <el-tag v-if="scope.row.targetLayer" type="info" size="small">{{ scope.row.targetLayer.toUpperCase() }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="执行器" prop="executorType" width="110">
        <template #default="scope">
          <el-tag v-if="scope.row.executorType==='datax'" type="success" size="small">DataX</el-tag>
          <el-tag v-else-if="scope.row.executorType==='spark_sql'" type="warning" size="small">Spark SQL</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="源数据源" prop="sourceDatasourceName" min-width="150" :show-overflow-tooltip="true" />
      <el-table-column label="源表" prop="sourceTable" min-width="140" :show-overflow-tooltip="true" />
      <el-table-column label="目标数据源" prop="targetDatasourceName" min-width="150" :show-overflow-tooltip="true" />
      <el-table-column label="目标表" prop="targetTable" min-width="140" :show-overflow-tooltip="true" />
      <el-table-column label="多租户采集" prop="isMultiDbTask" width="100" align="center">
        <template #default="scope">
          <el-tag v-if="scope.row.isMultiDbTask" type="warning" size="small">是 ({{ scope.row.sourceDatabases?.length || 0 }}库)</el-tag>
          <el-tag v-else type="info" size="small">否</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" prop="status" width="80" align="center">
        <template #default="scope">
          <el-tag :type="scope.row.status==='0' ? 'success' : 'danger'">{{ scope.row.status==='0' ? '正常' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="createTime" width="160" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="scope">
          <el-button size="small" type="primary" plain icon="VideoPlay" @click="handleExecute(scope.row)">执行</el-button>
          <el-button size="small" type="success" plain icon="List" @click="viewExecutions(scope.row)">日志</el-button>
          <el-dropdown style="margin-left: 5px">
            <el-button size="small" plain icon="More">
              更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item icon="Edit" @click="handleUpdate(scope.row)">编辑</el-dropdown-item>
                <el-dropdown-item icon="DocumentCopy" @click="viewVersions(scope.row)">版本管理</el-dropdown-item>
                <el-dropdown-item icon="Delete" divided @click="handleDelete(scope.row)">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
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

    <!-- 执行日志对话框 -->
    <el-dialog v-model="executionsDialogVisible" title="执行历史" width="900px" append-to-body>
      <el-table v-loading="executionsLoading" :data="executionsList">
        <el-table-column label="执行ID" prop="executionId" width="150" />
        <el-table-column label="状态" prop="status" width="90">
          <template #default="scope">
            <el-tag v-if="scope.row.status==='success'" type="success">成功</el-tag>
            <el-tag v-else-if="scope.row.status==='failed'" type="danger">失败</el-tag>
            <el-tag v-else-if="scope.row.status==='running'" type="warning">运行中</el-tag>
            <el-tag v-else type="info">待执行</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="读取行数" prop="rowsRead" width="100" align="right" />
        <el-table-column label="写入行数" prop="rowsWritten" width="100" align="right" />
        <el-table-column label="耗时(秒)" prop="durationSeconds" width="90" align="right" />
        <el-table-column label="开始时间" prop="startTime" width="160" />
        <el-table-column label="触发方式" prop="triggeredBy" width="90">
          <template #default="scope">
            <el-tag v-if="scope.row.triggeredBy==='manual'" size="small">手动</el-tag>
            <el-tag v-else size="small" type="info">调度</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="scope">
            <el-button link type="primary" size="small" @click="viewExecutionDetail(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <pagination
        v-show="executionsTotal > 0"
        :total="executionsTotal"
        v-model:page="executionsQueryParams.pageNum"
        v-model:limit="executionsQueryParams.pageSize"
        @pagination="getExecutionsList"
      />
    </el-dialog>
  </div>
</template>

<script setup name="DataIntegrationTaskList">
import { listTasks, delTask, executeTask, getTaskExecutions } from '@/api/data/integration'

const router = useRouter()
const { proxy } = getCurrentInstance()

const showSearch = ref(true)
const loading = ref(false)
const total = ref(0)
const taskList = ref([])

// 执行日志对话框
const executionsDialogVisible = ref(false)
const executionsLoading = ref(false)
const executionsList = ref([])
const executionsTotal = ref(0)
const currentTask = ref(null)

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  taskName: '',
  taskType: '',
  targetLayer: '',
  executorType: '',
  status: ''
})

const executionsQueryParams = reactive({
  pageNum: 1,
  pageSize: 10
})

function getList() {
  loading.value = true
  listTasks({ ...queryParams }).then(res => {
    taskList.value = res.rows || []
    total.value = res.total || 0
  }).finally(() => loading.value = false)
}

function handleQuery() {
  queryParams.pageNum = 1
  getList()
}

function resetQuery() {
  queryParams.taskName = ''
  queryParams.taskType = ''
  queryParams.targetLayer = ''
  queryParams.executorType = ''
  queryParams.status = ''
  handleQuery()
}

function handleAdd() {
  router.push({ name: 'DataIntegrationTaskDetail', params: { id: 'new' } })
}

function handleUpdate(row) {
  router.push({ name: 'DataIntegrationTaskDetail', params: { id: row.taskId } })
}

function handleDelete(row) {
  proxy.$modal.confirm(`确认删除任务【${row.taskName}】吗？`).then(() => {
    return delTask(row.taskId)
  }).then(() => {
    proxy.$modal.msgSuccess('删除成功')
    getList()
  }).catch(() => {})
}

function handleExecute(row) {
  proxy.$modal.confirm(`确认立即执行任务【${row.taskName}】吗？`).then(() => {
    return executeTask(row.taskId)
  }).then(res => {
    proxy.$modal.msgSuccess('任务已提交执行')
    // 可以跳转到执行日志页面或刷新当前页
  }).catch(() => {})
}

function viewExecutions(row) {
  currentTask.value = row
  executionsDialogVisible.value = true
  executionsQueryParams.pageNum = 1
  getExecutionsList()
}

function getExecutionsList() {
  if (!currentTask.value) return

  executionsLoading.value = true
  getTaskExecutions(currentTask.value.taskId, executionsQueryParams).then(res => {
    executionsList.value = res.rows || []
    executionsTotal.value = res.total || 0
  }).finally(() => executionsLoading.value = false)
}

function viewExecutionDetail(row) {
  // 跳转到执行日志详情页面，可以后续实现
  router.push({
    name: 'DataIntegrationLogDetail',
    params: { id: row.id }
  })
}

function viewVersions(row) {
  // 跳转到版本管理页面
  router.push({
    name: 'DataIntegrationVersions',
    query: { taskId: row.taskId }
  })
}

onMounted(() => getList())
</script>

<style scoped></style>

