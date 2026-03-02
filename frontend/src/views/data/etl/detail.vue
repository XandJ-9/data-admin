<!-- eslint-disable vue/no-v-model-argument -->
<template>
  <div class="app-container task-detail-container">
    <!-- 页面头部 -->
    <el-page-header @back="handleBack" class="page-header">
      <template #content>
        <div class="page-header-content">
          <span class="title">{{ pageTitle }}</span>
          <el-tag :type="form.taskType === 'data_integration' ? 'success' : 'primary'" class="ml-2">
            {{ getTaskTypeLabel(form.taskType) }}
          </el-tag>
          <el-tag v-if="form.taskId" type="info" class="ml-2">
            {{ form.status === '0' ? '启用' : '停用' }}
          </el-tag>
        </div>
      </template>
      <template #extra>
        <div class="page-header-extra">
          <el-button v-if="form.taskId" type="primary" icon="VideoPlay" @click="handleExecute" :loading="executing">
            执行任务
          </el-button>
          <el-button type="success" icon="Check" @click="submitForm" :loading="submitting">
            保存
          </el-button>
          <el-button icon="Close" @click="handleBack">取消</el-button>
        </div>
      </template>
    </el-page-header>

    <!-- 表单内容 -->
    <el-card shadow="never" class="form-card">
      <el-form ref="taskFormRef" :model="form" :rules="rules" label-width="140px">
        <TaskForm
          ref="taskFormContentRef"
          v-model="form"
          :datasource-options="datasourceOptions"
          :source-table-options="sourceTableOptions"
          :target-table-options="targetTableOptions"
          :status-options="sys_normal_disable"
          @source-datasource-change="handleSourceDatasourceChange"
          @target-datasource-change="handleTargetDatasourceChange"
        />
      </el-form>
    </el-card>
  </div>
</template>

<script setup name="ETLTaskDetail">
import { getCurrentInstance, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TaskForm from './components/TaskForm.vue'
import { listDatasource, listMetaTables } from '@/api/data/asset'
import {
  getETLTask,
  addETLTask,
  updateETLTask,
  executeETLTask
} from '@/api/data/etl'

const { proxy } = getCurrentInstance()
const route = useRoute()
const router = useRouter()

const form = ref({})
const taskFormRef = ref(null)
const submitting = ref(false)
const executing = ref(false)

const datasourceOptions = ref([])
const sourceTableOptions = ref([])
const targetTableOptions = ref([])

const { sys_normal_disable } = proxy.useDict('sys_normal_disable')

// 页面标题
const pageTitle = computed(() => {
  return form.value.taskId ? '编辑ETL任务' : '新增ETL任务'
})

// 表单验证规则
const rules = ref({
  taskName: [
    { required: true, message: '任务名称不能为空', trigger: 'blur' }
  ],
  taskCode: [
    { required: true, message: '任务编码不能为空', trigger: 'blur' }
  ],
  taskType: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ],
  executeStrategy: [
    { required: true, message: '请选择执行策略', trigger: 'change' }
  ],
  sourceDatasourceId: [
    { required: true, message: '请选择源数据源', trigger: 'change' }
  ],
  targetDatasourceId: [
    { required: true, message: '请选择目标数据源', trigger: 'change' }
  ],
  sourceTableId: [
    { required: true, message: '请选择源表', trigger: 'change' }
  ],
  targetTable: [
    { required: true, message: '请输入目标表', trigger: 'blur' }
  ]
})

/** 获取数据源列表 */
function getDatasourceList() {
  listDatasource().then(res => {
    datasourceOptions.value = res.rows || []
  })
}

/** 处理源数据源变化 */
function handleSourceDatasourceChange(datasourceId) {
  if (datasourceId) {
    listMetaTables({ dataSourceId: datasourceId }).then(res => {
      sourceTableOptions.value = res.rows || []
    })
  } else {
    sourceTableOptions.value = []
  }
}

/** 处理目标数据源变化 */
function handleTargetDatasourceChange(datasourceId) {
  if (datasourceId) {
    listMetaTables({ dataSourceId: datasourceId }).then(res => {
      targetTableOptions.value = res.rows || []
    })
  } else {
    targetTableOptions.value = []
  }
}

/** 获取任务类型标签 */
function getTaskTypeLabel(taskType) {
  const labelMap = {
    'data_integration': '数据集成',
    'sql_task': 'SQL任务'
  }
  return labelMap[taskType] || taskType
}

/** 返回列表页 */
function handleBack() {
  router.push('/data-etl/task')
}

/** 提交表单 */
function submitForm() {
  taskFormRef.value?.validate().then(valid => {
    if (valid) {
      submitting.value = true
      if (form.value.taskId) {
        updateETLTask(form.value).then(() => {
          proxy.$modal.msgSuccess('修改成功')
          handleBack()
        }).finally(() => {
          submitting.value = false
        })
      } else {
        addETLTask(form.value).then(() => {
          proxy.$modal.msgSuccess('新增成功')
          handleBack()
        }).finally(() => {
          submitting.value = false
        })
      }
    }
  })
}

/** 执行任务 */
function handleExecute() {
  proxy.$modal.confirm('确认要执行该任务吗？').then(() => {
    executing.value = true
    return executeETLTask(form.value.taskId)
  }).then(() => {
    proxy.$modal.msgSuccess('任务执行成功，请查看执行日志')
  }).finally(() => {
    executing.value = false
  })
}

/** 初始化表单数据 */
function initForm() {
  const taskId = route.params.id
  if (taskId) {
    // 编辑模式：加载任务详情
    getETLTask(taskId).then(res => {
      form.value = res.data
      // 如果有源数据源，加载源表列表
      if (form.value.sourceDatasourceId) {
        handleSourceDatasourceChange(form.value.sourceDatasourceId)
      }
      // 如果有目标数据源，加载目标表列表
      if (form.value.targetDatasourceId) {
        handleTargetDatasourceChange(form.value.targetDatasourceId)
      }
    })
  } else {
    // 新增模式：初始化空表单
    form.value = {
      taskId: undefined,
      taskName: undefined,
      taskCode: undefined,
      description: undefined,
      taskType: undefined,
      executorType: undefined,
      executeStrategy: 'full',
      sourceDatasourceId: undefined,
      targetDatasourceId: undefined,
      sourceTableId: undefined,
      targetTable: undefined,
      sqlConfig: undefined,
      executorParams: undefined,
      status: '0',
      remark: undefined
    }
  }
}

onMounted(() => {
  getDatasourceList()
  initForm()
})
</script>

<style scoped lang="scss">
.task-detail-container {
  padding: 20px;
}

.page-header {
  background: #fff;
  padding: 16px 20px;
  border-radius: 4px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

  .page-header-content {
    display: flex;
    align-items: center;

    .title {
      font-size: 18px;
      font-weight: 500;
      color: #303133;
    }

    .ml-2 {
      margin-left: 8px;
    }
  }

  .page-header-extra {
    display: flex;
    gap: 8px;
  }
}

.form-card {
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

  :deep(.el-card__body) {
    padding: 20px;
  }
}
</style>
