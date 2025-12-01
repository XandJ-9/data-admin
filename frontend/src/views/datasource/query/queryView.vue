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
      </el-form-item>
      <el-form-item label="每页行数">
        <el-input-number v-model="innerPageSize" :min="1" :max="1000" />
      </el-form-item>
    </el-form>
    <el-input v-model="innerSql" type="textarea" :rows="8" placeholder="输入 SQL" />
  </div>
</template>

<script setup>
const props = defineProps({
  dsList: { type: Array, default: () => [] },
  dataSourceId: { type: Number, default: undefined },
  sqlText: { type: String, default: '' },
  running: { type: Boolean, default: false },
  pageSize: { type: Number, default: 50 },
  offset: { type: Number, default: 0 },
  next: { type: Object, default: null }
})
const emit = defineEmits(['update:dataSourceId', 'update:sqlText', 'update:pageSize', 'update:offset', 'run'])
const innerDsId = ref(props.dataSourceId)
const innerSql = ref(props.sqlText)
const innerPageSize = ref(props.pageSize)
const innerOffset = ref(props.offset)
const next = computed(() => props.next)
watch(innerDsId, v => emit('update:dataSourceId', v))
watch(innerSql, v => emit('update:sqlText', v))
watch(innerPageSize, v => emit('update:pageSize', v))
watch(innerOffset, v => emit('update:offset', v))
watch(() => props.dataSourceId, v => { innerDsId.value = v })
watch(() => props.sqlText, v => { innerSql.value = v })
watch(() => props.pageSize, v => { innerPageSize.value = v })
watch(() => props.offset, v => { innerOffset.value = v })
function emitRun() { emit('run', { pageSize: innerPageSize.value, offset: innerOffset.value }) }
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
</script>
