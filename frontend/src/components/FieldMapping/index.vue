<template>
  <div>
    <div style="margin-bottom: 8px">
      <el-button size="small" @click="applyDefaultMapping">默认字段映射</el-button>
      <el-button size="small" style="margin-left: 12px" @click="addMappingRow">添加字段映射</el-button>
    </div>
    <el-table :data="props.mappings" border style="width: 100%">
      <el-table-column prop="sourceExpr" label="来源字段/表达式">
        <template #default="scope">
          <el-select v-if="props.sourceColumns.length > 0" v-model="scope.row.sourceExpr" filterable allow-create default-first-option placeholder="选择或输入" style="width: 260px">
            <el-option v-for="c in props.sourceColumns" :key="c" :label="c" :value="c" />
          </el-select>
          <!-- <el-input v-model="scope.row.sourceExpr" placeholder="请输入" style="width: 260px" /> -->
        </template>
      </el-table-column>
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

// watch(() => props.mappings, (val) => {
//   console.log('mappings changed', val)
// })

// watch(() => props.targetColumns, (val) => {
//   // 当目标表字段变化时，清理无效的映射（目标字段不存在于新目标表字段中）
//   if (props.mappings.length > 0) {
//     const newTargetSet = new Set(val || [])
//     for (let i = props.mappings.length - 1; i >= 0; i--) {
//       const m = props.mappings[i]
//       if (m.targetField && !newTargetSet.has(m.targetField)) {
//         props.mappings.splice(i, 1)
//       }
//     }
//   }
// })

function applyDefaultMapping() {
  const src = props.sourceColumns || []
  const tgt = props.targetColumns || []
  if (!tgt.length || !src.length) return
  const srcSet = new Set(src)
  const mapped = tgt.filter(n => srcSet.has(n)).map(n => ({ targetField: n, sourceExpr: n }))
  
  // Clear existing mappings or merge? Current logic seems to want to update existing or add new
  // But props.mappings is reactive array. 
  
  // Strategy: 
  // 1. If mappings is empty, just push all mapped
  // 2. If not empty, update existing matches, and add new ones if they don't exist?
  // The original code had a bug where it tried to access .sourceExpr on undefined result of .find()
  
  if (props.mappings.length === 0) {
       props.mappings.push(...mapped)
  } else {
      mapped.forEach(item => {
          const existing = props.mappings.find(m => m.targetField === item.targetField)
          if (existing) {
              existing.sourceExpr = item.sourceExpr
          } else {
              // Should we add it if it's not there? 
              // The original logic was: if (!props.mappings.length) push else find...
              // If mappings has length but this specific item isn't there, the original code would crash or do nothing (if find returns undefined)
              // We'll choose to push it if not found, to ensure "Default Mapping" covers all matches
              props.mappings.push(item)
          }
      })
  }
  
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
