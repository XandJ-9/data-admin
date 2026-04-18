<template>
  <div class="app-container integration-page" v-loading="loading">
    <el-card shadow="hover" class="hero-panel">
      <div class="hero-copy">
        <span class="hero-eyebrow">数据集成</span>
        <h1>把同步任务配置、执行入口和状态判断放在同一页</h1>
        <p>
          数据集成首页仍以任务清单为主，但视觉层统一收敛到概览页风格：先看模块定位和关键状态，再进入列表做筛选、执行和详情维护。
        </p>
        <div class="hero-actions">
          <el-button type="primary" :icon="Plus" @click="handleAdd" v-hasPermi="['dataintegration:task:add']">新建同步任务</el-button>
          <el-button plain type="primary" :icon="Refresh" @click="getList">刷新列表</el-button>
        </div>
        <div class="hero-tags">
          <el-tag size="small" type="primary" effect="light" round>任务配置管理</el-tag>
          <el-tag size="small" effect="plain" round>执行状态跟踪</el-tag>
          <el-tag size="small" effect="plain" round>详情页深度编辑</el-tag>
        </div>
      </div>
      <div class="hero-highlight">
        <div class="highlight-card">
          <span class="highlight-label">使用方式</span>
          <ul>
            <li>先看当前任务规模和启用情况</li>
            <li>再在列表里筛选并进入详情页维护配置</li>
            <li>执行记录留在详情抽屉和详情页中查看，不把首页做成大工作台</li>
          </ul>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="metric-row">
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon tone-blue"><el-icon><Tickets /></el-icon></div>
          <div class="metric-body">
            <span class="metric-label">当前筛选任务</span>
            <strong class="metric-value">{{ total }}</strong>
            <span class="metric-hint">当前过滤条件下可见的同步任务数</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon tone-green"><el-icon><CircleCheck /></el-icon></div>
          <div class="metric-body">
            <span class="metric-label">启用中的任务</span>
            <strong class="metric-value">{{ activeTaskCount }}</strong>
            <span class="metric-hint">当前页处于启用状态，可直接纳入调度的任务</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon tone-orange"><el-icon><Clock /></el-icon></div>
          <div class="metric-body">
            <span class="metric-label">Cron 任务</span>
            <strong class="metric-value">{{ cronTaskCount }}</strong>
            <span class="metric-hint">当前页按 Cron 调度的任务数量</span>
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
.hero-panel,
.metric-card,
.filter-card,
.list-card {
  border-radius: 8px;
}

.hero-panel {
  border: 1px solid #ebeef5;
  margin-bottom: 16px;
}

.hero-panel :deep(.el-card__body) {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.8fr);
  gap: 16px;
  padding: 20px 22px;
}

.toolbar-row,
.section-head,
.hero-actions,
.toolbar-actions {
  display: flex;
  gap: 12px;
}

.toolbar-row,
.section-head {
  justify-content: space-between;
  align-items: flex-start;
}

.hero-copy h1,
.section-head h3 {
  margin: 12px 0 10px;
}

.hero-copy h1 {
  font-size: 28px;
  line-height: 1.35;
  font-weight: 600;
  color: #303133;
}

.hero-eyebrow,
.section-meta,
.task-cell span,
.owner-cell small {
  color: var(--el-text-color-secondary);
}

.hero-copy p,
.section-head p {
  margin: 0;
  line-height: 1.8;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.highlight-card {
  height: 100%;
  padding: 18px 20px;
  border-radius: 8px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
}

.highlight-label {
  font-size: 13px;
  color: #909399;
}

.highlight-card ul {
  margin: 12px 0 0;
  padding-left: 18px;
  display: grid;
  gap: 10px;
  line-height: 1.65;
  color: #303133;
}

.hero-actions,
.toolbar-actions {
  flex-wrap: wrap;
}

.metric-row {
  margin-bottom: 16px;
}

.metric-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 112px;
  padding: 18px 20px;
}

.metric-icon {
  width: 56px;
  height: 56px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 24px;
}

.tone-blue {
  color: #fff;
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.tone-green {
  color: #fff;
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.tone-orange {
  color: #fff;
  background: linear-gradient(135deg, #e6a23c, #ebb563);
}

.metric-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 13px;
  color: #909399;
}

.metric-value {
  font-size: 26px;
  line-height: 1;
  color: #303133;
}

.metric-hint {
  font-size: 12px;
  line-height: 1.5;
  color: #909399;
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
  .hero-panel :deep(.el-card__body),
  .toolbar-row {
    grid-template-columns: 1fr;
  }

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
