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
        <splitpanes horizontal class="editor-result-split default-theme">
          <pane :size="editorVSplit" :min-size="25">
            <code-editor
              ref="editorRef"
              v-model="content"
              :lang="scriptLang"
              :running="running"
              :has-change="hasChange"
              @run="handleRun"
              @save="handleSave"
              @publish="handlePublish"
              @fullscreen="showFullscreen = true"
            />
          </pane>
          <!-- 底部结果区（编辑器下方，占据中央+右侧） -->
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
      </pane>

      <!-- 右侧面板：版本历史 + 执行记录 -->
      <pane :size="rightSize" :min-size="15" :max-size="35">
        <div class="right-panel">
          <el-tabs v-model="rightTab" class="right-tabs">
            <el-tab-pane label="版本历史" name="versions">
              <el-scrollbar class="right-scroll">
                <div v-if="versions.length === 0" class="empty-tip">暂无版本</div>
                <div
                  v-for="v in versions"
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
    <el-dialog v-model="showCreateDialog" title="新建 SQL 脚本" width="480px" :close-on-click-modal="false">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="80px">
        <el-form-item label="脚本名称" prop="scriptName">
          <el-input v-model="createForm.scriptName" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="脚本编码" prop="scriptCode">
          <el-input v-model="createForm.scriptCode" placeholder="唯一编码，如 ods_user_sync" />
        </el-form-item>
        <el-form-item label="数据源" prop="datasourceId">
          <el-select v-model="createForm.datasourceId" placeholder="选择执行数据源" clearable style="width: 100%">
            <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
          </el-select>
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
            <el-tag v-if="createExecutorInfo" type="success" effect="plain">{{ createExecutorInfo.label }}</el-tag>
            <span v-else class="executor-hint">选择数据源后自动确定</span>
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

import { listDatasource } from '@/api/data/datasource'
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

// ── 数据源 ──────────────────────────────
const dsList = ref([])
async function loadDsList() {
  try {
    const res = await listDatasource()
    dsList.value = res.rows || res.data || []
  } catch (error) {
    dsList.value = []
    console.warn('[datadev] 加载数据源失败', error)
  }
}

const currentDsName = computed(() => {
  const ds = dsList.value.find((d) => d.dataSourceId === datasourceId.value)
  return ds ? ds.dataSourceName : ''
})

// db_type → 执行器映射
const DB_TYPE_EXECUTOR_MAP = {
  mysql: { type: 'jdbc', label: 'JDBC (MySQL)' },
  postgresql: { type: 'jdbc', label: 'JDBC (PostgreSQL)' },
  postgres: { type: 'jdbc', label: 'JDBC (PostgreSQL)' },
  oracle: { type: 'jdbc', label: 'JDBC (Oracle)' },
  sqlserver: { type: 'jdbc', label: 'JDBC (SQL Server)' },
  sqlite: { type: 'jdbc', label: 'JDBC (SQLite)' },
  presto: { type: 'presto', label: 'Presto 执行器' },
  starrocks: { type: 'starrocks', label: 'StarRocks 执行器' },
  hive: { type: 'hive', label: 'Hive 执行器' },
  spark: { type: 'spark', label: 'Spark SQL 执行器' },
  sparksql: { type: 'spark', label: 'Spark SQL 执行器' },
}

function getExecutorByDbType(dbType) {
  return DB_TYPE_EXECUTOR_MAP[(dbType || '').toLowerCase()] || { type: dbType || '', label: (dbType || '') + ' 执行器' }
}

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
const currentScript = ref(null)
const content = ref('')
const savedContent = ref('')
const scriptLang = ref('sql')
const datasourceId = ref(null)
const currentVersion = ref(0)
const editorRef = ref(null)
const cursorInfo = ref(null)

const hasChange = computed(() => content.value !== savedContent.value)

async function openScript(script) {
  stopExecutionStatusPolling()
  try {
    const res = await getScript(script.scriptId)
    const data = res.data
    currentScript.value = data
    content.value = data.content || ''
    savedContent.value = data.content || ''
    scriptLang.value = data.scriptType || 'sql'
    datasourceId.value = data.datasourceId || null
    currentVersion.value = data.versionNumber || 0
    // 加载版本 & 执行记录
    loadVersions(data.scriptId)
    loadExecutions(data.scriptId)
  } catch (e) {
    console.warn('[datadev] 打开脚本失败', e)
    ElMessage.error('打开脚本失败')
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
  datasourceId: null,
  layer: '',
  description: '',
})
const createRules = {
  scriptName: [{ required: true, message: '请输入脚本名称', trigger: 'blur' }],
  scriptCode: [{ required: true, message: '请输入脚本编码', trigger: 'blur' }],
}

// 根据当前选中数据源自动计算执行器
const createExecutorInfo = computed(() => {
  if (!createForm.datasourceId) return null
  const ds = dsList.value.find((d) => d.dataSourceId === createForm.datasourceId)
  if (!ds) return null
  return getExecutorByDbType(ds.dbType)
})

function onLayerChange(layerKey) {
  selectedLayer.value = layerKey || ''
}

// 点击数据目录中数据源节点的 + 按钮，or 顶部新建按钮
function onStartCreate(dsData) {
  createForm.scriptName = ''
  createForm.scriptCode = ''
  createForm.description = ''
  createForm.datasourceId = dsData?.dsId || null
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
    Object.assign(createForm, { scriptName: '', scriptCode: '', datasourceId: null, layer: '', description: '' })
    loadScripts()
  } catch (e) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

// ── 版本管理 ────────────────────────────
const versions = ref([])
async function loadVersions(scriptId) {
  try {
    const res = await listVersions(scriptId)
    versions.value = res.data || []
  } catch { versions.value = [] }
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
    if (saveMode.value === 'publish') {
      await publishVersion(currentScript.value.scriptId, {
        content: content.value,
        changeLog: saveChangeLog.value,
      })
    } else {
      await createVersion(currentScript.value.scriptId, {
        content: content.value,
        changeLog: saveChangeLog.value,
      })
    }
    savedContent.value = content.value
    ElMessage.success(saveMode.value === 'publish' ? '发布成功' : '草稿版本保存成功')
    showSaveDialog.value = false
    await loadVersions(currentScript.value.scriptId)
    await openScript({ scriptId: currentScript.value.scriptId })
    await loadScripts()
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
    const res = await executeScript(currentScript.value.scriptId, {
      params: { datasourceId: datasourceId.value },
    })
    const executionId = res.data?.executionId || ''
    execStatus.value = 'pending'
    logs.value.push({ time: new Date().toLocaleTimeString(), message: `已提交执行，ID: ${executionId || '-'}（待执行器处理）`, level: 'info' })

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
  } catch { executions.value = [] }
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
  loadDsList()
  loadScripts()
})

onBeforeUnmount(() => {
  stopExecutionStatusPolling()
})
</script>

<style lang="scss" scoped>
.dev-ide {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 84px); // 去掉顶栏 + tagbar 高度
  background: #f0f2f5;
}

.ide-splitpanes {
  flex: 1;
  min-height: 0;
}

.editor-result-split {
  height: 100%;
}

/* 右侧面板 */
.right-panel {
  height: 100%;
  background: #fff;
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

.empty-tip {
  text-align: center;
  color: #909399;
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
  border-radius: 6px;
  margin-bottom: 6px;
  border: 1px solid #ebeef5;
  &.current { border-color: #67c23a; background: #f0f9eb; }
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
  border-radius: 6px;
  margin-bottom: 6px;
  border: 1px solid #ebeef5;
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
</style>
