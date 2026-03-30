<template>
  <div class="query-view-container">
    <el-card shadow="never" class="query-form-card">
      <el-form :inline="true" label-width="72px" class="query-form">
        <el-form-item label="数据源">
          <el-select v-model="innerDsId" placeholder="选择数据源" style="width: 220px">
            <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
          </el-select>
        </el-form-item>
        <el-form-item label="每页行数">
          <el-input-number v-model="innerPageSize" :min="1" :max="1000" style="width: 110px" />
        </el-form-item>
        <el-form-item>
          <el-tooltip content="执行SQL (Ctrl+Enter)" placement="top">
            <el-button type="primary" @click="emitRun" :disabled="!innerDsId || !innerSql || running" icon="Search" style="margin-right: 4px;">执行</el-button>
          </el-tooltip>
          <el-tooltip content="上一页" placement="top">
            <el-button type="info" @click="emitPrev" :disabled="innerOffset <= 0 || running" icon="ArrowLeft" style="margin-right: 4px;">上一页</el-button>
          </el-tooltip>
          <el-tooltip content="下一页" placement="top">
            <el-button type="success" @click="emitNext" :disabled="!next || running" icon="ArrowRight" style="margin-right: 4px;">下一页</el-button>
          </el-tooltip>
          <el-tooltip content="导出CSV" placement="top">
            <el-button type="warning" @click="emitExport" :disabled="!innerDsId || !innerSql || running" icon="Download" style="margin-right: 4px;">导出</el-button>
          </el-tooltip>
          <el-tooltip content="模板参数" placement="top">
            <el-button type="info" @click="showTpl = true" icon="Edit" style="margin-right: 4px;">参数</el-button>
          </el-tooltip>
          <el-tooltip content="放大编辑器" placement="top">
            <el-button @click="showMaximize = true" icon="FullScreen" title="放大编辑" style="margin-right: 4px;" />
          </el-tooltip>
          <el-tooltip content="重置偏移量" placement="top">
            <el-button @click="innerOffset = 0" icon="Refresh" :disabled="innerOffset === 0" />
          </el-tooltip>
        </el-form-item>
        <el-form-item label="偏移量">
          <el-input v-model="innerOffset" style="width: 100px" readonly />
        </el-form-item>
      </el-form>
    </el-card>

    <div v-if="Object.keys(currentParams).length > 0" class="param-preview">
      <span class="param-label">模板参数:</span>
      <el-tag v-for="(val, key) in currentParams" :key="key" type="info" effect="plain" size="small" class="param-tag">
        {{ key }} = {{ val }}
      </el-tag>
    </div>

    <div class="editor-wrapper">
      <VAceEditor
        :value="innerSql"
        @update:value="val => innerSql = val"
        lang="sql"
        theme="xcode"
        :options="aceOptions"
        :style="{ height: editorHeight + 'px', width: '100%' }"
      />
    </div>

    <el-dialog v-model="showTpl" title="模板参数" width="500px" class="param-dialog">
      <div>
        <el-button size="small" type="primary" @click="addParam" icon="Plus" style="margin-bottom: 8px;">新增参数</el-button>
        <div v-for="(p, idx) in tplParams" :key="idx" class="param-row">
          <el-input v-model="p.key" placeholder="变量名" style="width: 140px" />
          <el-input v-model="p.value" placeholder="变量值" style="width: 180px" />
          <el-button type="danger" size="small" @click="removeParam(idx)" icon="Delete" />
        </div>
      </div>
      <template #footer>
        <div style="text-align: right;">
          <el-button @click="showTpl = false">取消</el-button>
          <el-button type="primary" @click="saveParams">保存</el-button>
        </div>
      </template>
    </el-dialog>

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
  fontSize: 16,
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
  editorHeight: { type: Number, default: 320 },
})

const emit = defineEmits(['update:dataSourceId', 'update:sqlText', 'update:pageSize', 'update:offset', 'update:templateParams', 'run', 'export'])

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
    if (param.key) {
      obj[param.key] = param.value
    }
  })
  return obj
})

function toParamEntries(params) {
  return Object.entries(params || {}).map(([key, value]) => ({ key, value: String(value) }))
}

watch(innerDsId, value => emit('update:dataSourceId', value))
watch(innerSql, value => emit('update:sqlText', value))
watch(innerPageSize, value => emit('update:pageSize', value))
watch(innerOffset, value => emit('update:offset', value))

watch(() => props.dataSourceId, value => {
  innerDsId.value = value
})
watch(() => props.sqlText, value => {
  innerSql.value = value
})
watch(() => props.pageSize, value => {
  innerPageSize.value = value
})
watch(() => props.offset, value => {
  innerOffset.value = value
})
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
  if (!paging) {
    return
  }
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
    if (param.key) {
      obj[param.key] = param.value
    }
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
  gap: 8px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.query-form-card {
  margin-bottom: 0;
  border-radius: 8px;
  box-shadow: 0 1px 4px #f3f3f3;
  border: none;
}

.query-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;
}

.editor-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 2px 8px #f0f1f2;
}

.param-preview {
  margin: 2px 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.param-label {
  margin-right: 8px;
  color: #909399;
  font-size: 13px;
}

.param-tag {
  margin: 2px 4px 2px 0;
}

.param-dialog .param-row {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  align-items: center;
}

@media (max-width: 900px) {
  .query-form-card {
    padding: 0;
    border-radius: 4px;
  }

  .editor-wrapper {
    box-shadow: none;
    border-radius: 4px;
  }
}
</style>
