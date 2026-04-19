<template>
  <div class="script-detail-page" v-loading="detailLoading">
    <template v-if="currentScript">
      <el-alert
        v-if="workspaceFeedback.title"
        class="page-feedback"
        :type="workspaceFeedback.type"
        :title="workspaceFeedback.title"
        :description="workspaceFeedback.message"
        :closable="false"
        show-icon
      />

      <flip-card :flipped="isEditing" min-height="720px">
        <template #front>
          <section class="content-grid">
            <div class="info-card">
              <div class="section-head section-head--stacked">
                <div class="script-overview">
                  <div class="script-overview__title">
                    <h2>{{ currentScript.scriptName }}</h2>
                    <div class="script-overview__tags">
                      <el-tag size="small" effect="plain">{{ currentScript.scriptType?.toUpperCase() }}</el-tag>
                      <el-tag size="small" type="success" effect="plain">{{ currentRuntimeLabel || '未配置执行能力' }}</el-tag>
                      <el-tag size="small" :type="scriptStatusTagType(currentScript.status)" effect="plain">{{ scriptStatusLabel(currentScript.status) }}</el-tag>
                    </div>
                  </div>
                  <p>先确认脚本上下文、负责人和当前运行状态，再按需进入 SQL 编辑页。</p>
                </div>
              </div>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="脚本编码">{{ currentScript.scriptCode || '-' }}</el-descriptions-item>
                <el-descriptions-item label="所属目录">{{ currentScript.directoryName || '未分配目录' }}</el-descriptions-item>
                <el-descriptions-item label="脚本类型">{{ currentScript.scriptType?.toUpperCase() || '-' }}</el-descriptions-item>
                <el-descriptions-item label="执行引擎">{{ currentRuntimeLabel || '-' }}</el-descriptions-item>
                <el-descriptions-item label="负责人">{{ currentScript.owner || '-' }}</el-descriptions-item>
                <el-descriptions-item label="当前状态">{{ scriptStatusLabel(currentScript.status) }}</el-descriptions-item>
                <el-descriptions-item label="当前版本">v{{ currentScript.versionNumber || 0 }}</el-descriptions-item>
                <el-descriptions-item label="最近执行">{{ latestExecutionSummary }}</el-descriptions-item>
                <el-descriptions-item label="脚本说明" :span="2">{{ currentScript.description || '暂无描述' }}</el-descriptions-item>
              </el-descriptions>
            </div>

            <div class="activity-card">
              <div class="section-head">
                <div>
                  <h3>版本与运维</h3>
                  <p>版本回溯、执行记录与日常运维统一放在这里；确定无误后再进入编辑态修改 SQL。</p>
                </div>
                <div class="section-actions">
                  <el-button type="primary" @click="openEditor">开始编辑 SQL</el-button>
                  <el-button @click="goBack">返回列表</el-button>
                  <el-button @click="handleEditScript(currentScript)">编辑信息</el-button>
                  <el-button type="danger" plain @click="handleDeleteScript(currentScript)">删除脚本</el-button>
                </div>
              </div>
              <activity-panel
                v-model:active-tab="activityTab"
                v-model:version-view="versionView"
                :filtered-versions="filteredVersions"
                :selected-version-id="selectedVersionId"
                :version-empty-text="versionEmptyText"
                :executions="executions"
                @preview-version="handlePreviewVersion"
                @rollback-version="handleRollback"
              />
            </div>
          </section>
        </template>

        <template #back>
          <section class="dev-mode-page">
            <div class="dev-mode-actions">
              <el-button @click="closeEditor">返回详情</el-button>
              <div class="dev-mode-buttons">
                <el-button text @click="goBack">返回列表</el-button>
                <el-button type="primary" :loading="running" @click="handleRun">执行脚本</el-button>
              </div>
            </div>
            <div class="dev-editor-shell">
              <code-editor
                ref="editorRef"
                v-model="content"
                :lang="scriptLang"
                :running="running"
                :hide-toolbar="true"
                @run="handleRun"
              />
            </div>
          </section>
        </template>
      </flip-card>
    </template>

    <el-empty v-else description="脚本不存在或已被删除" :image-size="88">
      <el-button type="primary" @click="goBack">返回脚本列表</el-button>
    </el-empty>

    <el-dialog v-model="showEditDialog" title="编辑脚本信息" width="480px" :close-on-click-modal="false">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="脚本名称" prop="scriptName">
          <el-input v-model="editForm.scriptName" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="所属目录">
          <el-select v-model="editForm.directoryId" placeholder="请选择目录（可选）" clearable style="width: 100%">
            <el-option
              v-for="directory in directoryOptions"
              :key="directory.directoryId"
              :label="directory.directoryName"
              :value="directory.directoryId"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editForm.scriptType === 'sql'" label="执行引擎" prop="engineType">
          <el-radio-group v-model="editForm.engineType">
            <el-radio value="spark">Spark SQL</el-radio>
            <el-radio value="hive">Hive</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="editing" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  getScript,
  updateScript,
  delScript,
  listVersions,
  createVersion,
  rollbackVersion,
  executeScript,
  listScriptExecutions,
  getDirectoryTree,
} from '@/api/data/datadev'

