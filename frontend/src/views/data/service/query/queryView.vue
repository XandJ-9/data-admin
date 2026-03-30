<template>
  <div class="query-view-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-row">
        <el-select v-model="innerDsId" placeholder="选择数据源" class="toolbar-ds">
          <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
        </el-select>
        <div class="toolbar-actions">
          <el-button type="primary" @click="emitRun" :disabled="!innerDsId || !innerSql || running" icon="Search" size="small">执行</el-button>
          <el-input-number v-model="innerPageSize" :min="1" :max="1000" size="small" class="toolbar-num" controls-position="right" />
          <span class="toolbar-label">行/页</span>
          <el-divider direction="vertical" />
          <el-button @click="showTpl = true" icon="Edit" size="small" text title="模板参数" />
          <el-button @click="showMaximize = true" icon="FullScreen" size="small" text title="放大编辑器" />
        </div>
      </div>
      <div v-if="Object.keys(currentParams).length > 0" class="param-preview">
        <el-tag v-for="(val, key) in currentParams" :key="key" type="info" effect="plain" size="small">
          {{ key }}={{ val }}
        </el-tag>
      </div>
    </div>

    <!-- SQL编辑器 -->
    <div class="editor-wrapper" ref="editorWrapperRef">
      <VAceEditor
        :value="innerSql"
        @update:value="val => innerSql = val"
        lang="sql"
        theme="xcode"
        :options="aceOptions"
        :style="{ height: actualEditorHeight + 'px', width: '100%' }"
        @init="onEditorInit"
      />
    </div>

    <!-- 翻页与导出（查询执行后显示） -->
    <div v-if="hasResult" class="bottom-bar">
      <el-button type="info" @click="emitPrev" :disabled="innerOffset <= 0 || running" icon="ArrowLeft" size="small">上一页</el-button>
      <el-button type="success" @click="emitNext" :disabled="!next || running" icon="ArrowRight" size="small">下一页</el-button>
      <el-button type="warning" @click="emitExport" :disabled="!innerDsId || !innerSql || running" icon="Download" size="small">导出</el-button>
      <span class="toolbar-label">偏移 {{ innerOffset }}</span>
      <el-button @click="innerOffset = 0" icon="Refresh" :disabled="innerOffset === 0" size="small" text title="重置偏移量" />
    </div>

    <!-- 模板参数对话框 -->
    <el-dialog v-model="showTpl" title="模板参数" width="500px">
      <div>
        <el-button size="small" type="primary" @click="addParam" icon="Plus" style="margin-bottom: 8px;">新增参数</el-button>
        <div v-for="(p, idx) in tplParams" :key="idx" class="param-row">
          <el-input v-model="p.key" placeholder="变量名" style="width: 140px" />
          <el-input v-model="p.value" placeholder="变量值" style="width: 180px" />
          <el-button type="danger" size="small" @click="removeParam(idx)" icon="Delete" />
        </div>
      </div>
      <template #footer>
        <el-button @click="showTpl = false">取消</el-button>
        <el-button type="primary" @click="saveParams">保存</el-button>
      </template>
    </el-dialog>

    <!-- 全屏SQL编辑对话框 -->
    <el-dialog v-model="showMaximize" title="SQL编辑" width="80%" top="5vh" :close-on-click-modal="false">
      <VAceEditor
        v-model:value="innerSql"
        lang="sql"
        theme="xcode"
        :options="{ ...aceOptions, fontSize: 16 }"
        style="height: 70vh; border: none; border-radius: 8px; box-shadow: 0 2px 12px #e0e1e2;"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { VAceEditor } from 'vue3-ace-editor'
import 'ace-builds/src-noconflict/ext-language_tools'
import 'ace-builds/src-noconflict/mode-sql'
import 'ace-builds/src-noconflict/snippets/sql'
import 'ace-builds/src-noconflict/theme-github'
import 'ace-builds/src-noconflict/theme-xcode'

const aceOptions = {
  fontSize: 14,
  showPrintMargin: false,
  wrap: true,
  enableBasicAutocompletion: true,
  enableLiveAutocompletion: true,
  enableSnippets: true,
}

