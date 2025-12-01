<template>
  <div>
    <el-form :inline="true" label-width="80px">
      <el-form-item label="数据源">
        <el-select v-model="innerDsId" placeholder="选择数据源" style="width: 260px">
          <el-option v-for="ds in dsList" :key="ds.dataSourceId" :label="ds.dataSourceName + ' (' + ds.dbType + ')'" :value="ds.dataSourceId" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="emitRun" :disabled="!innerDsId || !innerSql || running">执行</el-button>
        <el-button type="info" @click="emitPrev" :disabled="(innerOffset <= 0) || running">上一页</el-button>
        <el-button type="success" @click="emitNext" :disabled="(!next || running)">下一页</el-button>
        <el-button type="warning" @click="showTpl = true">模板参数</el-button>
      </el-form-item>
      <el-form-item label="每页行数">
        <el-input-number v-model="innerPageSize" :min="1" :max="1000" />
      </el-form-item>
    </el-form>
    <!--
    <el-input v-model="innerSql" type="textarea" :rows="8" placeholder="输入 SQL (支持 {{ var }} / {% if %} / {% for %} )" />
    -->
    <CodeEditor v-model="innerSql" language="sql" placeholder="输入 SQL (支持 {{ var }} / {% if %} / {% for %} )" theme="monokai" />
    
    <el-dialog v-model="showTpl" title="模板参数" width="500px">
      <div>
        <el-button size="small" @click="addParam">新增参数</el-button>
        <div v-for="(p, idx) in tplParams" :key="idx" style="display:flex;gap:8px;margin-top:8px">
          <el-input v-model="p.key" placeholder="变量名" style="width: 180px" />
          <el-input v-model="p.value" placeholder="变量值" style="width: 260px" />
          <el-button type="danger" size="small" @click="removeParam(idx)">删除</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="showTpl=false">取消</el-button>
        <el-button type="primary" @click="saveParams">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import CodeEditor from '@/components/CodeEditor'

const props = defineProps({
  dsList: { type: Array, default: () => [] },
  dataSourceId: { type: Number, default: undefined },
  sqlText: { type: String, default: '' },
  running: { type: Boolean, default: false },
  pageSize: { type: Number, default: 50 },
  offset: { type: Number, default: 0 },
  next: { type: Object, default: null },
  templateParams: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['update:dataSourceId', 'update:sqlText', 'update:pageSize', 'update:offset', 'update:templateParams', 'run'])
const innerDsId = ref(props.dataSourceId)
const innerSql = ref(props.sqlText)
const innerPageSize = ref(props.pageSize)
const innerOffset = ref(props.offset)
const next = computed(() => props.next)
const showTpl = ref(false)
const tplParams = ref(Object.entries(props.templateParams || {}).map(([k,v]) => ({ key: k, value: String(v) })))
watch(innerDsId, v => emit('update:dataSourceId', v))
watch(innerSql, v => emit('update:sqlText', v))
watch(innerPageSize, v => emit('update:pageSize', v))
watch(innerOffset, v => emit('update:offset', v))
watch(() => props.dataSourceId, v => { innerDsId.value = v })
watch(() => props.sqlText, v => { innerSql.value = v })
watch(() => props.pageSize, v => { innerPageSize.value = v })
watch(() => props.offset, v => { innerOffset.value = v })
watch(() => props.templateParams, v => {
  tplParams.value = Object.entries(v || {}).map(([k, val]) => ({ key: k, value: String(val) }))
})
function emitRun() { emit('run', { pageSize: innerPageSize.value, offset: innerOffset.value, params: toParams() }) }
function emitPrev() {
  const newOffset = Number(innerOffset.value) - Number(innerPageSize.value)
  innerOffset.value = newOffset > 0 ? newOffset : 0
  emitRun()
}
function emitNext() {
  const n = next.value
  if (!n) return
  innerOffset.value = Number(n.offset || 0)
  emitRun()
}

function addParam() { tplParams.value.push({ key: '', value: '' }) }
function removeParam(i) { tplParams.value.splice(i, 1) }
function toParams() {
  const obj = {}
  tplParams.value.forEach(p => { if (p.key) obj[p.key] = p.value })
  emit('update:templateParams', obj)
  return obj
}
function saveParams() { toParams(); showTpl.value = false }
</script>
