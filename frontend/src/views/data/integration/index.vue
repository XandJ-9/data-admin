<template>
  <div class="app-container integration-page" v-loading="loading">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-layout">
        <div>
          <span class="hero-eyebrow">数据集成</span>
          <h1>轻列表看任务，重详情页做配置</h1>
          <p>首页只保留筛选、任务清单和关键状态。配置编辑改到独立详情页，运行记录仍在详情抽屉里快速查看。</p>
        </div>
        <div class="hero-actions">
          <el-button type="primary" :icon="Plus" @click="handleAdd" v-hasPermi="['dataintegration:task:add']">新建同步任务</el-button>
          <el-button :icon="Refresh" @click="getList">刷新列表</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="summary-row">
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="summary-card">
          <div class="summary-icon tone-blue"><el-icon><Tickets /></el-icon></div>
          <div>
            <div class="summary-label">当前筛选任务</div>
            <div class="summary-value">{{ total }}</div>
            <div class="summary-hint">当前过滤条件下可见的同步任务数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="summary-card">
          <div class="summary-icon tone-green"><el-icon><CircleCheck /></el-icon></div>
          <div>
            <div class="summary-label">启用中的任务</div>
            <div class="summary-value">{{ activeTaskCount }}</div>
            <div class="summary-hint">当前页处于启用状态，可直接纳入调度的任务</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="summary-card">
          <div class="summary-icon tone-orange"><el-icon><Clock /></el-icon></div>
          <div>
            <div class="summary-label">Cron 任务</div>
            <div class="summary-value">{{ cronTaskCount }}</div>
            <div class="summary-hint">当前页按 Cron 调度的任务数量</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" class="filter-card">
      <div class="toolbar-row">
        <div class="toolbar-main">
          <el-input
            v-model="queryParams.taskName"
            placeholder="搜索任务名称"
            clearable
            class="toolbar-input"
            @keyup.enter="handleQuery"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-radio-group v-model="queryParams.status" size="small" @change="handleQuery">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button v-for="item in STATUS_OPTIONS" :key="item.value" :label="item.value">{{ item.label }}</el-radio-button>
          </el-radio-group>
          <el-select
            v-model="queryParams.executorType"
            clearable
            placeholder="全部执行器"
            class="toolbar-select"
            @change="handleQuery"
          >
            <el-option v-for="item in executorOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="toolbar-actions">
          <el-button type="primary" :icon="Search" @click="handleQuery">筛选</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="list-card">
      <template #header>
        <div class="section-head">
          <div>
            <h3>同步任务列表</h3>
            <p>列表页只回答“有哪些任务、哪个有问题、我该点谁进去看”。</p>
          </div>
          <span class="section-meta">共 {{ total }} 条</span>
        </div>
      </template>

      <el-table :data="taskList" row-key="taskId" @row-click="openTaskDetail" class="task-table" empty-text="暂无匹配任务">
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
              <small>{{ row.executorType === 'mock' ? '当前可直接联调' : '待接入真实执行链' }}</small>
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
            <el-button link type="primary" :icon="View" @click.stop="openTaskDetail(row)">详情</el-button>
            <el-button
              link
              type="primary"
              :icon="VideoPlay"
              :disabled="row.executorType !== 'mock'"
              @click.stop="handleExecute(row)"
              v-hasPermi="['dataintegration:task:execute']"
            >执行</el-button>
            <el-button link type="primary" :icon="Edit" @click.stop="handleUpdate(row)" v-hasPermi="['dataintegration:task:edit']">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click.stop="handleDelete(row)" v-hasPermi="['dataintegration:task:remove']">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <pagination
        v-show="total > 0"
        :total="total"
        v-model:page="queryParams.pageNum"
        v-model:limit="queryParams.pageSize"
        @pagination="getList"
      />
    </el-card>

    <TaskDetailDrawer
      v-model="detailOpen"
      v-model:detailTab="detailTab"
      :task="selectedTask"
      :preview-loading="previewLoading"
      :preview-executions="previewExecutions"
      :supported-executors="supportedExecutors"
      @edit="handleUpdate"
      @execute="handleExecute"
      @open-executions="openExecutionDialog"
      @refresh-preview="loadExecutionPreview"
      @open-execution-detail="openExecutionDetail"
    />

    <ExecutionRecordsDialog
      v-model="executionDialogVisible"
      v-model:detailVisible="executionDetailVisible"
      :task="selectedTask"
      :execution-loading="executionLoading"
      :execution-list="executionDialogList"
      :execution-total="executionTotal"
      :execution-query="executionQueryParams"
      :selected-execution="selectedExecution"
      @refresh="loadExecutions"
      @pagination="loadExecutions"
      @open-detail="openExecutionDetail"
    />
  </div>
</template>

<script setup name="DataIntegration">
import { CircleCheck, Clock, Delete, Edit, Plus, Refresh, Right, Search, Tickets, VideoPlay, View } from '@element-plus/icons-vue'
import TaskDetailDrawer from './components/TaskDetailDrawer.vue'
import ExecutionRecordsDialog from './components/ExecutionRecordsDialog.vue'
import { executorLabel, formatTargetTable, loadTypeLabel, scheduleTypeLabel, statusLabel, statusTagType, writeModeLabel } from './components/taskViewMeta'
import { useIntegrationPage } from './components/useIntegrationPage'

const {
  STATUS_OPTIONS,
  activeTaskCount,
  cronTaskCount,
  detailOpen,
  detailTab,
  executionDetailVisible,
  executionDialogList,
  executionDialogVisible,
  executionLoading,
  executionQueryParams,
  executionTotal,
  executorOptions,
  loading,
  previewExecutions,
  previewLoading,
  queryParams,
  selectedExecution,
  selectedTask,
  supportedExecutors,
  taskList,
  total,
  getList,
  handleAdd,
  handleDelete,
  handleExecute,
  handleQuery,
  handleUpdate,
  loadExecutionPreview,
  loadExecutions,
  openExecutionDetail,
  openExecutionDialog,
  openTaskDetail,
  resetQuery,
} = useIntegrationPage()
</script>

<style scoped>
.hero-card,
.summary-card,
.filter-card,
.list-card {
  border-radius: 16px;
}

.hero-card {
  margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.08), rgba(103, 194, 58, 0.05));
}

.hero-layout,
.toolbar-row,
.section-head,
.hero-actions,
.toolbar-actions {
  display: flex;
  gap: 12px;
}

.hero-layout,
.toolbar-row,
.section-head {
  justify-content: space-between;
  align-items: flex-start;
}

.hero-layout h1,
.section-head h3 {
  margin: 0;
}

.hero-eyebrow,
.summary-label,
.summary-hint,
.section-meta,
.task-cell span,
.owner-cell small {
  color: var(--el-text-color-secondary);
}

.hero-layout p,
.section-head p {
  margin: 8px 0 0;
  line-height: 1.7;
}

.hero-actions,
.toolbar-actions {
  flex-wrap: wrap;
}

.summary-row {
  margin-bottom: 16px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 14px;
}

.summary-icon {
  display: inline-flex;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.tone-blue {
  color: #2f7df6;
  background: rgba(47, 125, 246, 0.12);
}

.tone-green {
  color: #28a745;
  background: rgba(40, 167, 69, 0.12);
}

.tone-orange {
  color: #ff8f1f;
  background: rgba(255, 143, 31, 0.14);
}

.summary-value {
  margin: 4px 0;
  font-size: 28px;
  line-height: 1;
}

.toolbar-row {
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
  .hero-layout,
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
