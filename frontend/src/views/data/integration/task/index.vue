<template>
  <div class="app-container integration-task-page" v-loading="loading">
    <IntegrationTaskWorkbench
      :detail-open="detailOpen"
      :detail-tab="detailTab"
      :execution-detail-visible="executionDetailVisible"
      :execution-dialog-list="executionDialogList"
      :execution-dialog-visible="executionDialogVisible"
      :execution-loading="executionLoading"
      :execution-query-params="executionQueryParams"
      :execution-total="executionTotal"
      :executor-options="executorOptions"
      :preview-executions="previewExecutions"
      :preview-loading="previewLoading"
      :query-params="queryParams"
      :selected-execution="selectedExecution"
      :selected-task="selectedTask"
      :status-options="STATUS_OPTIONS"
      :supported-executors="supportedExecutors"
      :task-list="taskList"
      :total="total"
      @add="handleAdd"
      @delete="handleDelete"
      @edit="handleUpdate"
      @execute="handleExecute"
      @load-executions="loadExecutions"
      @open-execution-detail="openExecutionDetail"
      @open-execution-dialog="openExecutionDialog"
      @open-task-detail="openTaskDetail"
      @query="handleQuery"
      @refresh="getList"
      @refresh-preview="loadExecutionPreview"
      @reset="resetQuery"
      @update:detail-open="detailOpen = $event"
      @update:detail-tab="detailTab = $event"
      @update:execution-detail-visible="executionDetailVisible = $event"
      @update:execution-dialog-visible="executionDialogVisible = $event"
    />
  </div>
</template>

<script setup name="DataIntegrationTask">
import IntegrationTaskWorkbench from '../components/IntegrationTaskWorkbench.vue'
import { useIntegrationPage } from '../components/useIntegrationPage'

const {
  STATUS_OPTIONS,
  detailOpen,
  detailTab,
  executionDetailVisible,
  executionDialogList,
  executionDialogVisible,
  executionLoading,
  executionQueryParams,
  executionTotal,
  executorOptions,
  getList,
  handleAdd,
  handleDelete,
  handleExecute,
  handleQuery,
  handleUpdate,
  loadExecutionPreview,
  loadExecutions,
  loading,
  openExecutionDetail,
  openExecutionDialog,
  openTaskDetail,
  previewExecutions,
  previewLoading,
  queryParams,
  resetQuery,
  selectedExecution,
  selectedTask,
  supportedExecutors,
  taskList,
  total,
} = useIntegrationPage('task')
</script>