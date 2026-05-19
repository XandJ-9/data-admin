<template>
  <div class="job-detail-page" v-loading="detailLoading">
    <el-alert
      v-if="workspaceFeedback.title"
      class="page-feedback"
      :type="workspaceFeedback.type"
      :title="workspaceFeedback.title"
      :description="workspaceFeedback.message"
      :closable="false"
      show-icon
    />

    <template v-if="currentScript">
      <section class="page-header">
        <div>
          <p class="page-path">建模与加工 / 加工作业</p>
          <h1>{{ form.scriptName || currentScript.scriptName }}</h1>
          <p>在这里完成作业定义、脚本编写、版本管理与调试执行；确认后发布到任务运维继续编排和调度。</p>
        </div>
        <div class="header-actions">
          <el-button @click="goBack">返回列表</el-button>
          <el-button v-hasPermi="['datadev:ide:edit']" @click="handleSaveMeta" :loading="savingMeta">保存定义</el-button>
          <el-button v-hasPermi="['datadev:ide:edit']" type="primary" plain @click="handleSaveDraft" :loading="savingDraft">保存草稿</el-button>
          <el-button v-hasPermi="['datadev:ide:publish']" type="success" @click="handlePublishVersion" :loading="publishingVersion">发布版本</el-button>
          <el-button v-hasPermi="['datadev:ide:publish']" type="warning" @click="handlePublishTask" :loading="publishingTask">发布到任务运维</el-button>
        </div>
      </section>

      <section class="content-grid">
        <div class="main-column">
          <el-card shadow="never" class="detail-card">
            <template #header>
              <div class="card-header">
                <div>
                  <h3>作业定义</h3>
                  <p>模型驱动开发：模型加工类作业建议绑定目标模型，并在发布前补齐治理信息。</p>
                </div>
                <div class="meta-tags">
                  <el-tag effect="plain">{{ (currentScript.scriptType || 'sql').toUpperCase() }}</el-tag>
                  <el-tag effect="plain" type="success">{{ runtimeLabel }}</el-tag>
                  <el-tag effect="plain" :type="statusTagType(currentScript.status)">{{ statusLabel(currentScript.status) }}</el-tag>
                  <el-tag effect="plain" :type="currentScript.taskId ? 'success' : 'info'">{{ taskStatusLabel(currentScript.taskStatus) }}</el-tag>
                </div>
              </div>
            </template>

            <el-form ref="basicFormRef" :model="form" :rules="basicRules" label-width="96px">
              <el-row :gutter="16">
                <el-col :xs="24" :md="12">
                  <el-form-item label="作业名称" prop="scriptName">
                    <el-input v-model="form.scriptName" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="作业编码">
                    <el-input :model-value="currentScript.scriptCode" disabled />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="8">
                  <el-form-item label="作业类型">
                    <el-input :model-value="(currentScript.scriptType || 'sql').toUpperCase()" disabled />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="8">
                  <el-form-item label="作业用途" prop="scriptRole">
                    <el-select v-model="form.scriptRole" style="width: 100%">
                      <el-option v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="8">
                  <el-form-item label="负责人">
                    <el-input :model-value="currentScript.owner || '-'" disabled />
                  </el-form-item>
                </el-col>
                <el-col v-if="currentScript.scriptType === 'sql'" :xs="24" :md="8">
                  <el-form-item label="执行引擎" prop="engineType">
                    <el-select v-model="form.engineType" style="width: 100%">
                      <el-option label="Spark SQL" value="spark" />
                      <el-option label="Hive" value="hive" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="16">
                  <el-form-item label="目标模型">
                    <el-select v-model="form.targetModelId" clearable filterable placeholder="探索分析可不绑定；发布任务前会做治理校验" style="width: 100%">
                      <el-option
                        v-for="model in modelOptions"
                        :key="model.modelId"
                        :label="`${model.modelName}（${model.layer}）`"
                        :value="model.modelId"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="8">
                  <el-form-item label="当前版本">
                    <el-input :model-value="`v${currentScript.versionNumber || 0}`" disabled />
                  </el-form-item>
                </el-col>
                <el-col :span="24">
                  <el-form-item label="作业说明">
                    <el-input v-model="form.description" type="textarea" :rows="2" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </el-card>

          <el-card shadow="never" class="detail-card editor-card">
            <template #header>
              <div class="card-header">
                <div>
                  <h3>脚本编辑</h3>
                  <p>保存草稿用于开发调试；发布版本用于形成正式可回滚版本；发布到任务运维会基于当前版本生成任务快照。</p>
                </div>
                <div class="editor-actions">
                  <el-tag v-if="hasUnsavedContent" type="warning" effect="plain">内容未保存</el-tag>
                  <el-button v-hasPermi="['datadev:ide:execute']" type="primary" :loading="running" @click="handleRun">执行作业</el-button>
                </div>
              </div>
            </template>
            <code-editor
              ref="editorRef"
              v-model="content"
              :lang="currentScript.scriptType || 'sql'"
              :running="running"
              :hide-toolbar="true"
              @run="handleRun"
            />
          </el-card>
        </div>

        <div class="side-column">
          <el-card shadow="never" class="detail-card">
            <template #header>
              <div class="card-header">
                <div>
                  <h3>版本与执行</h3>
                  <p>当前页只做研发与发布，真正的调度依赖请在任务运维继续处理。</p>
                </div>
                <el-button v-if="currentScript.taskId" link type="primary" @click="openTaskDetail">查看任务运维</el-button>
              </div>
            </template>
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
          </el-card>
        </div>
      </section>
    </template>

    <el-empty v-else description="加工作业不存在或已被删除" :image-size="88">
      <el-button type="primary" @click="goBack">返回加工作业列表</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  createVersion,
  delScript,
  executeScript,
  getScript,
  listModels,
  listScriptExecutions,
  listVersions,
  publishScriptTask,
  publishVersion,
  rollbackVersion,
  updateScript,
} from '@/api/data/datadev'
import CodeEditor from '../../components/CodeEditor.vue'
import ActivityPanel from '../../components/ActivityPanel.vue'

