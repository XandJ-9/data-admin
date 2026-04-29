import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import {
  addTask,
  executeTask,
  getExecutionLogDetail,
  getSupportedExecutors,
  getTask,
  getTaskExecutions,
  publishTask,
  updateTask,
  validateTask,
} from '@/api/data/integration'
import { listDatasource } from '@/api/data/datasource'
import { STATUS_OPTIONS, buildDefaultTargetTableName } from './taskViewMeta'

function createDefaultForm() {
  return {
    taskId: null,
    taskName: '',
    taskCode: '',
    sourceDataSourceId: null,
    sourceDatabaseName: '',
    sourceTableName: '',
    targetDataSourceId: null,
    targetSchemaName: 'ods',
    targetTableName: '',
    loadType: 'full',
    writeMode: 'overwrite',
    executorType: 'mock',
    status: 'active',
    scheduleType: 'manual',
    cronExpression: '',
    owner: '',
    taskConfigText: '{}',
    remark: '',
  }
}

function mapTaskToForm(task) {
  return {
    taskId: task.taskId,
    taskName: task.taskName,
    taskCode: task.taskCode,
    sourceDataSourceId: task.sourceDataSourceId,
    sourceDatabaseName: task.sourceDatabaseName || '',
    sourceTableName: task.sourceTableName || '',
    targetDataSourceId: task.targetDataSourceId,
    targetSchemaName: task.targetSchemaName || '',
    targetTableName: task.targetTableName,
    loadType: task.loadType,
    writeMode: task.writeMode,
    executorType: task.executorType,
    status: task.status,
    scheduleType: task.scheduleType,
    cronExpression: task.cronExpression || '',
    owner: task.owner || '',
    taskConfigText: JSON.stringify(task.taskConfig || {}, null, 2),
    remark: task.remark || '',
  }
}

function getErrorMessage(error, fallback = '请求失败，请稍后重试') {
  return error?.response?.data?.msg || error?.response?.data?.message || error?.message || fallback
}

function notifyError(error, fallback) {
  if (error?.__handled) {
    return
  }
  ElMessage.error(getErrorMessage(error, fallback))
}

async function loadAllRows(loadPage, extraParams = {}) {
  const pageSize = 100
  let pageNum = 1
  let rows = []
  let total = 0

  do {
    const res = await loadPage({ ...extraParams, pageNum, pageSize })
    const currentRows = res.rows || []
    rows = rows.concat(currentRows)
    total = Number(res.total || 0)
    if (!currentRows.length || currentRows.length < pageSize) {
      break
    }
    pageNum += 1
  } while (!total || rows.length < total)

  return rows
}

