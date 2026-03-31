import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  getETLTask,
  addETLTask,
  updateETLTask,
  delETLTask,
  executeETLTask,
  cloneETLTask,
  validateETLConfig,
  generateDataXConfig,
  dryRunETLTask,
  listETLExecutionLog,
  getETLExecutionLogDetail,
  listETLFieldMapping,
  batchCreateFieldMapping,
  listETLQualityRule,
  delETLQualityRule
} from '@/api/data/etl'
import { listDatasource } from '@/api/data/datasource'
import { ElMessage, ElMessageBox } from 'element-plus'

export function useETLTaskDetail() {
  const router = useRouter()
  const route = useRoute()

  const isEdit = ref(false)
  const saving = ref(false)
  const loadingLogs = ref(false)
  const activeTab = ref('basic')
  const executionDetailVisible = ref(false)

  const taskId = computed(() => route.params.id)
  const datasourceList = ref([])
  const fieldMappings = ref([])
  const sourceColumns = ref([])
  const qualityRules = ref([])
  const executionLogs = ref([])
  const totalLogs = ref(0)
  const currentExecution = ref({})

  const taskForm = reactive({
    taskName: '', taskCode: '', description: '', category: '',
    etlType: 'full', executorType: 'mock', executeStrategy: 'full',
    status: '0', sourceDatasourceId: null, targetDatasourceId: null,
    sourceTableName: '', sourceDatabaseName: '', targetTable: '',
    sqlConfig: '', executorParams: null
  })

  const logQuery = reactive({ pageNum: 1, pageSize: 10 })

  function handleColumnsLoaded(columns) {
    sourceColumns.value = columns
  }

  async function loadDatasources() {
    try {
      const res = await listDatasource({ pageNum: 1, pageSize: 1000 })
      datasourceList.value = res.rows || []
    } catch (error) {
      console.error('加载数据源列表失败:', error)
    }
  }

  async function loadTaskDetail() {
    try {
      const res = await getETLTask(taskId.value)
      Object.assign(taskForm, res.data)
    } catch (error) {
      console.error('加载任务详情失败:', error)
    }
  }

  async function loadFieldMappings() {
    try {
      const res = await listETLFieldMapping({ taskId: taskId.value })
      fieldMappings.value = res.rows || []
    } catch (error) {
      console.error('加载字段映射失败:', error)
    }
  }

  async function loadQualityRules() {
    try {
      const res = await listETLQualityRule({ taskId: taskId.value })
      qualityRules.value = res.rows || []
    } catch (error) {
      console.error('加载质检规则失败:', error)
    }
  }

  async function loadExecutionLogs() {
    loadingLogs.value = true
    try {
      const res = await listETLExecutionLog({ taskId: taskId.value, ...logQuery })
      executionLogs.value = res.rows || []
      totalLogs.value = res.total || 0
    } catch (error) {
      console.error('加载执行历史失败:', error)
    } finally {
      loadingLogs.value = false
    }
  }

  async function handleSave() {
    saving.value = true
    try {
      let savedTaskId
      if (taskId.value === 'new') {
        const res = await addETLTask(taskForm)
        savedTaskId = res.data.id
        ElMessage.success('创建成功')
      } else {
        await updateETLTask(taskForm)
        savedTaskId = taskId.value
        ElMessage.success('保存成功')
      }
      if (fieldMappings.value.length > 0) {
        await batchCreateFieldMapping({ taskId: savedTaskId, mappings: fieldMappings.value })
      }
      if (taskId.value === 'new') {
        router.push({ name: 'ETLTaskDetail', params: { id: savedTaskId } })
      } else {
        isEdit.value = false
        await loadTaskDetail()
      }
    } catch (error) {
      console.error('保存失败:', error)
    } finally {
      saving.value = false
    }
  }

  async function handleExecute() {
    try {
      await ElMessageBox.confirm('确认要执行该任务吗？', '提示', { type: 'warning' })
      await executeETLTask(taskId.value)
      ElMessage.success('任务已提交执行')
      activeTab.value = 'history'
      await loadExecutionLogs()
    } catch (error) {
      if (error !== 'cancel') console.error('执行任务失败:', error)
    }
  }

  async function handleMoreCommand(command) {
    const actions = {
      clone: handleClone,
      validate: handleValidate,
      datx: handleGenerateDataX,
      dryRun: handleDryRun,
      delete: handleDelete
    }
    if (actions[command]) await actions[command]()
  }

  async function handleClone() {
    try {
      await cloneETLTask(taskId.value, {})
      ElMessage.success('克隆成功')
    } catch (error) {
      console.error('克隆失败:', error)
    }
  }

  async function handleValidate() {
    try {
      await validateETLConfig(taskId.value)
      ElMessage.success('配置验证通过')
    } catch (error) {
      console.error('验证失败:', error)
    }
  }

  async function handleGenerateDataX() {
    try {
      const res = await generateDataXConfig(taskId.value, {})
      ElMessageBox.alert(JSON.stringify(res.data, null, 2), 'DataX配置', {
        customClass: 'json-dialog'
      })
    } catch (error) {
      console.error('生成配置失败:', error)
    }
  }

  async function handleDryRun() {
    try {
      await ElMessageBox.confirm('模拟执行不会写入目标数据，确认继续？', '提示', { type: 'warning' })
      await dryRunETLTask(taskId.value)
      ElMessage.success('模拟执行已完成')
    } catch (error) {
      if (error !== 'cancel') console.error('模拟执行失败:', error)
    }
  }

  async function handleDelete() {
    try {
      await ElMessageBox.confirm('确认要删除该任务吗？删除后不可恢复！', '警告', { type: 'warning' })
      await delETLTask(taskId.value)
      ElMessage.success('删除成功')
      handleBack()
    } catch (error) {
      if (error !== 'cancel') console.error('删除失败:', error)
    }
  }

  function handleBack() {
    router.back()
  }

  function handleAddQualityRule() {
    router.push({ name: 'QualityRuleCreate', query: { taskId: taskId.value } })
  }

  async function handleToggleQualityRule() {
    // 切换质检规则启用状态（待实现）
  }

  function handleViewQualityRule() {
    // 查看质检规则详情（待实现）
  }

  async function handleDeleteQualityRule(row) {
    try {
      await delETLQualityRule(row.id)
      await loadQualityRules()
      ElMessage.success('删除成功')
    } catch (error) {
      console.error('删除失败:', error)
    }
  }

  async function handleViewExecution(row) {
    try {
      const res = await getETLExecutionLogDetail(row.id)
      currentExecution.value = res.data
      executionDetailVisible.value = true
    } catch (error) {
      console.error('加载执行详情失败:', error)
    }
  }

  function resetTaskForm() {
    Object.assign(taskForm, {
      taskName: '', taskCode: '', description: '', category: '',
      etlType: route.query.etlType || 'full', executorType: 'mock',
      executeStrategy: 'full', status: '0',
      sourceDatasourceId: null, targetDatasourceId: null,
      sourceTableName: '', sourceDatabaseName: '',
      targetTable: '', sqlConfig: '', executorParams: null
    })
    isEdit.value = true
    fieldMappings.value = []
    sourceColumns.value = []
    qualityRules.value = []
    executionLogs.value = []
  }

  onMounted(async () => {
    await loadDatasources()
    if (taskId.value !== 'new') {
      await loadTaskDetail()
      await loadFieldMappings()
      await loadQualityRules()
      await loadExecutionLogs()
    } else {
      isEdit.value = true
      if (route.query.etlType) {
        taskForm.etlType = route.query.etlType
      }
    }
  })

  watch(
    () => route.params.id,
    async (newId) => {
      if (route.name !== 'ETLTaskDetail') return
      if (newId === 'new') {
        resetTaskForm()
      } else {
        isEdit.value = false
        await loadTaskDetail()
        await loadFieldMappings()
        await loadQualityRules()
        await loadExecutionLogs()
      }
    },
    { immediate: false }
  )

  return {
    isEdit, saving, loadingLogs, activeTab, executionDetailVisible,
    taskId, datasourceList, fieldMappings, sourceColumns,
    qualityRules, executionLogs, totalLogs, currentExecution,
    taskForm, logQuery,
    handleColumnsLoaded, handleSave, handleExecute,
    handleMoreCommand, handleBack,
    handleAddQualityRule, handleToggleQualityRule,
    handleViewQualityRule, handleDeleteQualityRule,
    handleViewExecution, loadExecutionLogs
  }
}