defineOptions({ name: 'DataDevScriptDetail' })

const route = useRoute()
const router = useRouter()
const basicFormRef = ref(null)
const editorRef = ref(null)

const roleOptions = [
  { label: '探索分析', value: 'explore' },
  { label: '模型加工', value: 'transform' },
  { label: '质量校验', value: 'quality' },
  { label: '数据回刷', value: 'backfill' },
  { label: 'Python 作业', value: 'python_job' },
]
const engineLabelMap = { spark: 'Spark SQL', hive: 'Hive', mvp: 'MVP 预演' }

const detailLoading = ref(false)
const savingMeta = ref(false)
const savingDraft = ref(false)
const publishingVersion = ref(false)
const publishingTask = ref(false)
const running = ref(false)

const currentScript = ref(null)
const modelOptions = ref([])
const workspaceFeedback = ref({ type: 'info', title: '', message: '' })
const content = ref('')
const savedContent = ref('')
const versions = ref([])
const selectedVersionId = ref(null)
const activityTab = ref('versions')
const versionView = ref('all')
const executions = ref([])

const form = reactive({
  scriptName: '',
  scriptRole: 'transform',
  engineType: 'spark',
  targetModelId: null,
  description: '',
})
const basicRules = {
  scriptName: [{ required: true, message: '请输入作业名称', trigger: 'blur' }],
  scriptRole: [{ required: true, message: '请选择作业用途', trigger: 'change' }],
  engineType: [{ required: true, message: '请选择执行引擎', trigger: 'change' }],
}

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
const runtimeLabel = computed(() => {
  if (!currentScript.value) return '-'
  if (currentScript.value.datasourceName) return currentScript.value.datasourceName
  return engineLabelMap[currentScript.value.engineType] || '未配置'
})
const hasUnsavedContent = computed(() => content.value !== savedContent.value)
const hasMetaChange = computed(() => {
  if (!currentScript.value) return false
  return (
    form.scriptName !== (currentScript.value.scriptName || '')
    || form.scriptRole !== (currentScript.value.scriptRole || '')
    || form.engineType !== (currentScript.value.engineType || 'spark')
    || (form.targetModelId || null) !== (currentScript.value.targetModelId || null)
    || form.description !== (currentScript.value.description || '')
  )
})

