<!-- eslint-disable vue/no-v-model-argument -->
<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <el-form v-if="showSearch" :model="queryParams" ref="queryRef" :inline="true">
      <el-form-item label="任务名称" prop="taskId">
        <el-select v-model="queryParams.taskId" placeholder="请选择任务" clearable filterable style="width: 200px">
          <el-option v-for="task in taskOptions" :key="task.taskId" :label="task.taskName" :value="task.taskId" />
        </el-select>
      </el-form-item>
      <el-form-item label="执行ID" prop="executionId">
        <el-input v-model="queryParams.executionId" placeholder="请输入执行ID" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="执行状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="请选择状态" clearable style="width: 200px">
          <el-option label="等待执行" value="pending" />
          <el-option label="执行中" value="running" />
          <el-option label="执行成功" value="success" />
          <el-option label="执行失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
      </el-form-item>
      <el-form-item label="触发方式" prop="triggerType">
        <el-select v-model="queryParams.triggerType" placeholder="请选择触发方式" clearable style="width: 200px">
          <el-option label="手动触发" value="manual" />
          <el-option label="调度触发" value="schedule" />
          <el-option label="API触发" value="api" />
        </el-select>
      </el-form-item>
      <el-form-item label="执行者" prop="executedBy">
        <el-input v-model="queryParams.executedBy" placeholder="请输入执行者" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 工具栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="success" plain icon="Refresh" @click="handleRefresh">刷新</el-button>
      </el-col>
      <right-toolbar :showSearch="showSearch" @update:showSearch="val => (showSearch = val)" @queryTable="getList" />
    </el-row>

    <!-- 列表 -->
    <el-table v-loading="loading" :data="dataList" border>
      <el-table-column label="执行ID" prop="executionId" width="200" :show-overflow-tooltip="true" />
      <el-table-column label="任务名称" prop="taskName" width="180" :show-overflow-tooltip="true" />
      <el-table-column label="执行状态" prop="status" width="100">
        <template #default="scope">
          <el-tag v-if="scope.row.status === 'pending'" type="info">等待执行</el-tag>
          <el-tag v-else-if="scope.row.status === 'running'" type="warning">执行中</el-tag>
          <el-tag v-else-if="scope.row.status === 'success'" type="success">执行成功</el-tag>
          <el-tag v-else-if="scope.row.status === 'failed'" type="danger">执行失败</el-tag>
          <el-tag v-else-if="scope.row.status === 'cancelled'" type="info">已取消</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="触发方式" prop="triggerType" width="100">
        <template #default="scope">
          <dict-tag :options="trigger_type_options" :value="scope.row.triggerType" />
        </template>
      </el-table-column>
      <el-table-column label="总行数" prop="totalRows" width="100" align="right" />
      <el-table-column label="成功行数" prop="successRows" width="100" align="right">
        <template #default="scope">
          <span style="color: #67C23A">{{ scope.row.successRows || 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column label="失败行数" prop="failedRows" width="100" align="right">
        <template #default="scope">
          <span v-if="scope.row.failedRows > 0" style="color: #F56C6C">{{ scope.row.failedRows }}</span>
          <span v-else>{{ scope.row.failedRows || 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column label="执行时长(秒)" prop="durationSeconds" width="120" align="right" />
      <el-table-column label="开始时间" align="center" prop="startTime" width="180">
        <template #default="scope">
          <span v-if="scope.row.startTime">{{ parseTime(scope.row.startTime) }}</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="结束时间" align="center" prop="endTime" width="180">
        <template #default="scope">
          <span v-if="scope.row.endTime">{{ parseTime(scope.row.endTime) }}</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="执行者" prop="executedBy" width="100" :show-overflow-tooltip="true" />
      <el-table-column label="操作" align="center" width="150" fixed="right">
        <template #default="scope">
          <el-button link size="small" type="primary" icon="View" @click="handleDetail(scope.row)">详情</el-button>
          <el-button v-if="scope.row.status === 'failed'" link size="small" type="danger" icon="Document" @click="handleError(scope.row)">错误</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      v-show="total > 0"
      :total="total"
      :page="queryParams.pageNum"
      :limit="queryParams.pageSize"
      @update:page="val => (queryParams.pageNum = val)"
      @update:limit="val => (queryParams.pageSize = val)"
      @pagination="getList"
    />

    <!-- 执行日志详情弹窗 -->
    <el-dialog title="执行日志详情" v-model="detailOpen" width="900px" append-to-body>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="执行ID">{{ detailData.executionId }}</el-descriptions-item>
        <el-descriptions-item label="任务名称">{{ detailData.taskName }}</el-descriptions-item>
        <el-descriptions-item label="执行状态">
          <el-tag v-if="detailData.status === 'pending'" type="info">等待执行</el-tag>
          <el-tag v-else-if="detailData.status === 'running'" type="warning">执行中</el-tag>
          <el-tag v-else-if="detailData.status === 'success'" type="success">执行成功</el-tag>
          <el-tag v-else-if="detailData.status === 'failed'" type="danger">执行失败</el-tag>
          <el-tag v-else-if="detailData.status === 'cancelled'" type="info">已取消</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="触发方式">
          <dict-tag :options="trigger_type_options" :value="detailData.triggerType" />
        </el-descriptions-item>
        <el-descriptions-item label="总行数">{{ detailData.totalRows || 0 }}</el-descriptions-item>
        <el-descriptions-item label="成功行数">{{ detailData.successRows || 0 }}</el-descriptions-item>
        <el-descriptions-item label="失败行数">{{ detailData.failedRows || 0 }}</el-descriptions-item>
        <el-descriptions-item label="执行时长(秒)">{{ detailData.durationSeconds || 0 }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ detailData.startTime ? parseTime(detailData.startTime) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ detailData.endTime ? parseTime(detailData.endTime) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="执行者">{{ detailData.executedBy || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detailData.createTime }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" v-if="detailData.errorMessage" :span="2">
          <el-alert type="error" :closable="false">{{ detailData.errorMessage }}</el-alert>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailOpen = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 错误信息弹窗 -->
    <el-dialog title="错误信息" v-model="errorOpen" width="700px" append-to-body>
      <el-alert type="error" :closable="false">
        <pre style="white-space: pre-wrap; word-wrap: break-word; margin: 0;">{{ errorMessage }}</pre>
      </el-alert>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="errorOpen = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="ETLExecutionLog">
import { listETLTaskSimple } from '@/api/data/etl'
import { listETLExecutionLog, getETLExecutionLogDetail } from '@/api/data/etl'

const { proxy } = getCurrentInstance()

const dataList = ref([])
const loading = ref(false)
const showSearch = ref(true)
const total = ref(0)
const detailOpen = ref(false)
const errorOpen = ref(false)
const detailData = ref({})
const errorMessage = ref('')
const taskOptions = ref([])

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  taskId: undefined,
  executionId: undefined,
  status: undefined,
  triggerType: undefined,
  executedBy: undefined
})

// 触发方式选项
const trigger_type_options = ref([
  { label: '手动触发', value: 'manual' },
  { label: '调度触发', value: 'schedule' },
  { label: 'API触发', value: 'api' }
])

/** 查询执行日志列表 */
function getList() {
  loading.value = true
  listETLExecutionLog(queryParams.value).then(res => {
    dataList.value = res.rows || []
    total.value = res.total || 0
    loading.value = false
  }).catch(() => {
    loading.value = false
  })
}

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
}

/** 详情按钮操作 */
function handleDetail(row) {
  getETLExecutionLogDetail(row.logId).then(res => {
    detailData.value = res.data
    detailOpen.value = true
  })
}

/** 错误信息按钮操作 */
function handleError(row) {
  errorMessage.value = row.errorMessage || '暂无错误信息'
  errorOpen.value = true
}

/** 刷新按钮操作 */
function handleRefresh() {
  getList()
  proxy.$modal.msgSuccess('刷新成功')
}

/** 获取任务列表（用于下拉框） */
function getTaskList() {
  listETLTaskSimple().then(res => {
    taskOptions.value = res.data || []
  })
}

onMounted(() => {
  getList()
  getTaskList()
})
</script>
