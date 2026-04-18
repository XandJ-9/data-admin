<template>
  <el-drawer v-model="drawerVisible" :title="detailTitle" size="720px" append-to-body class="detail-drawer">
    <template v-if="task">
      <div class="detail-summary">
        <div>
          <span class="detail-code">{{ task.taskCode }}</span>
          <h2>{{ task.taskName }}</h2>
          <p>{{ task.remark || '当前任务用于把源表同步到 ODS/贴源层，详情分模块查看。' }}</p>
        </div>
        <div class="detail-tag-group">
          <el-tag :type="statusTagType(task.status)">{{ statusLabel(task.status) }}</el-tag>
          <el-tag effect="plain">{{ executorLabel(task.executorType) }}</el-tag>
          <el-tag effect="plain">{{ scheduleTypeLabel(task.scheduleType) }}</el-tag>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="detail-tabs">
        <el-tab-pane label="配置" name="config">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="源数据源">{{ task.sourceDataSourceName || '-' }}</el-descriptions-item>
            <el-descriptions-item label="源表">{{ task.sourceTableName || '-' }}</el-descriptions-item>
            <el-descriptions-item label="目标数据源">{{ task.targetDataSourceName || '-' }}</el-descriptions-item>
            <el-descriptions-item label="目标表">{{ formatTargetTable(task) }}</el-descriptions-item>
            <el-descriptions-item label="加载方式">{{ loadTypeLabel(task.loadType) }}</el-descriptions-item>
            <el-descriptions-item label="写入模式">{{ writeModeLabel(task.writeMode) }}</el-descriptions-item>
            <el-descriptions-item label="负责人">{{ task.owner || '-' }}</el-descriptions-item>
            <el-descriptions-item label="任务状态">{{ statusLabel(task.status) }}</el-descriptions-item>
          </el-descriptions>

          <el-card shadow="never" class="info-block">
            <template #header><span>说明</span></template>
            <p class="info-text">{{ task.remark || '暂无备注说明。' }}</p>
          </el-card>

          <el-collapse class="advanced-collapse">
            <el-collapse-item title="高级配置 JSON" name="taskConfig">
              <pre class="json-preview">{{ formatJson(task.taskConfig) }}</pre>
            </el-collapse-item>
          </el-collapse>
        </el-tab-pane>

        <el-tab-pane label="调度" name="schedule">
          <div class="schedule-grid">
            <el-card shadow="never" class="info-block">
              <template #header><span>执行器</span></template>
              <strong>{{ executorLabel(task.executorType) }}</strong>
              <p class="info-text">{{ executorDescription(task.executorType) }}</p>
            </el-card>
            <el-card shadow="never" class="info-block">
              <template #header><span>调度方式</span></template>
              <strong>{{ scheduleTypeLabel(task.scheduleType) }}</strong>
              <p class="info-text">Cron：{{ task.cronExpression || '未配置' }}</p>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="运行" name="runtime">
          <div class="runtime-toolbar">
            <el-button text type="primary" :icon="Refresh" @click="$emit('refresh-preview')">刷新运行快照</el-button>
            <el-button text type="primary" :icon="Histogram" @click="$emit('open-executions', task)">查看执行记录</el-button>
          </div>
          <div v-if="previewLoading" class="preview-loading">
            <el-skeleton :rows="4" animated />
          </div>
          <div v-else-if="previewExecutions.length" class="execution-timeline">
            <article v-for="item in previewExecutions" :key="item.instanceId" class="execution-item">
              <div>
                <div class="execution-title">
                  <el-tag size="small" :type="executionStatusTagType(item.status)">{{ executionStatusLabel(item.status) }}</el-tag>
                  <strong>{{ item.instanceId }}</strong>
                </div>
                <p>
                  {{ item.triggerMode || '-' }}
                  <span v-if="item.triggeredBy">· {{ item.triggeredBy }}</span>
                  <span v-if="item.executorType">· {{ item.executorType }}</span>
                </p>
              </div>
              <div class="execution-side">
                <span>{{ item.durationSeconds ?? '-' }}s</span>
                <small>{{ item.finishedAt || item.createTime || '-' }}</small>
                <el-button text type="primary" @click="$emit('open-execution-detail', item)">查看详情</el-button>
              </div>
            </article>
          </div>
          <el-empty v-else description="暂无执行记录" :image-size="72" />
        </el-tab-pane>
      </el-tabs>
    </template>

    <template #footer>
      <div class="drawer-footer">
        <el-button @click="drawerVisible = false">关闭</el-button>
        <el-button v-if="task" :icon="Clock" @click="$emit('open-executions', task)">执行记录</el-button>
        <el-button
          v-if="task"
          type="primary"
          :icon="VideoPlay"
          :disabled="task.executorType !== 'mock'"
          @click="$emit('execute', task)"
          v-hasPermi="['dataintegration:task:execute']"
        >立即执行</el-button>
        <el-button v-if="task" type="primary" plain :icon="Edit" @click="$emit('edit', task)" v-hasPermi="['dataintegration:task:edit']">编辑任务</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { Clock, Edit, Histogram, Refresh, VideoPlay } from '@element-plus/icons-vue'
import {
  executionStatusLabel,
  executionStatusTagType,
  executorLabel,
  formatJson,
  formatTargetTable,
  loadTypeLabel,
  scheduleTypeLabel,
  statusLabel,
  statusTagType,
  writeModeLabel,
} from './taskViewMeta'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  detailTab: { type: String, default: 'config' },
  task: { type: Object, default: null },
  previewLoading: { type: Boolean, default: false },
  previewExecutions: { type: Array, default: () => [] },
  supportedExecutors: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue', 'update:detailTab', 'edit', 'execute', 'open-executions', 'refresh-preview', 'open-execution-detail'])

const drawerVisible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value),
})

const activeTab = computed({
  get: () => props.detailTab,
  set: value => emit('update:detailTab', value),
})

const detailTitle = computed(() => props.task ? `任务详情 - ${props.task.taskName}` : '任务详情')

function executorDescription(value) {
  return props.supportedExecutors.find(item => item.value === value)?.description || '暂无说明'
}
</script>

<style scoped>
.detail-summary,
.detail-tag-group,
.runtime-toolbar,
.drawer-footer,
.execution-title {
  display: flex;
  gap: 12px;
}

.detail-summary {
  justify-content: space-between;
  margin-bottom: 16px;
}

.detail-summary h2 {
  margin: 0;
}

.detail-code,
.info-text,
.execution-side small {
  color: var(--el-text-color-secondary);
}

.detail-summary p,
.info-text {
  margin: 8px 0 0;
  line-height: 1.7;
}

.detail-tag-group {
  flex-wrap: wrap;
  align-content: flex-start;
}

.info-block,
.advanced-collapse {
  margin-top: 16px;
}

.schedule-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.runtime-toolbar,
.drawer-footer {
  justify-content: flex-end;
}

.execution-timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.execution-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 14px;
}

.execution-item p {
  margin: 8px 0 0;
}

.execution-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.json-preview {
  margin: 8px 0 0;
  padding: 12px;
  overflow: auto;
  border-radius: 12px;
  background: var(--el-fill-color-light);
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 992px) {
  .detail-summary,
  .execution-item {
    flex-direction: column;
  }

  .schedule-grid {
    grid-template-columns: 1fr;
  }

  .execution-side {
    align-items: flex-start;
  }
}
</style>
