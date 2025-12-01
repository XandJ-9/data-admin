<template>
  <el-table :data="rows" style="margin-top: 16px">
    <el-table-column v-for="col in columns" :key="col" :prop="col" :label="col" :width="columnWidth(col)" />
  </el-table>
</template>

<script setup>
import { calculateColumnWidth } from '@/utils'
const { proxy } = getCurrentInstance()
const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] }
})
function columnWidth(columnName) {
  if ((props.rows || []).length === 0) return 200
  let maxWidth = 200
  props.rows.forEach(item => {
    const val = item[columnName]
    const width = (proxy?.calculateColumnWidth || calculateColumnWidth)(val, { minWidth: 150, maxWidth: 300 })
    maxWidth = Math.max(maxWidth, width)
  })
  return maxWidth
}
</script>
