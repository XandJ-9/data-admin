<template>
  <div>
    <el-table :data="logs" border stripe v-loading="loading">
      <el-table-column prop="id" label="执行ID" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusColor(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="读取/写入" width="150">
        <template #default="{ row }">
          {{ formatNumber(row.rowsRead) }} / {{ formatNumber(row.rowsWritten) }}
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="耗时" width="100">
        <template #default="{ row }">{{ formatDuration(row.duration) }}</template>
      </el-table-column>
      <el-table-column prop="startTime" label="开始时间" width="160" />
      <el-table-column prop="endTime" label="结束时间" width="160" />
      <el-table-column prop="executedBy" label="执行者" width="100" />
      <el-table-column label="操作" width="100" align="center">
        <template #default="{ row }">
          <el-button link type="primary" icon="View" @click="$emit('view', row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="query.pageNum"
      v-model:limit="query.pageSize"
      @pagination="$emit('load')"
    />
  </div>
</template>

<script setup>
defineProps({
  logs: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  query: { type: Object, required: true },
  loading: { type: Boolean, default: false }
})

defineEmits(['view', 'load'])

function getStatusText(status) {
  const texts = {
    pending: '等待执行', running: '执行中', success: '成功',
    failed: '失败', cancelled: '已取消'
  }
  return texts[status] || status
}

function getStatusColor(status) {
  const colors = {
    pending: 'info', running: 'warning', success: 'success',
    failed: 'danger', cancelled: ''
  }
  return colors[status] || ''
}

function formatNumber(num) {
  if (!num) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

function formatDuration(seconds) {
  if (!seconds) return '0秒'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (hours > 0) return `${hours}小时${minutes}分${secs}秒`
  if (minutes > 0) return `${minutes}分${secs}秒`
  return `${secs}秒`
}
</script>
