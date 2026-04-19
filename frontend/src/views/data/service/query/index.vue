<template>
  <div class="app-container query-page">
    <el-tabs v-model="active" type="card" @tab-click="onTabClick" @tab-remove="removeTab" :before-leave="beforeLeave">
      <el-tab-pane v-for="t in tabs" :key="t.key" :name="t.key" :label="t.title" :closable="tabs.length > 1">
        <div class="tab-content">
          <splitpanes horizontal class="query-splitpanes default-theme" @resized="event => onPaneResized(t, event)">
            <pane :size="t.splitSize" :min-size="20">
              <div class="pane-inner">
                <query-view
                  :dataSourceId="t.dataSourceId"
                  :sqlText="t.sqlText"
                  :pageSize="t.pageSize"
                  :offset="t.offset"
                  :templateParams="t.templateParams"
                  :next="t.next"
                  :ds-list="dsList"
                  :running="t.running"
                  :hasResult="t.columns.length > 0"
                  @update:dataSourceId="v => (t.dataSourceId = v)"
                  @update:sqlText="v => (t.sqlText = v)"
                  @update:pageSize="v => (t.pageSize = v)"
                  @update:offset="v => (t.offset = v)"
                  @update:templateParams="v => (t.templateParams = v)"
                  @run="(p) => runQuery(t, p)"
                  @export="(p) => exportRows(t, p)"
                  @publish="() => openPublishDialog(t)"
                />
              </div>
            </pane>
            <pane :size="100 - t.splitSize" :min-size="15">
              <div class="pane-inner">
                <div v-if="t.columns.length === 0" class="empty-result">
                  <el-empty description="执行查询后在此显示结果" :image-size="80" />
                </div>
                <query-result v-else :columns="t.columns" :rows="t.rows" result-height="100%" />
              </div>
            </pane>
          </splitpanes>
        </div>
      </el-tab-pane>
      <el-tab-pane :name="addKey" label="新增查询">
        <template #label>
          <el-icon><Plus /></el-icon>
        </template>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="publishOpen" title="发布为数据接口" width="720px" append-to-body>
      <el-alert
        title="发布后会自动进入接口管理，并根据当前模板参数生成请求参数、根据当前查询结果生成响应字段。"
        type="info"
        :closable="false"
        style="margin-bottom: 16px;"
      />
      <el-form ref="publishFormRef" :model="publishForm" :rules="publishRules" label-width="120px">
        <el-form-item label="数据源">
          <el-input :model-value="getDatasourceLabel(publishForm.dataSourceId)" disabled />
        </el-form-item>
        <el-form-item label="接口名称" prop="interfaceName">
          <el-input v-model="publishForm.interfaceName" placeholder="请输入接口名称" @blur="syncPublishCode" />
        </el-form-item>
        <el-form-item label="接口编码" prop="interfaceCode">
          <el-input v-model="publishForm.interfaceCode" placeholder="请输入接口编码，仅支持字母数字中划线下划线" @blur="normalizePublishCode" />
        </el-form-item>
        <el-form-item label="接口描述" prop="interfaceDesc">
          <el-input v-model="publishForm.interfaceDesc" type="textarea" :rows="2" placeholder="可选：补充接口用途说明" />
        </el-form-item>
        <el-form-item label="是否合计" prop="isTotal">
          <el-radio-group v-model="publishForm.isTotal">
            <el-radio value="1">是</el-radio>
            <el-radio value="0">否</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="合计SQL" prop="totalSql">
          <el-input
            v-model="publishForm.totalSql"
            type="textarea"
            :rows="3"
            :placeholder="publishForm.isTotal === '1' ? '请输入合计 SQL' : '未启用合计时可留空'"
          />
        </el-form-item>
        <el-form-item label="是否分页" prop="isPaging">
          <el-radio-group v-model="publishForm.isPaging">
            <el-radio value="1">是</el-radio>
            <el-radio value="0">否</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="接口状态" prop="enable">
          <el-radio-group v-model="publishForm.enable">
            <el-radio value="1">启用</el-radio>
            <el-radio value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="模板参数">
          <div class="publish-tag-group">
            <el-tag v-if="Object.keys(publishForm.params || {}).length === 0" type="info" effect="plain">无模板参数</el-tag>
            <el-tag v-for="(value, key) in publishForm.params" :key="key" type="warning" effect="plain">
              {{ key }}={{ value }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="响应字段">
          <div class="publish-tag-group">
            <el-tag v-for="column in publishForm.outputColumns" :key="column" type="success" effect="plain">
              {{ column }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="接口SQL">
          <el-input :model-value="publishForm.sql" type="textarea" :rows="6" readonly />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="publishOpen = false">取消</el-button>
          <el-button type="primary" :loading="publishLoading" @click="submitPublish">发布</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="DataServiceQuery">
import { getCurrentInstance } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'
import { listDatasource } from '@/api/data/datasource'
import { executeQuery, exportQuery, publishQueryAsInterface } from '@/api/data/service'
import QueryView from './queryView.vue'
import QueryResult from './queryResult.vue'

const { proxy } = getCurrentInstance()

const active = ref('')
const tabs = ref([])
const dsList = ref([])
const addKey = '__add__'
const publishOpen = ref(false)
const publishLoading = ref(false)
const publishFormRef = ref(null)
const publishForm = ref(createPublishForm())
function validatePublishTotalSql(rule, value, callback) {
  if (publishForm.value.isTotal === '1' && !String(value || '').trim()) {
    callback(new Error('启用合计时必须填写合计SQL'))
    return
  }
  callback()
}

const publishRules = {
  interfaceName: [{ required: true, message: '接口名称不能为空', trigger: 'blur' }],
  interfaceCode: [
    { required: true, message: '接口编码不能为空', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '接口编码仅支持字母、数字、中划线和下划线', trigger: 'blur' }
  ],
  totalSql: [{ validator: validatePublishTotalSql, trigger: 'blur' }]
}

const DEFAULT_SPLIT = 55

function createPublishForm() {
  return {
    dataSourceId: undefined,
    sql: '',
    params: {},
    outputColumns: [],
    interfaceName: '',
    interfaceCode: '',
    interfaceDesc: '由 SQL 查询模块发布',
    isTotal: '0',
    totalSql: '',
    isPaging: '1',
    enable: '1'
  }
}

function buildInterfaceCode(name) {
  const normalized = String(name || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
  return normalized || `sql_interface_${Date.now()}`
}

function onPaneResized(tab, event) {
  const first = event?.[0]
  if (first) {
    tab.splitSize = Number(first.size.toFixed(1))
  }
}

function addTab() {
  const key = 'new-' + Date.now()
  tabs.value.push({
    key,
    title: '查询页',
    dataSourceId: undefined,
    sqlText: '',
    templateParams: {},
    pageSize: 20,
    offset: 0,
    next: null,
    columns: [],
    rows: [],
    running: false,
    splitSize: DEFAULT_SPLIT,
  })
  active.value = key
}

function removeTab(name) {
  if (tabs.value.length <= 1) {
    proxy.$modal.msgWarning('至少保留一个查询页')
    return
  }
  const idx = tabs.value.findIndex(t => t.key === name)
  if (idx >= 0) {
    tabs.value.splice(idx, 1)
    if (tabs.value.length) active.value = tabs.value[Math.max(0, idx - 1)].key
  }
}

function runQuery(t, p) {
  if (!t.dataSourceId || !t.sqlText) {
    proxy.$modal.msgError('请选择数据源并输入SQL')
    return
  }
  t.running = true
  const payload = { dataSourceId: t.dataSourceId, sql: t.sqlText, params: t.templateParams || {} }
  if (p && typeof p.pageSize !== 'undefined') payload.pageSize = p.pageSize
  if (p && typeof p.offset !== 'undefined') payload.offset = p.offset
  executeQuery(payload).then(res => {
    applyResult(t, res.data)
    proxy.$modal.msgSuccess('查询成功')
  }).finally(() => {
    t.running = false
  })
}

function exportRows(t, p) {
  if (!t.dataSourceId || !t.sqlText) {
    proxy.$modal.msgError('请选择数据源并输入SQL')
    return
  }
  const payload = { dataSourceId: t.dataSourceId, sql: t.sqlText, params: (p && p.params) || t.templateParams || {} }
  if (p && typeof p.pageSize !== 'undefined') payload.pageSize = p.pageSize
  if (p && typeof p.offset !== 'undefined') payload.offset = p.offset
  exportQuery(payload).then(res => {
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'query_export.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    proxy.$modal.msgSuccess('导出成功')
  }).catch(err => {
    proxy.$modal.msgError(err?.msg || '导出失败')
  })
}

function applyResult(t, data) {
  const cols = data?.columns || []
  const rows = data?.rows || []
  t.columns = cols
  t.rows = rows.map(row => {
    const item = {}
    for (let i = 0; i < cols.length; i++) item[i] = row[i]
    return item
  })
  t.next = data?.next || null
}

function getDsList() {
  listDatasource().then(res => {
    dsList.value = res.rows || []
  })
}

function getDatasourceLabel(dataSourceId) {
  const dataSource = dsList.value.find(item => item.dataSourceId === dataSourceId)
  if (!dataSource) return ''
  return `${dataSource.dataSourceName} (${dataSource.dbType})`
}

function syncPublishCode() {
  if (!publishForm.value.interfaceCode) {
    publishForm.value.interfaceCode = buildInterfaceCode(publishForm.value.interfaceName)
  }
}

function normalizePublishCode() {
  publishForm.value.interfaceCode = buildInterfaceCode(publishForm.value.interfaceCode)
}

function openPublishDialog(tab) {
  if (!tab.dataSourceId || !tab.sqlText || !tab.columns.length) {
    proxy.$modal.msgError('请先执行 SQL，确保结果字段可识别后再发布接口')
    return
  }
  publishForm.value = createPublishForm()
  publishForm.value.dataSourceId = tab.dataSourceId
  publishForm.value.sql = tab.sqlText
  publishForm.value.params = { ...(tab.templateParams || {}) }
  publishForm.value.outputColumns = [...(tab.columns || [])]
  publishForm.value.interfaceName = `${getDatasourceLabel(tab.dataSourceId) || 'SQL 查询'}接口`
  publishForm.value.interfaceCode = buildInterfaceCode(publishForm.value.interfaceName)
  publishOpen.value = true
  nextTick(() => proxy.resetForm('publishFormRef'))
}

function submitPublish() {
  publishFormRef.value.validate(valid => {
    if (!valid) return
    publishLoading.value = true
    publishQueryAsInterface(publishForm.value).then(() => {
      proxy.$modal.msgSuccess('发布成功，已添加到接口管理')
      publishOpen.value = false
    }).finally(() => {
      publishLoading.value = false
    })
  })
}

function onTabClick(tab) {
  if (tab.paneName === addKey) {
    addTab()
  }
}

function beforeLeave(activeName) {
  return activeName !== addKey
}

onMounted(() => {
  getDsList()
  addTab()
})
</script>

<style scoped>
.query-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 84px);
  overflow: hidden;
}

.query-page :deep(.el-tabs) {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.query-page :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.query-page :deep(.el-tab-pane) {
  height: 100%;
}

.tab-content {
  height: 100%;
  overflow: hidden;
}

.query-splitpanes {
  height: 100%;
}

.pane-inner {
  height: 100%;
  overflow: hidden;
}

:deep(.query-splitpanes > .splitpanes__pane) {
  background-color: transparent;
}

.empty-result {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.publish-tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

:deep(.query-splitpanes > .splitpanes__splitter) {
  background: #f0f2f5;
  border-top: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
  height: 7px;
  position: relative;
  transition: background 0.2s;
}

:deep(.query-splitpanes > .splitpanes__splitter::before) {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 40px;
  height: 4px;
  border-radius: 2px;
  transform: translate(-50%, -50%);
  background: #c0c4cc;
  transition: background 0.2s;
}

:deep(.query-splitpanes > .splitpanes__splitter:hover) {
  background: #e6e9ed;
}

:deep(.query-splitpanes > .splitpanes__splitter:hover::before) {
  background: #409eff;
}
</style>