import FlipCard from '@/components/FlipCard/index.vue'
import CodeEditor from './components/CodeEditor.vue'
import ActivityPanel from './components/ActivityPanel.vue'

defineOptions({ name: 'DataDevScriptDetail' })

const route = useRoute()
const router = useRouter()

const engineLabelMap = { spark: 'Spark SQL', hive: 'Hive', mvp: 'MVP预演' }

const detailLoading = ref(false)
const currentScript = ref(null)
const workspaceFeedback = ref({ type: 'info', title: '', message: '' })
const directoryOptions = ref([])
const isEditing = ref(false)
const running = ref(false)
const editorRef = ref(null)

const currentRuntimeLabel = computed(() => getRuntimeLabel(currentScript.value))
const scriptLang = computed(() => currentScript.value?.scriptType || 'sql')
const latestExecutionSummary = computed(() => {
  const latestExecution = executions.value?.[0]
  if (!latestExecution) return '暂无记录'
  return `${execStatusLabel(latestExecution.status)} / ${latestExecution.createTime || '-'} `
})
const content = computed({
  get: () => currentScript.value?.content || '',
  set: (value) => {
    if (!currentScript.value) return
    currentScript.value.content = value
  },
})
const hasChange = computed(() => {
  if (!currentScript.value) return false
  return currentScript.value.content !== currentScript.value.savedContent
})

function getRuntimeLabel(script) {
  if (!script) return ''
  if (script.datasourceName) return script.datasourceName
  return engineLabelMap[script.engineType] || ''
}

function showWorkspaceFeedback(type, title, message) {
  workspaceFeedback.value = { type, title, message }
}

function clearWorkspaceFeedback() {
  workspaceFeedback.value = { type: 'info', title: '', message: '' }
}

function scriptStatusLabel(status) {
  return ({ draft: '草稿', published: '正式', archived: '归档' })[status] || '草稿'
}

function scriptStatusTagType(status) {
  return ({ draft: 'info', published: 'success', archived: 'warning' })[status] || 'info'
}

function getErrorMessage(error, fallback = '操作失败') {
  if (!error) return fallback
  if (error instanceof Error && error.message) return error.message
  if (typeof error === 'string' && error.trim()) return error
  if (error?.response?.data?.msg) return error.response.data.msg
  if (error?.response?.data?.detail) return error.response.data.detail
  if (error?.msg) return error.msg
  return fallback
}

function presentActionError(error, title, fallback = '操作失败') {
  let message = getErrorMessage(error, fallback)
  if (message === '系统接口请求超时' && title === '脚本执行失败') {
    message = '脚本执行等待超时，任务可能仍在后端运行，请稍后到执行记录查看结果'
  }
  showWorkspaceFeedback('error', title, message)
  if (!error?.__handled) {
    ElMessage.error(message)
  }
  return message
}