const props = defineProps({
  dsList: { type: Array, default: () => [] },
  dataSourceId: { type: Number, default: undefined },
  sqlText: { type: String, default: '' },
  running: { type: Boolean, default: false },
  pageSize: { type: Number, default: 50 },
  offset: { type: Number, default: 0 },
  next: { type: Object, default: null },
  templateParams: { type: Object, default: () => ({}) },
  hasResult: { type: Boolean, default: false },
})

const emit = defineEmits(['update:dataSourceId', 'update:sqlText', 'update:pageSize', 'update:offset', 'update:templateParams', 'run', 'export'])

const editorWrapperRef = ref(null)
const aceInstance = ref(null)
const actualEditorHeight = ref(200)

const innerDsId = ref(props.dataSourceId)
const innerSql = ref(props.sqlText)
const innerPageSize = ref(props.pageSize)
const innerOffset = ref(props.offset)
const next = computed(() => props.next)
const showTpl = ref(false)
const showMaximize = ref(false)
const tplParams = ref(toParamEntries(props.templateParams))

const currentParams = computed(() => {
  const obj = {}
  tplParams.value.forEach(param => {
    if (param.key) obj[param.key] = param.value
  })
  return obj
})

function toParamEntries(params) {
  return Object.entries(params || {}).map(([key, value]) => ({ key, value: String(value) }))
}

function onEditorInit(editor) {
  aceInstance.value = editor
}

function recalcEditorHeight() {
  nextTick(() => {
    const wrapper = editorWrapperRef.value
    if (wrapper) {
      const h = wrapper.clientHeight
      if (h > 50) {
        actualEditorHeight.value = h
        aceInstance.value?.resize()
      }
    }
  })
}

let resizeObserver = null
onMounted(() => {
  resizeObserver = new ResizeObserver(() => recalcEditorHeight())
  if (editorWrapperRef.value) {
    resizeObserver.observe(editorWrapperRef.value)
  }
  recalcEditorHeight()
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})

watch(innerDsId, value => emit('update:dataSourceId', value))
watch(innerSql, value => emit('update:sqlText', value))
watch(innerPageSize, value => emit('update:pageSize', value))
watch(innerOffset, value => emit('update:offset', value))

watch(() => props.dataSourceId, value => { innerDsId.value = value })
watch(() => props.sqlText, value => { innerSql.value = value })
watch(() => props.pageSize, value => { innerPageSize.value = value })
watch(() => props.offset, value => { innerOffset.value = value })
watch(() => props.templateParams, value => {
  tplParams.value = toParamEntries(value)
}, { deep: true })

function emitRun() {
  emit('run', { pageSize: innerPageSize.value, offset: innerOffset.value, params: toParams() })
}

function emitExport() {
  emit('export', { pageSize: innerPageSize.value, offset: innerOffset.value, params: toParams() })
}

function emitPrev() {
  const newOffset = Number(innerOffset.value) - Number(innerPageSize.value)
  innerOffset.value = newOffset > 0 ? newOffset : 0
  emitRun()
}

function emitNext() {
  const paging = next.value
  if (!paging) return
  innerOffset.value = Number(paging.offset || 0)
  emitRun()
}

function addParam() {
  tplParams.value.push({ key: '', value: '' })
}

function removeParam(index) {
  tplParams.value.splice(index, 1)
}

function toParams() {
  const obj = {}
  tplParams.value.forEach(param => {
    if (param.key) obj[param.key] = param.value
  })
  emit('update:templateParams', obj)
  return obj
}

function saveParams() {
  toParams()
  showTpl.value = false
}
</script>

<style scoped>
.query-view-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.toolbar {
  flex-shrink: 0;
  padding: 6px 8px;
  background: #fafbfc;
  border-bottom: 1px solid #ebeef5;
}

.toolbar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-ds {
  width: 200px;
  flex-shrink: 0;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.toolbar-num {
  width: 90px;
}

.toolbar-label {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.param-preview {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.param-row {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  align-items: center;
}

.editor-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.bottom-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: #fafbfc;
  border-top: 1px solid #ebeef5;
}

@media (max-width: 768px) {
  .toolbar-ds {
    width: 100%;
  }
  .toolbar-actions {
    width: 100%;
  }
}
</style>
