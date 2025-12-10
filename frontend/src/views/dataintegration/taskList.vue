<template>
  <div class="app-container">
    <el-form v-if="showSearch" :model="queryParams" ref="queryRef" :inline="true">
      <el-form-item label="任务名称" prop="taskName">
        <el-input v-model="queryParams.taskName" placeholder="请输入任务名称" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="任务类型" prop="taskType">
        <el-select v-model="queryParams.taskType" placeholder="请选择任务类型" clearable style="width: 200px">
          <el-option label="单表" value="single" />
          <el-option label="分库分表" value="multi" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="createTask('single')">新增单表任务</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="createTask('multi')">新增分库分表任务</el-button>
      </el-col>
    </el-row>

    <el-table v-loading="loading" :data="taskList">
      <el-table-column label="任务名称" prop="taskName" min-width="200" />
      <el-table-column label="任务类型" prop="taskType" width="120">
        <template #default="scope">
          <el-tag type="info" v-if="scope.row.taskType==='single'">单表</el-tag>
          <el-tag type="success" v-else>分库分表</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" prop="status" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status==='0' ? 'success' : 'danger'">{{ scope.row.status==='0' ? '正常' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="createTime" min-width="160" />
      <el-table-column label="更新时间" prop="updateTime" min-width="160" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
          <el-button size="small" type="primary" plain @click="viewDetail(scope.row)">查看</el-button>
          <el-button size="small" type="danger" plain @click="handleDelete(scope.row)">删除</el-button>
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
  </div>
</template>

<script setup>
import { listTasks, delTask } from '@/api/dataintegration'
const router = useRouter()
const { proxy } = getCurrentInstance()

const showSearch = ref(true)
const loading = ref(false)
const total = ref(0)
const taskList = ref([])

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  taskName: '',
  taskType: ''
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
  handleQuery()
}

function viewDetail(row) {
  const type = row.taskType || 'single'
  router.push({ name: 'DataIntegrationTaskDetail', params: { id: row.taskId }, query: { type } })
}

function createTask(type) {
  router.push({ name: 'DataIntegrationTaskDetail', params: { id: 'new' }, query: { type } })
}

function handleDelete(row) {
  proxy.$modal.confirm(`确认删除任务【${row.taskName}】吗？`).then(() => {
    return delTask(row.taskId)
  }).then(() => {
    proxy.$modal.msgSuccess('删除成功')
    getList()
  }).catch(() => {})
}

onMounted(() => getList())
</script>

<style scoped></style>