function flattenDirectoryTree(treeNodes) {
  const result = []
  const traverse = (nodes) => {
    ;(nodes || []).forEach((node) => {
      result.push(node)
      if (node.children?.length) {
        traverse(node.children)
      }
    })
  }
  traverse(treeNodes)
  return result
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

function createScriptPayload(data) {
  return {
    scriptId: data.scriptId,
    scriptName: data.scriptName,
    scriptCode: data.scriptCode,
    content: data.content || '',
    savedContent: data.content || '',
    scriptType: data.scriptType || 'sql',
    status: data.status || 'draft',
    datasourceId: data.datasourceId || null,
    datasourceName: data.datasourceName || '',
    engineType: data.engineType || 'spark',
    directoryId: data.directoryId || null,
    directoryName: data.directoryName || '',
    versionNumber: data.versionNumber || 0,
    owner: data.owner || '',
    description: data.description || '',
  }
}

async function loadCurrentScript(scriptId, { preserveFeedback = false } = {}) {
  if (!scriptId) {
    currentScript.value = null
    return
  }
  detailLoading.value = true
  try {
    const res = await getScript(scriptId)
    currentScript.value = createScriptPayload(res.data || {})
    await Promise.all([loadVersions(scriptId), loadExecutions(scriptId)])
    if (!preserveFeedback) {
      clearWorkspaceFeedback()
    }
  } catch (error) {
    currentScript.value = null
    presentActionError(error, '脚本详情加载失败', '加载脚本详情失败')
  } finally {
    detailLoading.value = false
  }
}

async function confirmDiscardChanges(message = '当前脚本有未保存修改，离开后将丢失编辑内容，是否继续？') {
  if (!hasChange.value) return true
  try {
    await ElMessageBox.confirm(message, '离开确认', {
      type: 'warning',
      confirmButtonText: '继续离开',
      cancelButtonText: '继续编辑',
    })
    return true
  } catch {
    return false
  }
}

function goBack() {
  router.push({ name: 'DataDevIde' })
}

function openEditor() {
  if (!currentScript.value) {
    ElMessage.warning('请先选择一个脚本')
    return
  }
  isEditing.value = true
}

function closeEditor() {
  isEditing.value = false
}

function focusEditor() {
  const editor = editorRef.value?.getEditor?.()
  if (!editor) return
  editor.resize()
  editor.focus()
}

watch(isEditing, async (editing) => {
  if (!editing) return
  await nextTick()
  window.requestAnimationFrame(() => {
    window.setTimeout(() => {
      focusEditor()
    }, 320)
  })
})

const showEditDialog = ref(false)
const editing = ref(false)
const editFormRef = ref(null)
const editForm = reactive({ scriptId: null, scriptName: '', scriptType: 'sql', engineType: 'spark', directoryId: null, description: '' })
const editRules = {
  scriptName: [{ required: true, message: '请输入脚本名称', trigger: 'blur' }],
}

function handleEditScript(script) {
  if (!script) return
  editForm.scriptId = script.scriptId
  editForm.scriptName = script.scriptName
  editForm.scriptType = script.scriptType || 'sql'
  editForm.engineType = script.engineType || 'spark'
  editForm.directoryId = script.directoryId || null
  editForm.description = script.description || ''
  showEditDialog.value = true
  nextTick(() => editFormRef.value?.clearValidate())
}

async function submitEdit() {
  try {
    await editFormRef.value.validate()
  } catch {
    return
  }
  editing.value = true
  try {
    await updateScript(editForm.scriptId, {
      scriptName: editForm.scriptName,
      directoryId: editForm.directoryId,
      engineType: editForm.scriptType === 'sql' ? editForm.engineType : 'mvp',
      description: editForm.description,
    })
    showEditDialog.value = false
    showWorkspaceFeedback('success', '脚本信息已更新', '脚本基础信息已保存。')
    ElMessage.success('保存成功')
    await Promise.all([
      loadDirectories(),
      loadCurrentScript(editForm.scriptId, { preserveFeedback: true }),
    ])
  } catch (error) {
    presentActionError(error, '脚本信息保存失败', '保存失败')
  } finally {
    editing.value = false
  }
}

async function handleDeleteScript(script) {
  if (!script?.scriptId) return
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
    ElMessage.success('删除成功')
    await router.push({ name: 'DataDevIde' })
  } catch (error) {
    presentActionError(error, '脚本删除失败', '删除失败')
  }
}

const versions = ref([])
const selectedVersionId = ref(null)
const activityTab = ref('versions')
const versionView = ref('all')
const executions = ref([])

const filteredVersions = computed(() => {
  if (versionView.value === 'released') return versions.value.filter(item => item.isReleased)
  if (versionView.value === 'draft') return versions.value.filter(item => !item.isReleased)
  return versions.value
})
const versionEmptyText = computed(() => {
  if (versionView.value === 'released') return '暂无正式版本'
  if (versionView.value === 'draft') return '暂无草稿版本'
  return '暂无版本'
})

async function loadVersions(scriptId) {
  try {
    const res = await listVersions(scriptId)
    versions.value = res.data || []
    const currentVersionItem = versions.value.find(item => item.isCurrent)
    selectedVersionId.value = currentVersionItem?.versionId || null
  } catch (error) {
    versions.value = []
    selectedVersionId.value = null
    console.warn('[datadev] 加载版本失败', error)
  }
}

async function handlePreviewVersion(version) {
  if (!currentScript.value || !version) return
  if (selectedVersionId.value === version.versionId) return
  if (!(await confirmDiscardChanges('当前内容有未保存修改，查看历史版本将覆盖编辑区内容，是否继续？'))) {
    return
  }
  currentScript.value.content = version.content || ''
  currentScript.value.versionNumber = version.versionNumber || currentScript.value.versionNumber
  selectedVersionId.value = version.versionId
  showWorkspaceFeedback('info', '版本内容已切换', `当前正在预览 v${version.versionNumber}。`)
}

