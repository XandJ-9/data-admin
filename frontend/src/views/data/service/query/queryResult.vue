<template>
  <el-table :data="rows" stripe highlight-current-row border :height="resultHeight">
    <el-table-column v-for="col,idx in columns" :key="idx" :prop="idx+''" :label="col" :width="columnWidth(idx)" show-overflow-tooltip>
      <template #header>
        <el-tooltip :content="col" placement="top" :show-after="500">
          <span style="display:inline-block;width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
            {{ col }}
          </span>
        </el-tooltip>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
const { proxy } = getCurrentInstance()
const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  resultHeight: { type: [Number, String], default: 300 },
})
function columnWidth(colIdx) {
    if ((props.rows || []).length === 0) return 200
    let maxWidth = 200
    props.rows.forEach(item => {
        const val = item[colIdx]
        const width = proxy.calculateColumnWidth(val, { minWidth: 100, maxWidth: 500 })
        maxWidth = width
    })
    return maxWidth
}
</script>