<template>
  <div>
    <div style="margin-bottom: 8px">
      <el-checkbox v-model="defaultMapping" @change="onDefaultMapping">默认字段映射</el-checkbox>
      <!-- <el-button size="small" style="margin-left: 12px" @click="addMappingRow" :disabled="innerMappings.length >= props.targetColumns.length">新增映射</el-button> -->
    </div>
    <el-table :data="innerMappings" border style="width: 100%">
      <el-table-column prop="targetField" label="目标字段">
        <template #header>
          <span>目标字段{{ innerMappings.length }}/{{ props.targetColumns.length }}</span>
        </template>
        <template #default="scope">
          <el-select v-model="scope.row.targetField" filterable allow-create default-first-option placeholder="选择目标字段" style="width: 220px">
            <el-option v-for="c in targetOptions(scope.row)" :key="c" :label="c" :value="c" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="sourceExpr" label="来源字段/表达式">
        <template #default="scope">
          <el-select v-model="scope.row.sourceExpr" filterable allow-create default-first-option placeholder="选择或输入" style="width: 260px">
            <el-option v-for="c in sourceColumns" :key="c" :label="c" :value="c" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="scope">
          <el-button link type="primary" @click="insertAfter(scope.$index)" :disabled="innerMappings.length >= props.targetColumns.length">在后追加</el-button>
          <el-button link type="danger" @click="removeMapping(scope.$index)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
  </template>

<script setup>
import { ElMessage } from 'element-plus'
const emit = defineEmits(['update:mappings'])
const props = defineProps({
  sourceColumns: { type: Array, default: () => [] },
  targetColumns: { type: Array, default: () => [] },
  mappings: { type: Array, default: () => [] }
})

const innerMappings = ref(props.mappings.slice())
const defaultMapping = ref(false)

watch(innerMappings, v => {
    emit('update:mappings', v)
}, { deep: true })

watch(() => props.sourceColumns, () => {
  applyDefaultMapping()
})

watch(() => props.targetColumns, () => {
  applyDefaultMapping()
})

function addMappingRow() {
  if (!props.targetColumns.length) {
    ElMessage.warning('未指定目标字段')
    return
  }
  if (innerMappings.value.length >= props.targetColumns.length) {
    ElMessage.warning('字段映射个数不能超过目标字段个数，最多' + props.targetColumns.length + '个')
    return
  }
  innerMappings.value.push({ targetField: '', sourceExpr: '' })
}

function insertAfter(index) {
  if (!props.targetColumns.length) {
    ElMessage.warning('未指定目标字段')
    return
  }
  if (innerMappings.value.length >= props.targetColumns.length) {
    ElMessage.warning('字段映射个数不能超过目标字段个数，最多' + props.targetColumns.length + '个')
    return
  }
  innerMappings.value.splice(index + 1, 0, { targetField: '', sourceExpr: '' })
}

function removeMapping(i) { innerMappings.value.splice(i, 1) }

function onDefaultMapping() { applyDefaultMapping() }

function applyDefaultMapping() {
  if (!defaultMapping.value) return
  const src = props.sourceColumns || []
  const tgt = props.targetColumns || []
  if (!tgt.length || !src.length) return
  const srcSet = new Set(src)
  const mapped = tgt.filter(n => srcSet.has(n)).map(n => ({ targetField: n, sourceExpr: n }))
  const limit = props.targetColumns.length
  innerMappings.value = mapped.slice(0, limit)
}

function targetOptions(row) {
  const used = new Set((innerMappings.value || []).map(m => m.targetField).filter(Boolean))
  return (props.targetColumns || []).filter(c => c === row.targetField || !used.has(c))
}

</script>

<style scoped>
</style>