async function handleRollback(version) {
  if (!currentScript.value || !version) return
  try {
    await ElMessageBox.confirm(`确认回滚到 v${version.versionNumber}？`, '回滚确认')
  } catch {
    return
  }
  try {
    await rollbackVersion(currentScript.value.scriptId, version.versionId)
    activityTab.value = 'versions'
    showWorkspaceFeedback('success', '版本回滚成功', `已回滚到 v${version.versionNumber}。`)
    ElMessage.success('回滚成功')
    await loadCurrentScript(currentScript.value.scriptId, { preserveFeedback: true })
  } catch (error) {
    presentActionError(error, '版本回滚失败', '回滚失败')
  }
}

function execStatusLabel(status) {
  const map = { pending: '已提交', running: '执行中', success: '成功', failed: '失败', cancelled: '已取消' }
  return map[status] || status || '未知'
}

async function loadExecutions(scriptId) {
  try {
    const res = await listScriptExecutions(scriptId)
    executions.value = res.rows || res.data || []
  } catch (error) {
    executions.value = []
    console.warn('[datadev] 加载执行记录失败', error)
  }
}

async function syncDraftBeforeRun() {
  if (!currentScript.value?.scriptId || !hasChange.value) return
  await createVersion(currentScript.value.scriptId, {
    content: content.value,
    changeLog: '开发模式自动保存',
  })
  currentScript.value.savedContent = content.value
  await loadVersions(currentScript.value.scriptId)
}

async function handleRun() {
  if (!currentScript.value) {
    ElMessage.warning('请先选择一个脚本')
    return
  }
  running.value = true
  try {
    await syncDraftBeforeRun()
    const res = await executeScript(currentScript.value.scriptId)
    const data = res.data || {}
    showWorkspaceFeedback(
      data.designOnly ? 'warning' : 'success',
      data.designOnly ? '脚本预演完成' : '脚本执行完成',
      data.designOnly
        ? `本次为预演模式，耗时 ${data.duration || '-'}s。`
        : `本次执行返回 ${data.rows?.length || 0} 行数据，耗时 ${data.duration || '-'}s。`,
    )
    ElMessage.success(data.designOnly ? '预演完成' : '执行成功')
    await loadExecutions(currentScript.value.scriptId)
  } catch (error) {
    presentActionError(error, '脚本执行失败', '执行失败')
  } finally {
    running.value = false
  }
}

onMounted(async () => {
  await loadDirectories()
  await loadCurrentScript(Number(route.params.scriptId))
})

watch(
  () => route.params.scriptId,
  async (scriptId, oldScriptId) => {
    const nextScriptId = Number(scriptId)
    const prevScriptId = Number(oldScriptId)
    if (!nextScriptId || nextScriptId === prevScriptId) return
    if (!(await confirmDiscardChanges('当前脚本有未保存修改，切换脚本将丢失编辑内容，是否继续？'))) {
      await router.replace(`/datadev/ide/detail/${prevScriptId || currentScript.value?.scriptId}`)
      return
    }
    isEditing.value = false
    await loadCurrentScript(nextScriptId)
  },
)

onBeforeRouteLeave(async () => {
  return await confirmDiscardChanges()
})
</script>

<style lang="scss" scoped>
.script-detail-page {
  min-height: calc(100vh - 84px);
  padding: 18px;
  background: #f5f7fb;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card,
.activity-card,
.dev-mode-page {
  background: #fff;
  border: 1px solid #e6ebf2;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.page-feedback {
  border-radius: 14px;
}

.content-grid {
  min-height: 720px;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(360px, 0.9fr);
  gap: 12px;
}

.info-card,
.activity-card {
  min-height: 0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-head--stacked {
  display: block;
}

.section-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.section-head h3,
.script-overview h2 {
  margin: 0;
  color: #1f2f45;
}

.script-overview h2 {
  font-size: 26px;
}

.script-overview p,
.section-head p {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.7;
  color: #66768b;
}

.script-overview__title,
.script-overview__tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.script-overview__title {
  justify-content: space-between;
}

.activity-card :deep(.activity-panel) {
  flex: 1;
  min-height: 0;
}

.dev-mode-page {
  min-height: 720px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dev-mode-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.dev-mode-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.dev-editor-shell {
  flex: 1;
  min-height: 0;
  border: 1px solid #e6ebf2;
  border-radius: 12px;
  overflow: hidden;
}

@media (max-width: 1280px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .activity-card {
    min-height: 420px;
  }
}

@media (max-width: 768px) {
  .script-detail-page {
    min-height: calc(100vh - 72px);
    padding: 12px;
  }

  .info-card,
  .activity-card,
  .dev-mode-page {
    padding: 16px;
  }

  .section-head,
  .dev-mode-actions,
  .script-overview__title {
    flex-direction: column;
    align-items: stretch;
  }

  .section-actions,
  .dev-mode-buttons,
  .script-overview__tags {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
