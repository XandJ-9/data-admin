<template>
  <div class="status-bar">
    <div class="status-left">
      <span class="status-item">
        <el-icon :class="statusClass"><component :is="statusIcon" /></el-icon>
        {{ statusText }}
      </span>
      <el-divider direction="vertical" />
      <span v-if="scriptName" class="status-item script-name" :title="scriptName">
        {{ scriptName }}
      </span>
    </div>
    <div class="status-right">
      <span class="status-item" v-if="version > 0">v{{ version }}</span>
      <el-divider direction="vertical" v-if="version > 0" />
      <span class="status-item">{{ lang.toUpperCase() }}</span>
      <el-divider direction="vertical" />
      <span class="status-item" v-if="cursorInfo">行 {{ cursorInfo.row }}, 列 {{ cursorInfo.col }}</span>
      <el-divider direction="vertical" v-if="datasourceName" />
      <span class="status-item ds" v-if="datasourceName">
        <el-icon><Coin /></el-icon>
        {{ datasourceName }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { Coin, Loading, CircleCheck, CircleClose, Clock } from '@element-plus/icons-vue'

defineOptions({ name: 'DevStatusBar' })

const props = defineProps({
  status: { type: String, default: 'idle' }, // idle | running | pending | success | failed | cancelled
  scriptName: { type: String, default: '' },
  version: { type: Number, default: 0 },
  lang: { type: String, default: 'sql' },
  cursorInfo: { type: Object, default: null }, // { row, col }
  datasourceName: { type: String, default: '' },
})

const statusIcon = computed(() => {
  const map = {
    idle: 'Clock',
    running: 'Loading',
    pending: 'Clock',
    success: 'CircleCheck',
    failed: 'CircleClose',
    cancelled: 'CircleClose',
  }
  return map[props.status] || 'Clock'
})
const statusText = computed(() => {
  const map = {
    idle: '就绪',
    running: '执行中...',
    pending: '已提交',
    success: '执行成功',
    failed: '执行失败',
    cancelled: '已取消',
  }
  return map[props.status] || '就绪'
})
const statusClass = computed(() => `status-icon-${props.status}`)
</script>

<style lang="scss" scoped>
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 26px;
  padding: 0 12px;
  background: #f5f7fa;
  border-top: 1px solid #e4e7ed;
  font-size: 12px;
  color: #606266;
  flex-shrink: 0;
}

.status-left, .status-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 3px;
  white-space: nowrap;
}

.script-name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ds {
  color: #409eff;
}

.status-icon-idle    { color: #909399; }
.status-icon-running { color: #e6a23c; animation: spin 1s linear infinite; }
.status-icon-pending { color: #409eff; }
.status-icon-success { color: #67c23a; }
.status-icon-failed  { color: #f56c6c; }
.status-icon-cancelled { color: #909399; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
</style>