export function useIntegrationTaskForm() {
  const route = useRoute()
  const router = useRouter()

  const loading = ref(false)
  const submitting = ref(false)
  const publishing = ref(false)
  const validating = ref(false)
  const executionLoading = ref(false)
  const executionDialogVisible = ref(false)
  const executionDetailVisible = ref(false)
  const executionList = ref([])
  const executionTotal = ref(0)
  const selectedExecution = ref(null)
  const dataSourceOptions = ref([])
  const formRef = ref()
  const form = ref(createDefaultForm())
  const taskSnapshot = ref(null)
  const autoFilledTargetTable = ref(true)
  let executionListRequestToken = 0
  let executionDetailRequestToken = 0

  const executionQueryParams = ref({
    pageNum: 1,
    pageSize: 10,
  })

  const rules = {
    taskName: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
    taskCode: [{ required: true, message: '请输入任务编码', trigger: 'blur' }],
    sourceDataSourceId: [{ required: true, message: '请选择源数据源', trigger: 'change' }],
    sourceTableName: [{ required: true, message: '请输入源表名', trigger: 'blur' }],
    targetDataSourceId: [{ required: true, message: '请选择目标数据源', trigger: 'change' }],
    targetTableName: [{ required: true, message: '请输入目标表名', trigger: 'blur' }],
    scheduleType: [{ required: true, message: '请选择调度方式', trigger: 'change' }],
    cronExpression: [{
      validator: (rule, value, callback) => {
        if (form.value.scheduleType === 'cron' && !value) {
          callback(new Error('请输入 Cron 表达式'))
          return
        }
        callback()
      },
      trigger: 'blur',
    }],
  }

  const supportedExecutors = getSupportedExecutors().map(item => ({
    ...item,
    disabled: false,
  }))

  const isEditMode = computed(() => Boolean(route.params.taskId))
  const pageTitle = computed(() => isEditMode.value ? '集成任务详情' : '新建集成任务')
  const currentExecutorHint = computed(() => {
    return supportedExecutors.find(item => item.value === form.value.executorType)?.description || ''
  })

  async function loadDataSources() {
    try {
      dataSourceOptions.value = await loadAllRows(params => listDatasource(params))
    } catch (error) {
      dataSourceOptions.value = []
      notifyError(error, '加载数据源失败')
    }
  }

  function syncTargetTableFromSourceTable() {
    const currentTableName = String(form.value.sourceTableName || '').trim()
    if (!currentTableName || !autoFilledTargetTable.value) {
      return
    }
    form.value.targetTableName = buildDefaultTargetTableName(currentTableName, form.value.targetSchemaName)
  }

  async function loadTask() {
    if (!isEditMode.value) {
      taskSnapshot.value = null
      form.value = createDefaultForm()
      autoFilledTargetTable.value = true
      formRef.value?.clearValidate()
      return
    }
    loading.value = true
    try {
      const res = await getTask(route.params.taskId)
      taskSnapshot.value = res.data
      form.value = mapTaskToForm(res.data)
      autoFilledTargetTable.value = false
      formRef.value?.clearValidate()
    } catch (error) {
      notifyError(error, '加载任务详情失败')
    } finally {
      loading.value = false
    }
  }

  function handleSourceDataSourceChange() {
    form.value.sourceDatabaseName = ''
    form.value.sourceTableName = ''
    form.value.targetTableName = ''
    autoFilledTargetTable.value = true
  }

  function handleSourceTableInput() {
    autoFilledTargetTable.value = true
    syncTargetTableFromSourceTable()
  }

  function handleTargetTableInput() {
    autoFilledTargetTable.value = false
  }

  function buildPayload() {
    const taskConfig = form.value.taskConfigText?.trim() ? JSON.parse(form.value.taskConfigText) : {}
    return {
      taskId: form.value.taskId,
      taskName: form.value.taskName,
      taskCode: form.value.taskCode,
      sourceDataSourceId: form.value.sourceDataSourceId,
      sourceDatabaseName: form.value.sourceDatabaseName,
      sourceTableName: form.value.sourceTableName,
      targetDataSourceId: form.value.targetDataSourceId,
      targetSchemaName: form.value.targetSchemaName,
      targetTableName: form.value.targetTableName,
      loadType: form.value.loadType,
      writeMode: form.value.writeMode,
      executorType: form.value.executorType,
      scheduleType: form.value.scheduleType,
      cronExpression: form.value.scheduleType === 'cron' ? form.value.cronExpression : '',
      owner: form.value.owner,
      taskConfig,
      remark: form.value.remark,
    }
  }

  async function handleValidate() {
    try {
      await formRef.value?.validate()
      validating.value = true
      await validateTask(buildPayload())
      ElMessage.success('校验通过')
    } catch (error) {
      if (error instanceof SyntaxError) {
        ElMessage.error('任务配置必须是合法 JSON')
      } else if (error instanceof Error && !error.__handled) {
        ElMessage.error(error.message)
      }
    } finally {
      validating.value = false
    }
  }

  async function submitForm() {
    try {
      await formRef.value?.validate()
      const payload = buildPayload()
      submitting.value = true
      let res
      if (form.value.taskId) {
        const updatePayload = { ...payload, status: form.value.status }
        delete updatePayload.taskCode
        res = await updateTask(updatePayload)
      } else {
        const createPayload = { ...payload }
        delete createPayload.taskId
        res = await addTask(createPayload)
      }
      taskSnapshot.value = res.data
      const successMessage = taskSnapshot.value?.publishedToTaskOps
        ? '保存成功，请重新发布到任务中心后使调度变更生效'
        : '保存成功，需要纳入调度时请手动点击发布'
      ElMessage.success(successMessage)
      if (!form.value.taskId && res.data?.taskId) {
        await router.replace({ name: 'DataIntegrationTaskDetail', params: { taskId: res.data.taskId }, query: route.query })
        return
      }
      form.value = mapTaskToForm(res.data)
      autoFilledTargetTable.value = false
    } catch (error) {
      if (error instanceof SyntaxError) {
        ElMessage.error('任务配置必须是合法 JSON')
      } else if (error?.response || error instanceof Error) {
        notifyError(error, '保存任务失败')
      }
    } finally {
      submitting.value = false
    }
  }

  async function handleExecute() {
    if (!taskSnapshot.value?.taskId) {
      return
    }
    try {
      await ElMessageBox.confirm(`确认立即执行任务「${taskSnapshot.value.taskName}」吗？`, '提示', { type: 'warning' })
    } catch {
      return
    }
    try {
      await executeTask(taskSnapshot.value.taskId)
      ElMessage.success('执行已完成')
      openExecutionDialog()
    } catch (error) {
      notifyError(error, '执行任务失败')
    }
  }

  async function handlePublish() {
    if (!taskSnapshot.value?.taskId) {
      return
    }
    try {
      await ElMessageBox.confirm(`确认将任务「${taskSnapshot.value.taskName}」发布到任务中心吗？`, '提示', { type: 'warning' })
    } catch {
      return
    }
    try {
      publishing.value = true
      const res = await publishTask(taskSnapshot.value.taskId)
      taskSnapshot.value = res.data
      form.value = mapTaskToForm(res.data)
      autoFilledTargetTable.value = false
      ElMessage.success('发布成功，任务中心将按已发布快照参与调度')
    } catch (error) {
      notifyError(error, '发布任务失败')
    } finally {
      publishing.value = false
    }
  }

  function openExecutionDialog() {
    executionDialogVisible.value = true
    executionDetailVisible.value = false
    selectedExecution.value = null
    executionList.value = []
    executionTotal.value = 0
    executionQueryParams.value.pageNum = 1
    loadExecutions()
  }

  async function loadExecutions() {
    if (!taskSnapshot.value?.taskId) {
      executionList.value = []
      executionTotal.value = 0
      return
    }
    const requestTaskId = taskSnapshot.value.taskId
    const currentToken = ++executionListRequestToken
    executionLoading.value = true
    selectedExecution.value = null
    try {
      const res = await getTaskExecutions(requestTaskId, executionQueryParams.value)
      if (currentToken !== executionListRequestToken || taskSnapshot.value?.taskId !== requestTaskId) {
        return
      }
      executionList.value = res.rows || []
      executionTotal.value = res.total || 0
    } catch (error) {
      if (currentToken === executionListRequestToken && taskSnapshot.value?.taskId === requestTaskId) {
        executionList.value = []
        executionTotal.value = 0
        notifyError(error, '加载执行记录失败')
      }
    } finally {
      if (currentToken === executionListRequestToken) {
        executionLoading.value = false
      }
    }
  }

  async function openExecutionDetail(row) {
    const currentToken = ++executionDetailRequestToken
    selectedExecution.value = null
    executionDetailVisible.value = true
    try {
      const res = await getExecutionLogDetail(row.taskInstanceId)
      if (currentToken !== executionDetailRequestToken) {
        return
      }
      selectedExecution.value = res.data
    } catch (error) {
      if (currentToken === executionDetailRequestToken) {
        executionDetailVisible.value = false
        notifyError(error, '加载执行详情失败')
      }
    }
  }

  function goBack() {
    if (route.query.from === 'task-detail' && route.query.returnTaskId) {
      router.push({ name: 'DataTaskDetail', params: { id: route.query.returnTaskId } })
      return
    }
    if (route.query.from === 'task-center') {
      router.push({ name: 'DataTaskIndex' })
      return
    }
    if (route.query.from === 'integration-home') {
      router.push({ name: 'DataIntegrationHome' })
      return
    }
    if (route.query.from === 'integration-task-list') {
      router.push({ name: 'DataIntegrationTask' })
      return
    }
    if (route.query.view === 'overview') {
      router.push({ name: 'DataIntegrationHome' })
      return
    }
    router.push({
      name: 'DataIntegrationTask',
    })
  }

  watch(() => form.value.targetSchemaName, () => {
    syncTargetTableFromSourceTable()
  })

  watch(
    () => route.params.taskId,
    () => {
      loadTask()
    }
  )

  onMounted(async () => {
    await loadDataSources()
    await loadTask()
  })

  return {
    STATUS_OPTIONS,
    currentExecutorHint,
    dataSourceOptions,
    executionDetailVisible,
    executionDialogVisible,
    executionList,
    executionLoading,
    executionQueryParams,
    executionTotal,
    form,
    formRef,
    goBack,
    handleExecute,
    handlePublish,
    handleSourceDataSourceChange,
    handleSourceTableInput,
    handleTargetTableInput,
    handleValidate,
    isEditMode,
    loadExecutions,
    loading,
    openExecutionDetail,
    openExecutionDialog,
    pageTitle,
    publishing,
    rules,
    selectedExecution,
    submitting,
    supportedExecutors,
    submitForm,
    taskSnapshot,
    validating,
  }
}
