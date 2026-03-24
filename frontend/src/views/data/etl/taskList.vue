<template>
  <div class="app-container etl-task-list">
    <!-- 查询表单 -->
    <el-form :model="queryParams" :inline="true" class="query-form">
      <el-form-item label="任务名称">
        <el-input
          v-model="queryParams.taskName"
          placeholder="请输入任务名称"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="任务编码">
        <el-input
          v-model="queryParams.taskCode"
          placeholder="请输入任务编码"
          clearable
          style="width: 180px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="ETL类型">
        <el-select
          v-model="queryParams.etlType"
          placeholder="全部类型"
          clearable
          style="width: 140px"
        >
          <el-option label="STG采集" value="extract" />
          <el-option label="DWD转换" value="transform" />
          <el-option label="ODS加载" value="load" />
          <el-option label="全量ETL" value="full" />
        </el-select>
      </el-form-item>
      <el-form-item label="执行器类型">
        <el-select
          v-model="queryParams.executorType"
          placeholder="全部"
          clearable
          style="width: 120px"
        >
          <el-option label="模拟执行器" value="mock" />
          <el-option label="DataX" value="datax" />
          <el-option label="Spark SQL" value="spark" />
          <el-option label="Python脚本" value="python" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select
          v-model="queryParams.status"
          placeholder="全部状态"
          clearable
          style="width: 100px"
        >
          <el-option label="启用" value="0" />
          <el-option label="停用" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 操作栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          icon="Plus"
          @click="handleCreate"
        >新增任务</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="success"
          icon="VideoPlay"
          :disabled="selectedIds.length !== 1"
          @click="handleBatchExecute"
        >执行</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          icon="Delete"
          :disabled="selectedIds.length === 0"
          @click="handleBatchDelete"
        >删除</el-button>
      </el-col>
      <right-toolbar @queryTable="getList" />
    </el-row>

    <!-- 任务列表 -->
    <el-table
      v-loading="loading"
      :data="taskList"
      stripe
      border
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column prop="taskName" label="任务名称" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          <el-link type="primary" @click="handleView(row)">
            {{ row.taskName }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="taskCode" label="任务编码" width="140" show-overflow-tooltip />
      <el-table-column prop="etlType" label="ETL类型" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getEtlTypeColor(row.etlType)" size="small">
            {{ getEtlTypeText(row.etlType) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="executorType" label="执行器" width="100" align="center">
        <template #default="{ row }">
          <el-tag size="small">{{ getExecutorTypeText(row.executorType) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="executeStrategy" label="执行策略" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.executeStrategy === 'full' ? 'success' : 'warning'" size="small">
            {{ row.executeStrategy === 'full' ? '全量' : '增量' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="数据源" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="datasource-info">
            <div class="source">{{ row.sourceDatasourceName }}</div>
            <el-icon><Right /></el-icon>
            <div class="target">{{ row.targetDatasourceName }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === '0' ? 'success' : 'danger'" size="small">
            {{ row.status === '0' ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" width="160" />
      <el-table-column label="操作" width="280" align="center" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            icon="VideoPlay"
            @click="handleExecute(row)"
            :disabled="row.status !== '0'"
          >执行</el-button>
          <el-button
            link
            type="primary"
            icon="View"
            @click="handleView(row)"
          >查看</el-button>
          <el-button
            link
            type="primary"
            icon="Edit"
            @click="handleEdit(row)"
          >编辑</el-button>
          <el-button
            link
            type="primary"
            icon="CopyDocument"
            @click="handleClone(row)"
          >克隆</el-button>
          <el-button
            link
            type="danger"
            icon="Delete"
            @click="handleDelete(row)"
          >删除</el-button>
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

    <!-- 克隆对话框 -->
    <el-dialog
      v-model="cloneDialogVisible"
      title="克隆任务"
      width="500px"
      append-to-body
    >
      <el-form :model="cloneForm" :rules="cloneRules" ref="cloneFormRef" label-width="100px">
        <el-form-item label="新任务名称" prop="taskName">
          <el-input v-model="cloneForm.taskName" placeholder="请输入新任务名称" />
        </el-form-item>
        <el-form-item label="新任务编码" prop="taskCode">
          <el-input v-model="cloneForm.taskCode" placeholder="请输入新任务编码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cloneDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmClone">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="ETLTaskList">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Right } from '@element-plus/icons-vue'
import {
  listETLTask,
  delETLTask,
  executeETLTask,
  cloneETLTask
} from '@/api/data/etl'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const taskList = ref([])
const total = ref(0)
const selectedIds = ref([])
const cloneDialogVisible = ref(false)
const cloneFormRef = ref()

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  taskName: '',
  taskCode: '',
  etlType: '',
  executorType: '',
  status: ''
})

const cloneForm = reactive({
  taskId: null,
  taskName: '',
  taskCode: ''
})

const cloneRules = {
  taskName: [
    { required: true, message: '请输入任务名称', trigger: 'blur' }
  ],
  taskCode: [
    { required: true, message: '请输入任务编码', trigger: 'blur' }
  ]
}

onMounted(() => {
  getList()
})

function getList() {
  loading.value = true
  listETLTask(queryParams).then(res => {
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
  queryParams.taskName = ''
  queryParams.taskCode = ''
  queryParams.etlType = ''
  queryParams.executorType = ''
  queryParams.status = ''
  handleQuery()
}

function handleSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.taskId)
}

function handleCreate() {
  router.push({ name: 'ETLTaskDetail', params: { id: 'new' } })
}

function handleView(row) {
  router.push({ name: 'ETLTaskDetail', params: { id: row.taskId } })
}

function handleEdit(row) {
  router.push({ name: 'ETLTaskDetail', params: { id: row.taskId } })
}

async function handleExecute(row) {
  try {
    await ElMessageBox.confirm('确认要执行该任务吗？', '提示', {
      type: 'warning'
    })
    await executeETLTask(row.taskId)
    ElMessage.success('任务已提交执行')
    getList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('执行任务失败:', error)
    }
  }
}

function handleClone(row) {
  cloneForm.taskId = row.taskId
  cloneForm.taskName = `${row.taskName} - 副本`
  cloneForm.taskCode = `${row.taskCode}_copy`
  cloneDialogVisible.value = true
}

async function handleConfirmClone() {
  try {
    await cloneFormRef.value.validate()
    await cloneETLTask(cloneForm.taskId, {
      taskName: cloneForm.taskName,
      taskCode: cloneForm.taskCode
    })
    ElMessage.success('克隆成功')
    cloneDialogVisible.value = false
    getList()
  } catch (error) {
    console.error('克隆任务失败:', error)
  }
}

async function handleBatchExecute() {
  if (selectedIds.value.length !== 1) {
    ElMessage.warning('请选择一个任务执行')
    return
  }
  try {
    await ElMessageBox.confirm('确认要执行选中的任务吗？', '提示', {
      type: 'warning'
    })
    await executeETLTask(selectedIds.value[0])
    ElMessage.success('任务已提交执行')
    getList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('执行任务失败:', error)
    }
  }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确认要删除选中的 ${selectedIds.value.length} 个任务吗？`, '警告', {
      type: 'warning'
    })
    await delETLTask(selectedIds.value.join(','))
    ElMessage.success('删除成功')
    getList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
    }
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确认要删除该任务吗？删除后不可恢复！', '警告', {
      type: 'warning'
    })
    await delETLTask(row.taskId)
    ElMessage.success('删除成功')
    getList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
    }
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
.etl-task-list {
  .query-form {
    margin-bottom: 16px;
  }

  .mb8 {
    margin-bottom: 8px;
  }

  .datasource-info {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;

    .source, .target {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}
</style>
