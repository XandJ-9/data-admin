<template>
  <div>
    <div style="margin-bottom: 8px">
      <el-checkbox v-model="innerDefaultMapping" @change="onDefaultMapping">默认字段映射</el-checkbox>
      <el-button size="small" style="margin-left: 12px" @click="addMappingRow">添加字段映射</el-button>
    </div>
    <el-table :data="props.mappings" border style="width: 100%">
      <el-table-column prop="targetField" label="目标字段">
        <template #header>
          <span>目标字段
            <span style="font-size: small;">映射字段{{ props.mappings.length }}个{{ props.targetColumns.length > 0 ? ', 目标表字段' + props.targetColumns.length +'个': '' }}</span>
          </span>
        </template>
        <template #default="scope">
          <el-select v-if="props.targetColumns.length > 0" v-model="scope.row.targetField" filterable allow-create default-first-option placeholder="选择目标字段" style="width: 220px">
            <el-option v-for="c in props.targetColumns.filter(c => !props.mappings.find(m => m.targetField === c))" :key="c" :label="c" :value="c" />
          </el-select>
          <!-- <el-input v-model="scope.row.targetField" placeholder="请输入" style="width: 220px" /> -->
        </template>
      </el-table-column>
      <el-table-column prop="sourceExpr" label="来源字段/表达式">
        <template #default="scope">
          <el-select v-if="props.sourceColumns.length > 0" v-model="scope.row.sourceExpr" filterable allow-create default-first-option placeholder="选择或输入" style="width: 260px">
            <el-option v-for="c in props.sourceColumns" :key="c" :label="c" :value="c" />
          </el-select>
          <!-- <el-input v-model="scope.row.sourceExpr" placeholder="请输入" style="width: 260px" /> -->
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="scope">
          <el-button link type="primary" @click="insertAfter(scope.$index)" :disabled="props.mappings.length >= props.targetColumns.length">在后追加</el-button>
          <el-button link type="danger" @click="removeMapping(scope.$index)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
  </template>

<script setup>
import { ElMessage } from 'element-plus'
const props = defineProps({
  sourceColumns: { type: Array, default: () => [] },
  targetColumns: { type: Array, default: () => [] },
  mappings: { type: Array, default: () => []},
})

// const emit = defineEmits(['update:sourceColumns', 'update:targetColumns', 'update:mappings'])

const innerDefaultMapping = ref(false)

watch(() => props.sourceColumns, () => {
  applyDefaultMapping()
})

watch(() => props.targetColumns, () => {
  applyDefaultMapping()
})

function onDefaultMapping() { applyDefaultMapping() }

function applyDefaultMapping() {
  if (!innerDefaultMapping.value) return
  const src = props.sourceColumns || []
  const tgt = props.targetColumns || []
  if (!tgt.length || !src.length) return
  const srcSet = new Set(src)
  const mapped = tgt.filter(n => srcSet.has(n)).map(n => ({ targetField: n, sourceExpr: n }))
    //   const limit = props.targetColumns.length
    //   props.mappings = mapped.slice(0, limit)
    mapped.forEach(item => {
        if (!props.mappings.length) props.mappings.push(item)
        else {
             props.mappings.find(m => m.targetField === item.targetField).sourceExpr = item.sourceExpr
        }

    })
  console.log('default mapping', mapped, props.mappings)
}

function addMappingRow() {
  if (!props.targetColumns.length) {
    ElMessage.warning('目标表字段数为空')
    return
  }
  if (props.mappings.length >= props.targetColumns.length) {
    ElMessage.warning('字段映射个数不能超过目标字段个数，最多' + props.targetColumns.length + '个')
    return
  }
  props.mappings.push({ targetField: '', sourceExpr: '' })
}

function insertAfter(index) {
  if (!props.targetColumns.length) {
    ElMessage.warning('未指定目标字段')
    return
  }
  if (props.mappings.length >= props.targetColumns.length) {
    ElMessage.warning('字段映射个数不能超过目标字段个数，最多' + props.targetColumns.length + '个')
    return
  }
  props.mappings.splice(index + 1, 0, { targetField: '', sourceExpr: '' })
}

function removeMapping(i) { props.mappings.splice(i, 1) }

</script>

<style scoped>
</style>
