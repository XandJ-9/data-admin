<template>
  <div class="result-panel">
    <el-tabs v-model="activeTab" class="panel-tabs">
      <!-- 数据预览 -->
      <el-tab-pane label="数据预览" name="preview">
        <div class="tab-body">
          <template v-if="columns.length > 0">
            <el-table :data="rows" border size="small" class="result-table" max-height="100%" stripe>
              <el-table-column
                v-for="col in columns"
                :key="col"
                :prop="col"
                :label="col"
                min-width="120"
                show-overflow-tooltip
              />
            </el-table>
            <div class="result-meta">
              <span>共 {{ rows.length }} 行 · {{ columns.length }} 列</span>
              <span v-if="duration !== null">耗时 {{ duration }}s</span>
            </div>
          </template>
          <el-empty v-else description="执行脚本后在此预览数据" :image-size="64" />
        </div>
      </el-tab-pane>

      <!-- 血缘图谱 -->
      <el-tab-pane label="血缘图谱" name="lineage">
        <div class="tab-body">
          <div v-if="lineageData" class="lineage-container" ref="lineageRef">
            <!-- 简易表级血缘展示 -->
            <div class="lineage-graph">
              <div v-for="(node, idx) in lineageData.nodes" :key="idx" class="lineage-node" :class="node.type">
                <el-icon><Coin /></el-icon>
                <span>{{ node.name }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="解析脚本后展示血缘关系" :image-size="64" />
        </div>
      </el-tab-pane>

      <!-- 执行计划 -->
      <el-tab-pane label="执行计划" name="plan">
        <div class="tab-body">
          <template v-if="executionPlan">
            <el-table :data="executionPlan" border size="small" class="result-table" max-height="100%">
              <el-table-column prop="id" label="ID" width="60" />
              <el-table-column prop="operation" label="操作" min-width="180" show-overflow-tooltip />
              <el-table-column prop="table" label="表" min-width="120" />
              <el-table-column prop="rows" label="预估行数" width="100" />
              <el-table-column prop="cost" label="代价" width="100" />
              <el-table-column prop="extra" label="额外信息" min-width="160" show-overflow-tooltip />
            </el-table>
          </template>
          <el-empty v-else description="执行 EXPLAIN 后展示执行计划" :image-size="64" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 执行日志 -->
    <div v-if="logs.length > 0" class="log-section">
      <div class="log-header" @click="logExpand = !logExpand">
        <el-icon><Document /></el-icon>
        <span>执行日志</span>
        <el-icon class="log-toggle"><component :is="logExpand ? 'ArrowDown' : 'ArrowRight'" /></el-icon>
      </div>
      <el-scrollbar v-show="logExpand" class="log-body">
        <div v-for="(line, idx) in logs" :key="idx" class="log-line" :class="line.level">
          <span class="log-time">{{ line.time }}</span>
          <span class="log-msg">{{ line.message }}</span>
        </div>
      </el-scrollbar>
    </div>
  </div>
</template>

<script setup>
import { Coin, Document, ArrowDown, ArrowRight } from '@element-plus/icons-vue'

defineOptions({ name: 'DevResultPanel' })

defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  duration: { type: Number, default: null },
  lineageData: { type: Object, default: null },
  executionPlan: { type: Array, default: null },
  logs: { type: Array, default: () => [] },
})

const activeTab = ref('preview')
const logExpand = ref(true)
</script>

<style lang="scss" scoped>
.result-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}

.panel-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;

  :deep(.el-tabs__header) {
    margin-bottom: 0;
    padding: 0 12px;
  }
  :deep(.el-tabs__content) {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
  :deep(.el-tab-pane) {
    height: 100%;
  }
}

.tab-body {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px;
  overflow: auto;
}

.result-table {
  flex: 1;
  min-height: 0;
}

.result-meta {
  display: flex;
  gap: 16px;
  padding: 6px 0 0;
  font-size: 12px;
  color: #909399;
}

/* 血缘图谱简易布局 */
.lineage-container {
  padding: 16px;
}
.lineage-graph {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.lineage-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 13px;
  border: 1px solid #dcdfe6;
  background: #f5f7fa;
  &.source { border-color: #409eff; background: #ecf5ff; }
  &.target { border-color: #67c23a; background: #f0f9eb; }
}

/* 执行日志 */
.log-section {
  border-top: 1px solid #e4e7ed;
  max-height: 150px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.log-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  cursor: pointer;
  user-select: none;
  &:hover { background: #f5f7fa; }
}
.log-toggle {
  margin-left: auto;
}
.log-body {
  flex: 1;
  min-height: 0;
  padding: 0 12px 6px;
}
.log-line {
  font-family: 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.6;
  &.error { color: #f56c6c; }
  &.warn  { color: #e6a23c; }
}
.log-time {
  color: #909399;
  margin-right: 8px;
}
</style>
