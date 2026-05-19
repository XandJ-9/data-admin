<template>
  <div class="job-list-page">
    <el-alert
      v-if="pageFeedback.title"
      class="page-feedback"
      :type="pageFeedback.type"
      :title="pageFeedback.title"
      :description="pageFeedback.message"
      :closable="false"
      show-icon
    />

    <section class="list-shell">
      <script-list-panel
        :loading="listLoading"
        :scripts="scriptList"
        :total="scriptTotal"
        :query="listQuery"
        :models="modelOptions"
        @select="openDetail"
        @create="openCreateDialog"
        @delete="handleDeleteScript"
        @refresh="loadPage"
        @search="handleSearch"
        @reset="handleResetSearch"
        @page-change="handlePageChange"
      />
    </section>

    <el-dialog v-model="showCreateDialog" title="新建加工作业" width="560px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="96px">
        <el-form-item label="作业名称" prop="scriptName">
          <el-input v-model="createForm.scriptName" placeholder="请输入作业名称" />
        </el-form-item>
        <el-form-item label="作业编码" prop="scriptCode">
          <el-input v-model="createForm.scriptCode" placeholder="唯一编码，如 dwd_order_transform" />
        </el-form-item>
        <el-form-item label="作业类型" prop="scriptType">
          <el-radio-group v-model="createForm.scriptType">
            <el-radio value="sql">SQL</el-radio>
            <el-radio value="python">Python</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="作业用途" prop="scriptRole">
          <el-select v-model="createForm.scriptRole" style="width: 100%">
            <el-option v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="createForm.scriptType === 'sql'" label="执行引擎" prop="engineType">
          <el-radio-group v-model="createForm.engineType">
            <el-radio value="spark">Spark SQL</el-radio>
            <el-radio value="hive">Hive</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="目标模型">
          <el-select v-model="createForm.targetModelId" clearable filterable placeholder="探索分析类作业可不绑定" style="width: 100%">
            <el-option
              v-for="model in modelOptions"
              :key="model.modelId"
              :label="`${model.modelName}（${model.layer}）`"
              :value="model.modelId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="作业说明">
          <el-input v-model="createForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">创建并进入详情</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'

import { addScript, delScript, listModels, listScripts } from '@/api/data/datadev'
import ScriptListPanel from '../components/ScriptListPanel.vue'

defineOptions({ name: 'DataDevIde' })

const route = useRoute()
const router = useRouter()

const roleOptions = [
  { label: '探索分析', value: 'explore' },
  { label: '模型加工', value: 'transform' },
  { label: '质量校验', value: 'quality' },
  { label: '数据回刷', value: 'backfill' },
  { label: 'Python 作业', value: 'python_job' },
]

const listQuery = reactive({
  pageNum: 1,
  pageSize: 10,
  scriptName: '',
  scriptType: '',
  scriptRole: '',
  targetModelId: undefined,
})

const scriptList = ref([])
const scriptTotal = ref(0)
const listLoading = ref(false)
const modelOptions = ref([])
const pageFeedback = ref({ type: 'success', title: '', message: '' })

function normalizeListParams(query = listQuery) {
  return {
    pageNum: query.pageNum,
    pageSize: query.pageSize,
    ...(query.scriptName ? { scriptName: query.scriptName } : {}),
    ...(query.scriptType ? { scriptType: query.scriptType } : {}),
    ...(query.scriptRole ? { scriptRole: query.scriptRole } : {}),
    ...(query.targetModelId !== undefined && query.targetModelId !== null && query.targetModelId !== ''
      ? { targetModelId: query.targetModelId }
      : {}),
  }
}

async function loadModelOptions() {
  try {
    const res = await listModels({ pageNum: 1, pageSize: 200 })
    modelOptions.value = res.rows || res.data || []
  } catch (error) {
    modelOptions.value = []
    console.warn('[datadev] 加载模型列表失败', error)
  }
}

async function loadScriptList() {
  listLoading.value = true
  try {
    const res = await listScripts(normalizeListParams())
    scriptList.value = res.rows || res.data || []
    scriptTotal.value = Number(res.total || scriptList.value.length || 0)
  } catch (error) {
    scriptList.value = []
    scriptTotal.value = 0
    ElMessage.error(error?.response?.data?.msg || error?.message || '加载加工作业列表失败')
  } finally {
    listLoading.value = false
  }
}

async function loadPage() {
  await Promise.all([loadModelOptions(), loadScriptList()])
}

function showPageFeedback(type, title, message) {
  pageFeedback.value = { type, title, message }
}

