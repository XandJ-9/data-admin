<template>
  <div class="dev-ide">
    <splitpanes class="default-theme ide-splitpanes">
      <!-- 左侧面板 -->
      <pane :size="sideSize" :min-size="12" :max-size="30">
        <side-panel
          :scripts="scriptList"
          :active-script-id="currentScript?.scriptId"
          @select="openScript"
          @create="onStartCreate"
          @layer-change="onLayerChange"
        />
      </pane>

      <!-- 中央编辑器 -->
      <pane :size="editorSize" :min-size="30">
        <div class="editor-workspace">
          <div class="editor-tabs-wrap">
            <el-tabs
              v-model="activeTabName"
              type="card"
              class="editor-tabs"
              closable
              @tab-remove="closeEditorTab"
            >
              <el-tab-pane
                v-for="tab in openTabs"
                :key="tab.scriptId"
                :name="String(tab.scriptId)"
                :closable="openTabs.length > 1"
              >
                <template #label>
                  <span class="tab-label" :title="tab.scriptName">
                    {{ tab.scriptName }}
                    <span v-if="tab.content !== tab.savedContent" class="tab-dirty-dot" />
                  </span>
                </template>
              </el-tab-pane>
            </el-tabs>
            <div v-if="openTabs.length === 0" class="editor-empty">
              <h3>脚本研发中心</h3>
              <p>从左侧资源树选择或新建脚本，支持 SQL / Python 多页签并行开发。</p>
            </div>
          </div>

          <splitpanes v-if="currentScript" horizontal class="editor-result-split default-theme">
            <pane :size="editorVSplit" :min-size="25">
              <code-editor
                ref="editorRef"
                v-model="content"
                :lang="scriptLang"
                :running="running"
                :has-change="hasChange"
                :script-name="currentScript?.scriptName || ''"
                @run="handleRun"
                @save="handleSave"
                @publish="handlePublish"
                @fullscreen="showFullscreen = true"
              />
            </pane>
            <pane :size="100 - editorVSplit" :min-size="15">
              <result-panel
                :columns="resultColumns"
                :rows="resultRows"
                :duration="resultDuration"
                :lineage-data="lineageData"
                :execution-plan="executionPlan"
                :logs="logs"
              />
            </pane>
          </splitpanes>
        </div>
      </pane>

      <!-- 右侧面板：版本历史 + 执行记录 -->
      <pane :size="rightSize" :min-size="15" :max-size="35">
        <div class="right-panel">
          <el-tabs v-model="rightTab" class="right-tabs">
            <el-tab-pane label="版本历史" name="versions">
              <el-scrollbar class="right-scroll">
                <div class="version-filter">
                  <el-radio-group v-model="versionView" size="small">
                    <el-radio-button label="all">全部</el-radio-button>
                    <el-radio-button label="released">正式</el-radio-button>
                    <el-radio-button label="draft">草稿</el-radio-button>
                  </el-radio-group>
                </div>
                <div v-if="filteredVersions.length === 0" class="empty-tip">{{ versionEmptyText }}</div>
                <div
                  v-for="v in filteredVersions"
                  :key="v.versionId"
                  class="version-item"
                  :class="{ current: v.isCurrent }"
                >
                  <div class="version-head">
                    <span class="version-num">v{{ v.versionNumber }}</span>
                    <div class="version-tags">
                      <el-tag :type="v.isReleased ? 'success' : 'info'" size="small" effect="plain">
                        {{ v.isReleased ? '正式' : '草稿' }}
                      </el-tag>
                      <el-tag v-if="v.isCurrent" type="success" size="small" effect="plain">当前</el-tag>
                    </div>
                    <el-button
                      v-if="!v.isCurrent && v.isReleased"
                      link type="primary" size="small"
                      @click="handleRollback(v)"
                    >回滚</el-button>
                  </div>
                  <div class="version-meta">
                    <span>{{ v.createBy || '-' }}</span>
                    <span>{{ v.createTime }}</span>
                  </div>
                  <div v-if="v.changeLog" class="version-log">{{ v.changeLog }}</div>
                </div>
              </el-scrollbar>
            </el-tab-pane>
            <el-tab-pane label="执行记录" name="executions">
              <el-scrollbar class="right-scroll">
                <div v-if="executions.length === 0" class="empty-tip">暂无记录</div>
                <div v-for="e in executions" :key="e.executionId" class="exec-item">
                  <div class="exec-head">
                    <el-tag :type="execTagType(e.status)" size="small" effect="plain">
                      {{ execStatusLabel(e.status) }}
                    </el-tag>
                    <span class="exec-time">{{ e.createTime }}</span>
                  </div>
                  <div class="exec-meta">
                    <span v-if="e.durationSeconds !== null">耗时 {{ e.durationSeconds }}s</span>
                    <span>{{ e.executedBy }}</span>
                  </div>
                  <div v-if="e.errorMessage" class="exec-error">{{ e.errorMessage }}</div>
                </div>
              </el-scrollbar>
            </el-tab-pane>
          </el-tabs>
        </div>
      </pane>
    </splitpanes>

    <!-- 底部状态栏 -->
    <status-bar
      :status="execStatus"
      :script-name="currentScript?.scriptName || ''"
      :version="currentVersion"
      :lang="scriptLang"
      :cursor-info="cursorInfo"
      :datasource-name="currentDsName"
    />

    <!-- 新建脚本对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建 Spark SQL 脚本" width="480px" :close-on-click-modal="false">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="80px">
        <el-form-item label="脚本名称" prop="scriptName">
          <el-input v-model="createForm.scriptName" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="脚本编码" prop="scriptCode">
          <el-input v-model="createForm.scriptCode" placeholder="唯一编码，如 ods_user_sync" />
        </el-form-item>
          <el-form-item label="数仓分层">
            <el-select v-model="createForm.layer" placeholder="选择分层（可选）" clearable style="width: 100%">
              <el-option label="ODS 贴源层" value="ODS" />
              <el-option label="DWD 明细层" value="DWD" />
              <el-option label="DWS 汇总层" value="DWS" />
              <el-option label="ADS 应用层" value="ADS" />
            </el-select>
          </el-form-item>
          <el-form-item label="执行器">
            <el-tag type="success" effect="plain">Spark SQL 执行引擎（固定）</el-tag>
          </el-form-item>
          <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 全屏编辑器 -->
    <el-dialog v-model="showFullscreen" title="全屏编辑" width="90%" top="3vh" :close-on-click-modal="false">
      <code-editor
        v-model="content"
        :lang="scriptLang"
        :running="running"
        :has-change="hasChange"
        :theme="'xcode'"
        @run="handleRun"
        @save="handleSave"
        @publish="handlePublish"
        style="height: 80vh"
      />
    </el-dialog>

    <!-- 保存版本对话框 -->
    <el-dialog v-model="showSaveDialog" :title="saveMode === 'publish' ? '发布版本' : '保存草稿版本'" width="420px">
      <el-input v-model="saveChangeLog" type="textarea" :rows="3" placeholder="变更说明（可选）" />
      <template #footer>
        <el-button @click="showSaveDialog = false">取消</el-button>
        <el-button :type="saveMode === 'publish' ? 'success' : 'primary'" @click="confirmSave" :loading="saving">
          {{ saveMode === 'publish' ? '发布' : '保存草稿' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import {
  listScripts, getScript, addScript,
  listVersions, createVersion, publishVersion, rollbackVersion,
  executeScript, listScriptExecutions,
} from '@/api/data/datadev'

import SidePanel  from './components/SidePanel.vue'
import CodeEditor from './components/CodeEditor.vue'
import ResultPanel from './components/ResultPanel.vue'
import StatusBar  from './components/StatusBar.vue'

defineOptions({ name: 'DataDevIde' })

// ── 布局 ────────────────────────────────
const sideSize = ref(18)
const editorSize = ref(57)
const rightSize = ref(25)
const editorVSplit = ref(60)

const currentDsName = computed(() => 'Spark SQL')

// ── 脚本列表 ────────────────────────────
const scriptList = ref([])
async function loadScripts() {
  try {
    const res = await listScripts()
    scriptList.value = res.rows || res.data || []
  } catch (error) {
    scriptList.value = []
    console.warn('[datadev] 加载脚本列表失败', error)
  }
}

// ── 当前脚本 ────────────────────────────
const openTabs = ref([])
const activeTabScriptId = ref(null)
const editorRef = ref(null)
const cursorInfo = ref(null)

const activeTabName = computed({
  get: () => (activeTabScriptId.value ? String(activeTabScriptId.value) : ''),
  set: (val) => {
    const scriptId = Number(val)
    switchEditorTab(scriptId)
  },
})

const currentScript = computed(() =>
  openTabs.value.find((item) => item.scriptId === activeTabScriptId.value) || null,
)

const content = computed({
  get: () => currentScript.value?.content || '',
  set: (val) => {
    if (!currentScript.value) return
    currentScript.value.content = val
  },
})

const scriptLang = computed(() => currentScript.value?.scriptType || 'sql')
const currentVersion = computed(() => currentScript.value?.versionNumber || 0)

const hasChange = computed(() => {
  if (!currentScript.value) return false
  return currentScript.value.content !== currentScript.value.savedContent
})

async function openScript(script) {
  stopExecutionStatusPolling()
  try {
    const res = await getScript(script.scriptId)
    const data = res.data
    const tabPayload = {
      scriptId: data.scriptId,
      scriptName: data.scriptName,
      scriptCode: data.scriptCode,
      content: data.content || '',
      savedContent: data.content || '',
      scriptType: data.scriptType || 'sql',
      datasourceId: data.datasourceId || null,
      versionNumber: data.versionNumber || 0,
    }

    const tabIndex = openTabs.value.findIndex((item) => item.scriptId === data.scriptId)
    if (tabIndex >= 0) {
      openTabs.value[tabIndex] = {
        ...openTabs.value[tabIndex],
        ...tabPayload,
      }
    } else {
      openTabs.value.push(tabPayload)
    }

    activeTabScriptId.value = data.scriptId
    await switchEditorTab(data.scriptId)
  } catch (e) {
    console.warn('[datadev] 打开脚本失败', e)
    ElMessage.error('打开脚本失败')
  }
}

async function switchEditorTab(scriptId) {
  if (!scriptId) return
  stopExecutionStatusPolling()
  activeTabScriptId.value = scriptId
  await loadVersions(scriptId)
  await loadExecutions(scriptId)
}

async function closeEditorTab(tabName) {
  const scriptId = Number(tabName)
  const tab = openTabs.value.find((item) => item.scriptId === scriptId)
  if (!tab) return

  if (tab.content !== tab.savedContent) {
    try {
      await ElMessageBox.confirm('当前页签有未保存内容，确认关闭？', '关闭确认', {
        type: 'warning',
        confirmButtonText: '确认关闭',
        cancelButtonText: '继续编辑',
      })
    } catch {
      return
    }
  }

  const removeIndex = openTabs.value.findIndex((item) => item.scriptId === scriptId)
  openTabs.value.splice(removeIndex, 1)

  if (activeTabScriptId.value === scriptId) {
    const next = openTabs.value[Math.min(removeIndex, openTabs.value.length - 1)] || null
    if (next) {
      await switchEditorTab(next.scriptId)
    } else {
      activeTabScriptId.value = null
      versions.value = []
      executions.value = []
      logs.value = []
      execStatus.value = 'idle'
      stopExecutionStatusPolling()
    }
  }
}

// ── 创建脚本 ────────────────────────────
const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref(null)
const selectedLayer = ref('')
const createForm = reactive({
  scriptName: '',
  scriptCode: '',
  layer: '',
  description: '',
})
const createRules = {
  scriptName: [{ required: true, message: '请输入脚本名称', trigger: 'blur' }],
  scriptCode: [{ required: true, message: '请输入脚本编码', trigger: 'blur' }],
}

function onLayerChange(layerKey) {
  selectedLayer.value = layerKey || ''
}

// 点击数据目录中数据源节点的 + 按钮，or 顶部新建按钮
function onStartCreate(dsData) {
  createForm.scriptName = ''
  createForm.scriptCode = ''
  createForm.description = ''
  createForm.layer = dsData?.layerKey || selectedLayer.value || ''
  showCreateDialog.value = true
  nextTick(() => {
    createFormRef.value?.clearValidate()
  })
}

async function submitCreate() {
  try {
    await createFormRef.value.validate()
  } catch { return }
  creating.value = true
  try {
    await addScript({ ...createForm, scriptType: 'sql' })
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    Object.assign(createForm, { scriptName: '', scriptCode: '', layer: '', description: '' })
    loadScripts()
  } catch (e) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

// ── 版本管理 ────────────────────────────
const versions = ref([])
const versionView = ref('all')
const filteredVersions = computed(() => {
  if (versionView.value === 'released') return versions.value.filter((v) => v.isReleased)
  if (versionView.value === 'draft') return versions.value.filter((v) => !v.isReleased)
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
  } catch (error) {
    versions.value = []
    console.warn('[datadev] 加载版本列表失败', error)
  }
}

const showSaveDialog = ref(false)
const saveChangeLog = ref('')
const saving = ref(false)
const saveMode = ref('draft')

function handleSave() {
  if (!currentScript.value) {
    ElMessage.warning('请先打开一个脚本')
    return
  }
  saveMode.value = 'draft'
  saveChangeLog.value = ''
  showSaveDialog.value = true
}

function handlePublish() {
  if (!currentScript.value) {
    ElMessage.warning('请先打开一个脚本')
    return
  }
  saveMode.value = 'publish'
  saveChangeLog.value = ''
  showSaveDialog.value = true
}

async function confirmSave() {
  saving.value = true
  try {
    const scriptId = currentScript.value?.scriptId
    if (!scriptId) {
      ElMessage.warning('请先打开一个脚本')
      return
    }
    if (saveMode.value === 'publish') {
      await publishVersion(scriptId, {
        content: content.value,
        changeLog: saveChangeLog.value,
      })
    } else {
      await createVersion(scriptId, {
        content: content.value,
        changeLog: saveChangeLog.value,
      })
    }
    currentScript.value.savedContent = content.value
    currentScript.value.versionNumber = currentScript.value.versionNumber + 1
    ElMessage.success(saveMode.value === 'publish' ? '发布成功' : '草稿版本保存成功')
    showSaveDialog.value = false

    await Promise.allSettled([
      loadVersions(scriptId),
      openScript({ scriptId }),
      loadScripts(),
    ])
  } catch {
    ElMessage.error(saveMode.value === 'publish' ? '发布失败' : '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleRollback(ver) {
  try {
    await ElMessageBox.confirm(`确认回滚到 v${ver.versionNumber}？`, '回滚确认')
  } catch { return }
  try {
    await rollbackVersion(currentScript.value.scriptId, ver.versionId)
    ElMessage.success('回滚成功')
    openScript(currentScript.value)
  } catch {
    ElMessage.error('回滚失败')
  }
}

// ── 执行 ────────────────────────────────
const running = ref(false)
const execStatus = ref('idle')
const resultColumns = ref([])
const resultRows = ref([])
const resultDuration = ref(null)
const lineageData = ref(null)
const executionPlan = ref(null)
const logs = ref([])

async function handleRun() {
  if (!currentScript.value) {
    ElMessage.warning('请先打开一个脚本')
    return
  }
  stopExecutionStatusPolling()
  running.value = true
  execStatus.value = 'running'
  logs.value = [{ time: new Date().toLocaleTimeString(), message: '开始执行...', level: 'info' }]

  try {
    const res = await executeScript(currentScript.value.scriptId)
    const executionId = res.data?.executionId || ''
    execStatus.value = 'pending'
    logs.value.push({ time: new Date().toLocaleTimeString(), message: `已提交 Spark SQL 执行请求，ID: ${executionId || '-'}（待执行器处理）`, level: 'info' })

    // 刷新执行记录
    await loadExecutions(currentScript.value.scriptId)
    if (executionId) {
      startExecutionStatusPolling(currentScript.value.scriptId, executionId)
    }
  } catch (e) {
    const errorMessage = e instanceof Error ? e.message : String(e)
    execStatus.value = 'failed'
    logs.value.push({ time: new Date().toLocaleTimeString(), message: `执行失败: ${errorMessage || '未知错误'}`, level: 'error' })
  } finally {
    running.value = false
  }
}

// ── 执行记录 ────────────────────────────
const executions = ref([])
const rightTab = ref('versions')
const executionStatusPollTimer = ref(null)

function stopExecutionStatusPolling() {
  if (executionStatusPollTimer.value) {
    clearInterval(executionStatusPollTimer.value)
    executionStatusPollTimer.value = null
  }
}

function startExecutionStatusPolling(scriptId, executionId) {
  stopExecutionStatusPolling()
  const maxAttempts = 10
  const maxConsecutiveFailures = 3
  let attempts = 0
  let consecutiveFailures = 0

  executionStatusPollTimer.value = setInterval(async () => {
    attempts += 1
    try {
      const res = await listScriptExecutions(scriptId, { pageNum: 1, pageSize: 20 })
      consecutiveFailures = 0
      const items = res.rows || res.data || []
      const target = items.find((item) => item.executionId === executionId)

      if (target?.status === 'pending' || target?.status === 'running') {
        execStatus.value = target.status
      }

      if (target && ['success', 'failed', 'cancelled'].includes(target.status)) {
        execStatus.value = target.status
        logs.value.push({
          time: new Date().toLocaleTimeString(),
          message: `执行结束，状态: ${execStatusLabel(target.status)}`,
          level: target.status === 'success' ? 'info' : target.status === 'cancelled' ? 'warn' : 'error',
        })
        stopExecutionStatusPolling()
        await loadExecutions(scriptId)
        return
      }
    } catch {
      consecutiveFailures += 1
      if (consecutiveFailures >= maxConsecutiveFailures) {
        stopExecutionStatusPolling()
        logs.value.push({
          time: new Date().toLocaleTimeString(),
          message: '执行状态查询失败，请稍后在执行记录中手动刷新',
          level: 'error',
        })
        return
      }
    }

    if (attempts >= maxAttempts) {
      stopExecutionStatusPolling()
      await loadExecutions(scriptId)
      logs.value.push({
        time: new Date().toLocaleTimeString(),
        message: '执行状态仍在处理中，可稍后在执行记录中刷新查看',
        level: 'warn',
      })
    }
  }, 2000)
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

function execTagType(status) {
  const map = { pending: 'info', running: 'warning', success: 'success', failed: 'danger', cancelled: 'info' }
  return map[status] || 'info'
}
function execStatusLabel(status) {
  const map = { pending: '已提交', running: '执行中', success: '成功', failed: '失败', cancelled: '已取消' }
  return map[status] || status
}

// ── 全屏编辑 ────────────────────────────
const showFullscreen = ref(false)

// ── 初始化 ──────────────────────────────
onMounted(() => {
  loadScripts()
})

onBeforeUnmount(() => {
  stopExecutionStatusPolling()
})
</script>

<style lang="scss" scoped>
.dev-ide {
  --dev-bg: linear-gradient(140deg, #f7f3ea 0%, #eef6f5 55%, #f4f7fb 100%);
  --panel-bg: rgba(255, 255, 255, 0.9);
  --panel-border: #d7dee8;
  --ink-title: #213044;
  --ink-sub: #66768b;
  --accent: #1f8f7a;
  --accent-soft: #e5f6f1;

  display: flex;
  flex-direction: column;
  height: calc(100vh - 84px);
  background: var(--dev-bg);
  padding: 10px;
  gap: 8px;
  font-family: 'Manrope', 'SF Pro Display', 'PingFang SC', sans-serif;
}

.ide-splitpanes {
  flex: 1;
  min-height: 0;

  :deep(.splitpanes__pane) {
    border: 1px solid var(--panel-border);
    border-radius: 12px;
    overflow: hidden;
    background: var(--panel-bg);
    box-shadow: 0 12px 24px rgba(22, 39, 58, 0.06);
  }

  :deep(.splitpanes__splitter) {
    background: transparent;
    margin: 0 2px;
  }
}

.editor-result-split {
  height: 100%;
}

.editor-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.editor-tabs-wrap {
  padding: 10px 12px 0;
  border-bottom: 1px solid #dbe3ec;
  background: linear-gradient(180deg, #fbfcfd 0%, #f4f8fb 100%);
}

.editor-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }
  :deep(.el-tabs__item) {
    border-radius: 8px 8px 0 0;
    font-weight: 600;
  }
  :deep(.el-tabs__item.is-active) {
    color: var(--accent);
  }
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tab-dirty-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #f08b35;
  box-shadow: 0 0 0 3px rgba(240, 139, 53, 0.2);
}

.editor-empty {
  margin: 18px 4px 14px;
  padding: 24px;
  border: 1px dashed #c6d5e7;
  border-radius: 10px;
  background: #fcfdfd;
  h3 {
    margin: 0;
    font-size: 18px;
    color: var(--ink-title);
  }
  p {
    margin: 8px 0 0;
    color: var(--ink-sub);
    font-size: 13px;
  }
}

/* 右侧面板 */
.right-panel {
  height: 100%;
  background: transparent;
  display: flex;
  flex-direction: column;
}
.right-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  :deep(.el-tabs__header) {
    margin-bottom: 0;
    padding: 0 12px;
  }
  :deep(.el-tabs__content) {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
  :deep(.el-tab-pane) {
    height: 100%;
  }
}

.right-scroll {
  height: 100%;
  padding: 8px;
}

.version-filter {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.empty-tip {
  text-align: center;
  color: var(--ink-sub);
  font-size: 13px;
  padding: 32px 0;
}

.executor-hint {
  font-size: 13px;
  color: #909399;
}

/* 版本条目 */
.version-item {
  padding: 10px 12px;
  border-radius: 10px;
  margin-bottom: 6px;
  border: 1px solid #e5ebf3;
  background: #fbfdff;
  &.current {
    border-color: #9ad7b7;
    background: var(--accent-soft);
  }
}
.version-head {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
}
.version-tags {
  display: flex;
  align-items: center;
  gap: 6px;
}
.version-num {
  font-weight: 600;
  font-size: 13px;
  color: #303133;
}
.version-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.version-log {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}

/* 执行记录条目 */
.exec-item {
  padding: 10px 12px;
  border-radius: 10px;
  margin-bottom: 6px;
  border: 1px solid #e5ebf3;
  background: #fbfdff;
}
.exec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.exec-time {
  font-size: 12px;
  color: #909399;
}
.exec-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.exec-error {
  font-size: 12px;
  color: #f56c6c;
  margin-top: 4px;
  word-break: break-all;
}

@media (max-width: 1024px) {
  .dev-ide {
    padding: 6px;
  }
  .tab-label {
    max-width: 140px;
  }
}

@media (max-width: 768px) {
  .dev-ide {
    height: calc(100vh - 72px);
  }
  .editor-tabs-wrap {
    padding: 6px 8px 0;
  }
  .editor-empty {
    padding: 16px;
    h3 { font-size: 16px; }
    p { font-size: 12px; }
  }
  .right-scroll {
    padding: 6px;
  }
}
</style>
