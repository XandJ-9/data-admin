<template>
  <div class="script-list-page">
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
        :directories="directoryOptions"
        @select="openDetail"
        @create="openCreateDialog"
        @delete="handleDeleteScript"
        @refresh="loadPage"
        @search="handleSearch"
        @reset="handleResetSearch"
        @page-change="handlePageChange"
      />
    </section>

    <el-dialog v-model="showCreateDialog" title="新建脚本" width="480px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="脚本名称" prop="scriptName">
          <el-input v-model="createForm.scriptName" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="脚本编码" prop="scriptCode">
          <el-input v-model="createForm.scriptCode" placeholder="唯一编码，如 ods_user_sync" />
        </el-form-item>
        <el-form-item label="脚本类型" prop="scriptType">
          <el-radio-group v-model="createForm.scriptType">
            <el-radio value="sql">SQL</el-radio>
            <el-radio value="python">Python</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="createForm.scriptType === 'sql'" label="执行引擎" prop="engineType">
          <el-radio-group v-model="createForm.engineType">
            <el-radio value="spark">Spark SQL</el-radio>
            <el-radio value="hive">Hive</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="所属目录">
          <el-select v-model="createForm.directoryId" placeholder="请选择目录（可选）" clearable style="width: 100%">
            <el-option
              v-for="directory in directoryOptions"
              :key="directory.directoryId"
              :label="directory.directoryName"
              :value="directory.directoryId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'

import { addScript, delScript, getDirectoryTree, listScripts } from '@/api/data/datadev'
import ScriptListPanel from './components/ScriptListPanel.vue'

defineOptions({ name: 'DataDevIde' })

const route = useRoute()
const router = useRouter()

const listQuery = reactive({
  pageNum: 1,
  pageSize: 10,
  scriptName: '',
  scriptType: '',
  directoryId: undefined,
})

const scriptList = ref([])
const scriptTotal = ref(0)
const listLoading = ref(false)
const directoryOptions = ref([])
const pageFeedback = ref({ type: 'success', title: '', message: '' })

function flattenDirectoryTree(treeNodes) {
  const rows = []
  const walk = (nodes) => {
    ;(nodes || []).forEach((node) => {
      rows.push(node)
      if (node.children?.length) {
        walk(node.children)
      }
    })
  }
  walk(treeNodes)
  return rows
}

async function loadDirectories() {
  try {
    const res = await getDirectoryTree()
    directoryOptions.value = flattenDirectoryTree(res.data || [])
  } catch (error) {
    directoryOptions.value = []
    console.warn('[datadev] 加载目录失败', error)
  }
}

function normalizeListParams(query = listQuery) {
  return {
    pageNum: query.pageNum,
    pageSize: query.pageSize,
    ...(query.scriptName ? { scriptName: query.scriptName } : {}),
    ...(query.scriptType ? { scriptType: query.scriptType } : {}),
    ...(query.directoryId !== undefined && query.directoryId !== null ? { directoryId: query.directoryId } : {}),
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
    ElMessage.error(error?.response?.data?.msg || error?.message || '加载脚本列表失败')
  } finally {
    listLoading.value = false
  }
}

async function loadPage() {
  await Promise.all([loadDirectories(), loadScriptList()])
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
    directoryId: undefined,
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
  engineType: 'spark',
  directoryId: null,
  description: '',
})
const createRules = {
  scriptName: [{ required: true, message: '请输入脚本名称', trigger: 'blur' }],
  scriptCode: [{ required: true, message: '请输入脚本编码', trigger: 'blur' }],
  engineType: [{ required: true, message: '请选择执行引擎', trigger: 'change' }],
}

function resetCreateForm(scriptType = 'sql') {
  createForm.scriptName = ''
  createForm.scriptCode = ''
  createForm.scriptType = scriptType
  createForm.engineType = scriptType === 'sql' ? 'spark' : 'mvp'
  createForm.directoryId = listQuery.directoryId ?? null
  createForm.description = ''
}

function openCreateDialog(scriptType = 'sql') {
  resetCreateForm(scriptType)
  showCreateDialog.value = true
  nextTick(() => createFormRef.value?.clearValidate())
}

async function submitCreate() {
  try {
    await createFormRef.value.validate()
  } catch {
    return
  }

  creating.value = true
  try {
    await addScript({ ...createForm })
    showCreateDialog.value = false
    showPageFeedback('success', '脚本创建成功', `已创建 ${createForm.scriptType.toUpperCase()} 脚本，可从列表进入详情页继续开发。`)
    ElMessage.success('创建成功')
    resetCreateForm('sql')
    await loadScriptList()
  } catch (error) {
    ElMessage.error(error?.response?.data?.msg || error?.message || '创建脚本失败')
  } finally {
    creating.value = false
  }
}

async function handleDeleteScript(script) {
  if (!script?.scriptId) {
    return
  }
  try {
    await ElMessageBox.confirm(`确认删除脚本「${script.scriptName}」？此操作不可恢复。`, '删除确认', {
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
    showPageFeedback('success', '脚本删除成功', `脚本「${script.scriptName}」已删除。`)
    ElMessage.success('删除成功')
    await loadScriptList()
  } catch (error) {
    ElMessage.error(error?.response?.data?.msg || error?.message || '删除脚本失败')
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
.script-list-page {
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
  .script-list-page {
    min-height: calc(100vh - 72px);
    padding: 10px;
  }

  .list-shell {
    min-height: calc(100vh - 100px);
  }
}
</style>