function openDetail(script) {
  if (!script?.scriptId) {
    return
  }
  router.push(`/datadev/ide/detail/${script.scriptId}`)
}

async function handleSearch(query) {
  Object.assign(listQuery, query, { pageNum: 1 })
  await loadScriptList()
}

async function handlePageChange(query) {
  Object.assign(listQuery, query)
  await loadScriptList()
}

async function handleResetSearch() {
  Object.assign(listQuery, {
    pageNum: 1,
    pageSize: 10,
    scriptName: '',
    scriptType: '',
    scriptRole: '',
    targetModelId: undefined,
  })
  await loadScriptList()
}

const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref(null)
const createForm = reactive({
  scriptName: '',
  scriptCode: '',
  scriptType: 'sql',
  scriptRole: 'transform',
  engineType: 'spark',
  targetModelId: null,
  description: '',
})
const createRules = {
  scriptName: [{ required: true, message: '请输入作业名称', trigger: 'blur' }],
  scriptCode: [{ required: true, message: '请输入作业编码', trigger: 'blur' }],
  scriptRole: [{ required: true, message: '请选择作业用途', trigger: 'change' }],
  engineType: [{ required: true, message: '请选择执行引擎', trigger: 'change' }],
}

function getDefaultRole(scriptType = 'sql') {
  return scriptType === 'python' ? 'python_job' : 'transform'
}

function resetCreateForm(scriptType = 'sql') {
  createForm.scriptName = ''
  createForm.scriptCode = ''
  createForm.scriptType = scriptType
  createForm.scriptRole = getDefaultRole(scriptType)
  createForm.engineType = scriptType === 'sql' ? 'spark' : 'mvp'
  createForm.targetModelId = route.query.targetModelId ? Number(route.query.targetModelId) : null
  createForm.description = ''
}

function openCreateDialog(scriptType = 'sql') {
  resetCreateForm(scriptType)
  showCreateDialog.value = true
  nextTick(() => createFormRef.value?.clearValidate())
}

watch(
  () => createForm.scriptType,
  (value) => {
    createForm.engineType = value === 'sql' ? 'spark' : 'mvp'
    createForm.scriptRole = getDefaultRole(value)
  },
)

async function submitCreate() {
  try {
    await createFormRef.value.validate()
  } catch {
    return
  }

  creating.value = true
  try {
    const res = await addScript({ ...createForm })
    showCreateDialog.value = false
    ElMessage.success('创建成功')
    showPageFeedback('success', '加工作业创建成功', `已创建 ${createForm.scriptType.toUpperCase()} 作业，正在进入详情页。`)
    await router.push(`/datadev/ide/detail/${res.data.scriptId}`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.msg || error?.message || '创建加工作业失败')
  } finally {
    creating.value = false
  }
}

async function handleDeleteScript(script) {
  if (!script?.scriptId) {
    return
  }
  try {
    await ElMessageBox.confirm(`确认删除加工作业「${script.scriptName}」？此操作不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await delScript(script.scriptId)
    if (scriptList.value.length === 1 && listQuery.pageNum > 1) {
      listQuery.pageNum -= 1
    }
    showPageFeedback('success', '加工作业删除成功', `作业「${script.scriptName}」已删除。`)
    ElMessage.success('删除成功')
    await loadScriptList()
  } catch (error) {
    ElMessage.error(error?.response?.data?.msg || error?.message || '删除加工作业失败')
  }
}

async function consumeQuickCreateQuery() {
  const quickCreate = route.query.quickCreate
  if (quickCreate !== 'sql' && quickCreate !== 'python') {
    return
  }
  openCreateDialog(quickCreate)
  const nextQuery = { ...route.query }
  delete nextQuery.quickCreate
  await router.replace({ path: route.path, query: nextQuery })
}

onMounted(async () => {
  if (route.query.targetModelId) {
    listQuery.targetModelId = Number(route.query.targetModelId)
  }
  await loadPage()
  await consumeQuickCreateQuery()
})

watch(
  () => route.query.quickCreate,
  () => {
    consumeQuickCreateQuery()
  },
)
</script>

<style lang="scss" scoped>
.job-list-page {
  min-height: calc(100vh - 84px);
  padding: 12px;
  background: #f5f7fb;
}

.page-feedback {
  margin-bottom: 12px;
  border-radius: 12px;
}

.list-shell {
  min-height: calc(100vh - 108px);
  background: #fff;
  border: 1px solid #e6ebf2;
  border-radius: 12px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

@media (max-width: 768px) {
  .job-list-page {
    min-height: calc(100vh - 72px);
    padding: 10px;
  }

  .list-shell {
    min-height: calc(100vh - 100px);
  }
}
</style>
