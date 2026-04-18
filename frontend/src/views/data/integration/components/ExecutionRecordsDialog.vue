<template>
  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="960px" append-to-body>
    <div class="runtime-toolbar">
      <el-button type="primary" plain :icon="Refresh" @click="$emit('refresh')">刷新</el-button>
    </div>
    <el-table v-loading="executionLoading" :data="executionList" border>
      <el-table-column label="实例ID" prop="instanceId" min-width="220" show-overflow-tooltip />
      <el-table-column label="状态" prop="status" width="100">
        <template #default="scope">
          <el-tag :type="executionStatusTagType(scope.row.status)" size="small">{{ executionStatusLabel(scope.row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="触发方式" prop="triggerMode" width="100" />
      <el-table-column label="触发人" prop="triggeredBy" width="120" show-overflow-tooltip />
      <el-table-column label="执行器" prop="executorType" width="120" show-overflow-tooltip />
      <el-table-column label="开始时间" prop="startedAt" width="180" />
      <el-table-column label="结束时间" prop="finishedAt" width="180" />
      <el-table-column label="耗时(s)" prop="durationSeconds" width="90" />
      <el-table-column label="操作" width="120" align="center">
        <template #default="scope">
          <el-button link type="primary" :icon="View" @click="$emit('open-detail', scope.row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="executionTotal > 0"
      :total="executionTotal"
      v-model:page="executionQuery.pageNum"
      v-model:limit="executionQuery.pageSize"
      @pagination="$emit('pagination')"
    />
  </el-dialog>

  <el-drawer v-model="detailDrawerVisible" :title="detailTitle" size="45%" append-to-body>
    <template v-if="selectedExecution">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="实例ID">{{ selectedExecution.instanceId }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ executionStatusLabel(selectedExecution.status) }}</el-descriptions-item>
        <el-descriptions-item label="触发方式">{{ selectedExecution.triggerMode || '-' }}</el-descriptions-item>
        <el-descriptions-item label="触发人">{{ selectedExecution.triggeredBy || '-' }}</el-descriptions-item>
        <el-descriptions-item label="执行器">{{ selectedExecution.executorType || '-' }}</el-descriptions-item>
        <el-descriptions-item label="错误信息">{{ selectedExecution.errorMessage || '-' }}</el-descriptions-item>
      </el-descriptions>
      <div class="json-section">
        <h4>运行时配置</h4>
        <pre class="json-preview">{{ formatJson(selectedExecution.runtimeConfig) }}</pre>
      </div>
      <div class="json-section">
        <h4>结果摘要</h4>
        <pre class="json-preview">{{ formatJson(selectedExecution.resultSummary) }}</pre>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { Refresh, View } from '@element-plus/icons-vue'
import { executionStatusLabel, executionStatusTagType, formatJson } from './taskViewMeta'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  detailVisible: { type: Boolean, default: false },
  task: { type: Object, default: null },
  executionLoading: { type: Boolean, default: false },
  executionList: { type: Array, default: () => [] },
  executionTotal: { type: Number, default: 0 },
  executionQuery: { type: Object, required: true },
  selectedExecution: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue', 'update:detailVisible', 'refresh', 'pagination', 'open-detail'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value),
})

const detailDrawerVisible = computed({
  get: () => props.detailVisible,
  set: value => emit('update:detailVisible', value),
})

const dialogTitle = computed(() => props.task ? `执行记录 - ${props.task.taskName}` : '执行记录')

const detailTitle = computed(() => props.selectedExecution ? `实例详情 - ${props.selectedExecution.instanceId}` : '实例详情')
</script>

<style scoped>
.runtime-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.json-section {
  margin-top: 16px;
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
</style>
