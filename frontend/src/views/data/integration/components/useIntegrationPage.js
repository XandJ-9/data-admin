import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import {
  delTask,
  executeTask,
  getExecutionLogDetail,
  getSupportedExecutors,
  getTaskExecutions,
  listTasks,
} from '@/api/data/integration'
import { STATUS_OPTIONS } from './taskViewMeta'

export function useIntegrationPage(pageKey = 'task') {
  const route = useRoute()
  const router = useRouter()
  const loading = ref(false)
  const taskList = ref([])
  const total = ref(0)
  const detailOpen = ref(false)
  const detailTab = ref('config')
  const previewLoading = ref(false)
  const executionLoading = ref(false)
  const executionDialogVisible = ref(false)
  const executionDetailVisible = ref(false)
  const previewExecutions = ref([])
  const executionDialogList = ref([])
  const executionTotal = ref(0)
  const selectedTask = ref(null)
  const selectedExecution = ref(null)
  let executionPreviewRequestToken = 0
  let executionListRequestToken = 0
  let executionDetailRequestToken = 0
  let taskListRequestToken = 0

  const queryParams = ref({
    pageNum: 1,
    pageSize: pageKey === 'overview' ? 6 : 10,
    taskName: '',
    status: '',
    executorType: '',
  })

  const executionQueryParams = ref({
    pageNum: 1,
    pageSize: 10,
  })

  const supportedExecutors = getSupportedExecutors().map(item => ({
    ...item,
    disabled: false,
  }))

  const executorOptions = supportedExecutors.map(item => ({
    label: item.label,
    value: item.value,
  }))

  const sampleTaskCount = computed(() => taskList.value.length)
  const focusTasks = computed(() => taskList.value.slice(0, 5))

  const activeTaskCount = computed(() => taskList.value.filter(item => item.status === 'active').length)
  const cronTaskCount = computed(() => taskList.value.filter(item => item.scheduleType === 'cron').length)

  function getErrorMessage(error, fallback = '请求失败，请稍后重试') {
    return error?.response?.data?.msg || error?.response?.data?.message || error?.message || fallback
  }

  function notifyError(error, fallback) {
    if (error?.__handled) {
      return
    }
    ElMessage.error(getErrorMessage(error, fallback))
  }

  function syncSelectedTask() {
    const currentId = selectedTask.value?.taskId
    if (!currentId) {
      return
    }
    selectedTask.value = taskList.value.find(item => item.taskId === currentId) || null
    if (!selectedTask.value) {
      detailOpen.value = false
      previewExecutions.value = []
      return
    }
    if (detailOpen.value && detailTab.value === 'runtime') {
      loadExecutionPreview()
    }
  }

  async function getList() {
    const currentToken = ++taskListRequestToken
    loading.value = true
    try {
      const res = await listTasks(queryParams.value)
      if (currentToken !== taskListRequestToken) {
        return
      }
      taskList.value = res.rows || []
      total.value = res.total || 0
      syncSelectedTask()
    } catch (error) {
      if (currentToken === taskListRequestToken) {
        taskList.value = []
        total.value = 0
        selectedTask.value = null
        detailOpen.value = false
        previewExecutions.value = []
        notifyError(error, '加载任务列表失败')
      }
    } finally {
      if (currentToken === taskListRequestToken) {
        loading.value = false
      }
    }
  }

  function handleQuery() {
    queryParams.value.pageNum = 1
    getList()
  }

  function resetQuery() {
    queryParams.value = { pageNum: 1, pageSize: pageKey === 'overview' ? 6 : 10, taskName: '', status: '', executorType: '' }
    getList()
  }

  function openTaskDetail(task) {
    selectedTask.value = task
    detailTab.value = 'config'
    detailOpen.value = true
  }

  function resolvePageFrom() {
    return pageKey === 'overview' ? 'integration-home' : 'integration-task-list'
  }

  function goToTaskList() {
    router.push({ name: 'DataIntegrationTask' })
  }

  function goToOverview() {
    router.push({ name: 'DataIntegrationHome' })
  }

  function handleAdd() {
    router.push({ name: 'DataIntegrationTaskCreate', query: { from: resolvePageFrom() } })
  }

  function handleUpdate(row) {
    const targetTask = row || selectedTask.value
    if (!targetTask?.taskId) {
      return
    }
    router.push({
      name: 'DataIntegrationTaskDetail',
      params: { taskId: targetTask.taskId },
      query: { from: resolvePageFrom() },
    })
  }

  async function handleDelete(row) {
    const taskId = row?.taskId || selectedTask.value?.taskId
    if (!taskId) {
      return
    }
    const taskName = row?.taskName || selectedTask.value?.taskName || '所选任务'
    try {
      await ElMessageBox.confirm(`确认删除任务「${taskName}」吗？`, '提示', { type: 'warning' })
    } catch {
      return
    }
    try {
      await delTask(taskId)
      ElMessage.success('删除成功')
      if (selectedTask.value?.taskId === taskId) {
        detailOpen.value = false
      }
      getList()
    } catch (error) {
      notifyError(error, '删除任务失败')
    }
  }

  async function handleExecute(row) {
    try {
      await ElMessageBox.confirm(`确认立即执行任务「${row.taskName}」吗？`, '提示', { type: 'warning' })
    } catch {
      return
    }
    try {
      await executeTask(row.taskId)
      ElMessage.success('执行已完成')
      selectedTask.value = row
      executionQueryParams.value.pageNum = 1
      if (detailOpen.value && detailTab.value === 'runtime') {
        loadExecutionPreview()
      }
      openExecutionDialog(row)
      getList()
    } catch (error) {
      notifyError(error, '执行任务失败')
    }
  }

  async function loadExecutionPreview() {
    if (!selectedTask.value) {
      previewExecutions.value = []
      return
    }
    const requestTaskId = selectedTask.value.taskId
    const currentToken = ++executionPreviewRequestToken
    previewLoading.value = true
    try {
      const res = await getTaskExecutions(requestTaskId, { pageNum: 1, pageSize: 5 })
      if (currentToken !== executionPreviewRequestToken || selectedTask.value?.taskId !== requestTaskId) {
        return
      }
      previewExecutions.value = res.rows || []
    } catch (error) {
      if (currentToken === executionPreviewRequestToken && selectedTask.value?.taskId === requestTaskId) {
        previewExecutions.value = []
        notifyError(error, '加载执行快照失败')
      }
    } finally {
      if (currentToken === executionPreviewRequestToken) {
        previewLoading.value = false
      }
    }
  }

  function openExecutionDialog(row) {
    if (row) {
      selectedTask.value = row
    }
    executionDialogVisible.value = true
    executionDetailVisible.value = false
    selectedExecution.value = null
    executionDialogList.value = []
    executionTotal.value = 0
    executionQueryParams.value.pageNum = 1
    loadExecutions()
  }

  async function loadExecutions() {
    if (!selectedTask.value) {
      executionDialogList.value = []
      executionTotal.value = 0
      return
    }
    const requestTaskId = selectedTask.value.taskId
    const currentToken = ++executionListRequestToken
    executionLoading.value = true
    selectedExecution.value = null
    try {
      const res = await getTaskExecutions(requestTaskId, executionQueryParams.value)
      if (currentToken !== executionListRequestToken || selectedTask.value?.taskId !== requestTaskId) {
        return
      }
      executionDialogList.value = res.rows || []
      executionTotal.value = res.total || 0
    } catch (error) {
      if (currentToken === executionListRequestToken && selectedTask.value?.taskId === requestTaskId) {
        executionDialogList.value = []
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

  watch(detailTab, value => {
    if (value === 'runtime' && detailOpen.value && selectedTask.value) {
      loadExecutionPreview()
    }
  })

  onMounted(() => {
    if (route.query.view === 'overview' && pageKey === 'task') {
      router.replace({ name: 'DataIntegrationHome' })
      return
    }
    if (route.query.view === 'tasks' && pageKey === 'overview') {
      router.replace({ name: 'DataIntegrationTask' })
      return
    }
    getList()
  })

  return {
    STATUS_OPTIONS,
    activeTaskCount,
    cronTaskCount,
    detailOpen,
    detailTab,
    executionDetailVisible,
    executionDialogList,
    executionDialogVisible,
    executionLoading,
    executionQueryParams,
    executionTotal,
    executorOptions,
    focusTasks,
    goToOverview,
    goToTaskList,
    loading,
    previewExecutions,
    previewLoading,
    queryParams,
    sampleTaskCount,
    selectedExecution,
    selectedTask,
    supportedExecutors,
    taskList,
    total,
    getList,
    handleAdd,
    handleDelete,
    handleExecute,
    handleQuery,
    handleUpdate,
    loadExecutionPreview,
    loadExecutions,
    openExecutionDetail,
    openExecutionDialog,
    openTaskDetail,
    resetQuery,
  }
}