function showWorkspaceFeedback(type, title, message) {
  workspaceFeedback.value = { type, title, message }
}

function statusLabel(status) {
  return ({ draft: '草稿', published: '正式', archived: '归档' })[status] || '草稿'
}

function statusTagType(status) {
  return ({ draft: 'info', published: 'success', archived: 'warning' })[status] || 'info'
}

function taskStatusLabel(status) {
  return status ? ({ active: '已纳管', paused: '已暂停', draft: '草稿', archived: '已归档' }[status] || status) : '未发布'
}

function roleLabel(value) {
  return roleOptions.find(item => item.value === value)?.label || '未设置'
}

function extractErrorMessage(error, fallback = '操作失败') {
  const responseData = error?.response?.data || {}
  if (responseData.msg) {
    return responseData.msg
  }
  if (responseData.errors) {
    const firstValue = Object.values(responseData.errors)[0]
    if (Array.isArray(firstValue)) {
      return String(firstValue[0] || fallback)
    }
    return String(firstValue || fallback)
  }
  if (responseData.detail) {
    return typeof responseData.detail === 'string' ? responseData.detail : JSON.stringify(responseData.detail)
  }
  return error?.message || fallback
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

function applyScriptData(data = {}) {
  currentScript.value = { ...data }
  form.scriptName = data.scriptName || ''
  form.scriptRole = data.scriptRole || (data.scriptType === 'python' ? 'python_job' : 'transform')
  form.engineType = data.engineType || (data.scriptType === 'python' ? 'mvp' : 'spark')
  form.targetModelId = data.targetModelId || null
  form.description = data.description || ''
  content.value = data.content || ''
  savedContent.value = data.content || ''
}

async function loadVersions(scriptId) {
  const res = await listVersions(scriptId)
  versions.value = res.data || []
  const currentVersionItem = versions.value.find(item => item.isCurrent)
  selectedVersionId.value = currentVersionItem?.versionId || null
}

async function loadExecutions(scriptId) {
  const res = await listScriptExecutions(scriptId)
  executions.value = res.rows || res.data || []
}

async function loadCurrentScript(scriptId, { preserveFeedback = false } = {}) {
  if (!scriptId) {
    currentScript.value = null
    return
  }
  detailLoading.value = true
  try {
    const res = await getScript(scriptId)
    applyScriptData(res.data || {})
    await Promise.all([loadVersions(scriptId), loadExecutions(scriptId)])
    if (!preserveFeedback) {
      workspaceFeedback.value = { type: 'info', title: '', message: '' }
    }
  } catch (error) {
    currentScript.value = null
    showWorkspaceFeedback('error', '加工作业加载失败', extractErrorMessage(error, '加载加工作业失败'))
  } finally {
    detailLoading.value = false
  }
}

function buildMetaPayload() {
  return {
    scriptName: form.scriptName,
    scriptRole: form.scriptRole,
    engineType: currentScript.value?.scriptType === 'sql' ? form.engineType : 'mvp',
    targetModelId: form.targetModelId,
    description: form.description,
  }
}

async function persistMeta({ silent = false } = {}) {
  if (!currentScript.value) return
  await basicFormRef.value?.validate()
  if (!hasMetaChange.value) return
  await updateScript(currentScript.value.scriptId, buildMetaPayload())
  Object.assign(currentScript.value, buildMetaPayload(), { targetModelName: '' })
  if (!silent) {
    ElMessage.success('作业定义已保存')
    showWorkspaceFeedback('success', '作业定义已保存', '基础信息已更新，后续可继续保存草稿或发布任务。')
  }
}

async function ensureDraftSynced() {
  if (!currentScript.value) return
  if (!hasUnsavedContent.value && currentScript.value.versionNumber) return
  await createVersion(currentScript.value.scriptId, {
    content: content.value,
    changeLog: '页面保存草稿',
  })
  savedContent.value = content.value
  await loadCurrentScript(currentScript.value.scriptId, { preserveFeedback: true })
}

async function confirmDiscardChanges(message = '当前作业有未保存内容，离开后将丢失修改，是否继续？') {
  if (!hasUnsavedContent.value && !hasMetaChange.value) return true
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

function openTaskDetail() {
  if (!currentScript.value?.taskId) return
  router.push({ name: 'DataTaskDetail', params: { id: currentScript.value.taskId } })
}

async function handleSaveMeta() {
  if (!currentScript.value) return
  savingMeta.value = true
  try {
    await persistMeta()
    await loadCurrentScript(currentScript.value.scriptId, { preserveFeedback: true })
  } catch (error) {
    const message = extractErrorMessage(error, '保存作业定义失败')
    showWorkspaceFeedback('error', '作业定义保存失败', message)
    ElMessage.error(message)
  } finally {
    savingMeta.value = false
  }
}

async function handleSaveDraft() {
  if (!currentScript.value) return
  savingDraft.value = true
  try {
    await persistMeta({ silent: true })
    await ensureDraftSynced()
    showWorkspaceFeedback('success', '草稿已保存', `当前作业已保存为 v${currentScript.value.versionNumber || 0} 草稿版本。`)
    ElMessage.success('草稿保存成功')
  } catch (error) {
    const message = extractErrorMessage(error, '保存草稿失败')
    showWorkspaceFeedback('error', '草稿保存失败', message)
    ElMessage.error(message)
  } finally {
    savingDraft.value = false
  }
}

async function handlePublishVersion() {
  if (!currentScript.value) return
  publishingVersion.value = true
  try {
    await persistMeta({ silent: true })
    await publishVersion(currentScript.value.scriptId, {
      content: content.value,
      changeLog: '页面发布正式版本',
    })
    savedContent.value = content.value
    await loadCurrentScript(currentScript.value.scriptId, { preserveFeedback: true })
    showWorkspaceFeedback('success', '版本发布成功', `已发布 v${currentScript.value.versionNumber || 0}，后续可直接发布到任务运维。`)
    ElMessage.success('版本发布成功')
  } catch (error) {
    const message = extractErrorMessage(error, '发布版本失败')
    showWorkspaceFeedback('error', '版本发布失败', message)
    ElMessage.error(message)
  } finally {
    publishingVersion.value = false
  }
}

async function handlePublishTask() {
  if (!currentScript.value) return
  publishingTask.value = true
  try {
    await persistMeta({ silent: true })
    await ensureDraftSynced()
    const res = await publishScriptTask(currentScript.value.scriptId)
    ElMessage.success(res.msg || '已发布到任务运维')
    router.push({ name: 'DataTaskDetail', params: { id: res.data.taskId } })
  } catch (error) {
    const message = extractErrorMessage(error, '发布任务失败')
    showWorkspaceFeedback('error', '发布到任务运维失败', message)
    ElMessage.error(message)
  } finally {
    publishingTask.value = false
  }
}

async function handleRollback(version) {
  if (!currentScript.value || !version) return
  try {
    await ElMessageBox.confirm(`确认回滚到 v${version.versionNumber}？`, '回滚确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    await rollbackVersion(currentScript.value.scriptId, version.versionId)
    await loadCurrentScript(currentScript.value.scriptId, { preserveFeedback: true })
    showWorkspaceFeedback('success', '版本回滚成功', `已回滚到 v${version.versionNumber}。`)
    ElMessage.success('版本回滚成功')
  } catch (error) {
    const message = extractErrorMessage(error, '回滚版本失败')
    showWorkspaceFeedback('error', '版本回滚失败', message)
    ElMessage.error(message)
  }
}

async function handlePreviewVersion(version) {
  if (!version) return
  if (!(await confirmDiscardChanges('当前编辑区有未保存内容，预览历史版本会覆盖编辑器内容，是否继续？'))) {
    return
  }
  selectedVersionId.value = version.versionId
  content.value = version.content || ''
  showWorkspaceFeedback('info', '已切换预览版本', `当前正在预览 v${version.versionNumber}。`)
}

async function handleRun() {
  if (!currentScript.value) return
  running.value = true
  try {
    await persistMeta({ silent: true })
    await ensureDraftSynced()
    const res = await executeScript(currentScript.value.scriptId)
    const data = res.data || {}
    showWorkspaceFeedback(
      data.designOnly ? 'warning' : 'success',
      data.designOnly ? '作业预演完成' : '作业执行完成',
      data.designOnly
        ? `本次为预演模式，耗时 ${data.duration || '-'}s。`
        : `本次执行返回 ${data.rows?.length || 0} 行数据，耗时 ${data.duration || '-'}s。`,
    )
    ElMessage.success(data.designOnly ? '预演完成' : '执行成功')
    await loadExecutions(currentScript.value.scriptId)
  } catch (error) {
    const message = extractErrorMessage(error, '执行作业失败')
    showWorkspaceFeedback('error', '作业执行失败', message)
    ElMessage.error(message)
  } finally {
    running.value = false
  }
}

async function handleDeleteScript() {
  if (!currentScript.value?.scriptId) return
  try {
    await ElMessageBox.confirm(`确认删除加工作业「${currentScript.value.scriptName}」？此操作不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await delScript(currentScript.value.scriptId)
    ElMessage.success('删除成功')
    router.push({ name: 'DataDevIde' })
  } catch (error) {
    const message = extractErrorMessage(error, '删除作业失败')
    showWorkspaceFeedback('error', '删除作业失败', message)
    ElMessage.error(message)
  }
}

onMounted(async () => {
  await Promise.all([loadModelOptions(), loadCurrentScript(Number(route.params.scriptId))])
})

watch(
  () => route.params.scriptId,
  async (scriptId, oldScriptId) => {
    const nextScriptId = Number(scriptId)
    const prevScriptId = Number(oldScriptId)
    if (!nextScriptId || nextScriptId === prevScriptId) return
    if (!(await confirmDiscardChanges('当前作业有未保存修改，切换作业将丢失内容，是否继续？'))) {
      await router.replace(`/datadev/ide/detail/${prevScriptId || currentScript.value?.scriptId}`)
      return
    }
    await loadCurrentScript(nextScriptId)
  },
)

onBeforeRouteLeave(async () => {
  return await confirmDiscardChanges()
})
</script>

<style lang="scss" scoped>
.job-detail-page {
  min-height: calc(100vh - 84px);
  padding: 18px;
  background: #f5f7fb;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-feedback {
  border-radius: 14px;
}

.page-header,
.card-header,
.header-actions,
.meta-tags,
.editor-actions {
  display: flex;
  gap: 12px;
}

.page-header,
.card-header {
  align-items: flex-start;
  justify-content: space-between;
}

.page-path {
  margin: 0 0 8px;
  font-size: 12px;
  color: #8a97a8;
}

.page-header h1,
.card-header h3 {
  margin: 0;
  color: #213044;
}

.page-header p,
.card-header p {
  margin: 8px 0 0;
  color: #66768b;
  line-height: 1.7;
}

.header-actions,
.meta-tags,
.editor-actions {
  flex-wrap: wrap;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.65fr);
  gap: 16px;
}

.main-column,
.side-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.detail-card {
  border-radius: 16px;
  border: 1px solid #e6ebf2;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.editor-card :deep(.code-editor),
.editor-card :deep(.editor-wrap) {
  min-height: 520px;
}

.side-column :deep(.activity-panel) {
  min-height: 640px;
}

@media (max-width: 1280px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .job-detail-page {
    min-height: calc(100vh - 72px);
    padding: 12px;
  }

  .page-header,
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
