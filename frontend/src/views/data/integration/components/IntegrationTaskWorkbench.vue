<template>
  <div class="workbench-layout">
    <el-card shadow="hover" class="workbench-card intro-card">
      <div class="intro-row">
        <div>
          <span class="section-eyebrow">任务工作面</span>
          <h2>把筛选、执行和详情查看集中在一个清晰的任务列表里</h2>
          <p>列表视图只服务高频操作，不再与首页定位说明混排。</p>
        </div>
        <div class="intro-actions">
          <el-button type="primary" :icon="Plus" @click="$emit('add')" v-hasPermi="['dataintegration:task:add']">新建同步任务</el-button>
          <el-button plain type="primary" :icon="Refresh" @click="$emit('refresh')">刷新列表</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="workbench-card filter-card">
      <div class="toolbar-row">
        <div class="toolbar-main">
          <el-input
            v-model="queryParams.taskName"
            placeholder="搜索任务名称"
            clearable
            class="toolbar-input"
            @keyup.enter="$emit('query')"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-radio-group v-model="queryParams.status" size="small" @change="$emit('query')">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button v-for="item in statusOptions" :key="item.value" :label="item.value">{{ item.label }}</el-radio-button>
          </el-radio-group>
          <el-select
            v-model="queryParams.executorType"
            clearable
            placeholder="全部执行器"
            class="toolbar-select"
            @change="$emit('query')"
          >
            <el-option v-for="item in executorOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="toolbar-actions">
          <el-button type="primary" :icon="Search" @click="$emit('query')">筛选</el-button>
          <el-button :icon="Refresh" @click="$emit('reset')">重置</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="workbench-card list-card">
      <template #header>
        <div class="section-head">
          <div>
            <h3>同步任务列表</h3>
            <p>回答“有哪些任务、哪个值得立刻处理、我该点谁进去看”。</p>
          </div>
          <span class="section-meta">共 {{ total }} 条</span>
        </div>
      </template>

      <el-table :data="taskList" row-key="taskId" @row-click="$emit('open-task-detail', $event)" class="task-table" empty-text="暂无匹配任务">
        <el-table-column label="任务" min-width="240">
          <template #default="{ row }">
            <div class="task-cell">
              <strong>{{ row.taskName }}</strong>
              <span>{{ row.taskCode }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="同步路径" min-width="280">
          <template #default="{ row }">
            <div class="route-cell">
              <span>{{ row.sourceDataSourceName || '未配置源' }}</span>
              <el-icon><Right /></el-icon>
              <span>{{ formatTargetTable(row) }}</span>
            </div>
            <small>{{ row.sourceTableName || '未配置源表' }}</small>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="同步策略" min-width="190">
          <template #default="{ row }">
            <div class="tag-stack">
              <el-tag size="small" effect="plain">{{ loadTypeLabel(row.loadType) }}</el-tag>
              <el-tag size="small" effect="plain">{{ writeModeLabel(row.writeMode) }}</el-tag>
              <el-tag size="small" effect="plain">{{ scheduleTypeLabel(row.scheduleType) }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="执行器" min-width="150">
          <template #default="{ row }">
            <div class="execution-cell">
              <el-tag size="small" :type="row.executorType === 'mock' ? 'success' : 'warning'">{{ executorLabel(row.executorType) }}</el-tag>
              <small>{{ row.executorType === 'mock' ? '当前用于联调闭环' : '当前走真实执行链路' }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="负责人" min-width="120">
          <template #default="{ row }">
            <div class="owner-cell">
              <span>{{ row.owner || '-' }}</span>
              <small>{{ row.updateTime || '-' }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" :icon="View" @click.stop="$emit('open-task-detail', row)">详情</el-button>
            <el-button
              link
              type="primary"
              :icon="VideoPlay"
              @click.stop="$emit('execute', row)"
              v-hasPermi="['dataintegration:task:execute']"
            >执行</el-button>
            <el-button link type="primary" :icon="Edit" @click.stop="$emit('edit', row)" v-hasPermi="['dataintegration:task:edit']">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click.stop="$emit('delete', row)" v-hasPermi="['dataintegration:task:remove']">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <pagination
        v-show="total > 0"
        :total="total"
        v-model:page="queryParams.pageNum"
        v-model:limit="queryParams.pageSize"
        @pagination="$emit('refresh')"
      />
    </el-card>

    <TaskDetailDrawer
      :model-value="detailOpen"
      :detail-tab="detailTab"
      :task="selectedTask"
      :preview-loading="previewLoading"
      :preview-executions="previewExecutions"
      :supported-executors="supportedExecutors"
      @update:model-value="$emit('update:detail-open', $event)"
      @update:detail-tab="$emit('update:detail-tab', $event)"
      @edit="$emit('edit', $event)"
      @execute="$emit('execute', $event)"
      @open-executions="$emit('open-execution-dialog')"
      @refresh-preview="$emit('refresh-preview')"
      @open-execution-detail="$emit('open-execution-detail', $event)"
    />

    <ExecutionRecordsDialog
      :model-value="executionDialogVisible"
      :detail-visible="executionDetailVisible"
      :task="selectedTask"
      :execution-loading="executionLoading"
      :execution-list="executionDialogList"
      :execution-total="executionTotal"
      :execution-query="executionQueryParams"
      :selected-execution="selectedExecution"
      @update:model-value="$emit('update:execution-dialog-visible', $event)"
      @update:detail-visible="$emit('update:execution-detail-visible', $event)"
      @refresh="$emit('load-executions')"
      @pagination="$emit('load-executions')"
      @open-detail="$emit('open-execution-detail', $event)"
    />
  </div>
</template>

<script setup>
import { Delete, Edit, Plus, Refresh, Right, Search, VideoPlay, View } from '@element-plus/icons-vue'
import ExecutionRecordsDialog from './ExecutionRecordsDialog.vue'
import TaskDetailDrawer from './TaskDetailDrawer.vue'
import { executorLabel, formatTargetTable, loadTypeLabel, scheduleTypeLabel, statusLabel, statusTagType, writeModeLabel } from './taskViewMeta'

defineProps({
  detailOpen: {
    type: Boolean,
    default: false,
  },
  detailTab: {
    type: String,
    default: 'config',
  },
  executionDetailVisible: {
    type: Boolean,
    default: false,
  },
  executionDialogList: {
    type: Array,
    default: () => [],
  },
  executionDialogVisible: {
    type: Boolean,
    default: false,
  },
  executionLoading: {
    type: Boolean,
    default: false,
  },
  executionQueryParams: {
    type: Object,
    required: true,
  },
  executionTotal: {
    type: Number,
    default: 0,
  },
  executorOptions: {
    type: Array,
    default: () => [],
  },
  previewExecutions: {
    type: Array,
    default: () => [],
  },
  previewLoading: {
    type: Boolean,
    default: false,
  },
  queryParams: {
    type: Object,
    required: true,
  },
  selectedExecution: {
    type: Object,
    default: null,
  },
  selectedTask: {
    type: Object,
    default: null,
  },
  statusOptions: {
    type: Array,
    default: () => [],
  },
  supportedExecutors: {
    type: Array,
    default: () => [],
  },
  taskList: {
    type: Array,
    default: () => [],
  },
  total: {
    type: Number,
    default: 0,
  },
})

defineEmits([
  'add',
  'delete',
  'edit',
  'execute',
  'load-executions',
  'open-execution-detail',
  'open-execution-dialog',
  'open-task-detail',
  'query',
  'refresh',
  'refresh-preview',
  'reset',
  'update:detail-open',
  'update:detail-tab',
  'update:execution-detail-visible',
  'update:execution-dialog-visible',
])
</script>

<style scoped>
.workbench-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.workbench-card {
  border-radius: 18px;
}

.intro-card {
  background: linear-gradient(135deg, rgba(236, 244, 242, 0.95), rgba(245, 244, 236, 0.95));
}

.intro-row,
.toolbar-row,
.section-head,
.intro-actions,
.toolbar-actions {
  display: flex;
  gap: 12px;
}

.intro-row,
.section-head {
  justify-content: space-between;
  align-items: flex-start;
}

.section-eyebrow,
.section-meta,
.task-cell span,
.owner-cell small,
.intro-row p,
.section-head p {
  color: var(--el-text-color-secondary);
}

.intro-row h2,
.section-head h3 {
  margin: 10px 0 8px;
}

.intro-row p,
.section-head p {
  margin: 0;
  line-height: 1.7;
}

.intro-actions,
.toolbar-actions {
  flex-wrap: wrap;
}

.toolbar-row {
  justify-content: space-between;
  align-items: center;
}

.toolbar-main {
  display: flex;
  flex: 1;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.toolbar-input {
  width: 240px;
}

.toolbar-select {
  width: 180px;
}

.task-table :deep(.el-table__row) {
  cursor: pointer;
}

.task-cell,
.owner-cell,
.execution-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.route-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.tag-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

@media (max-width: 992px) {
  .intro-row,
  .toolbar-row {
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .toolbar-input,
  .toolbar-select {
    width: 100%;
  }
}
</style>