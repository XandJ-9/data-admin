<template>
  <div class="app-container integration-detail-page" v-loading="loading">
    <div class="page-head">
      <div>
        <div class="page-breadcrumb">{{ pageBreadcrumb }}</div>
        <h1>{{ pageTitle }}</h1>
        <p>{{ isEditMode ? '直接在详情页完成配置、校验、执行和回看，不再把任务编辑塞进抽屉。' : '先完成源到目标的同步配置，保存后再进入执行与运维视角。' }}</p>
      </div>
      <div class="page-actions">
        <el-button :icon="ArrowLeft" @click="goBack">{{ backButtonText }}</el-button>
        <el-button :loading="validating" @click="handleValidate">校验配置</el-button>
        <el-button
          v-if="taskSnapshot"
          :icon="Histogram"
          @click="openExecutionDialog"
          v-hasPermi="['dataintegration:task:view']"
        >执行记录</el-button>
        <el-button
          v-if="taskSnapshot"
          type="primary"
          plain
          :icon="VideoPlay"
          @click="handleExecute"
          v-hasPermi="['dataintegration:task:execute']"
        >立即执行</el-button>
        <el-button v-if="canSubmit" type="primary" :loading="submitting" @click="submitForm">{{ isEditMode ? '保存修改' : '创建任务' }}</el-button>
      </div>
    </div>

    <div class="page-grid">
      <IntegrationTaskFormSections
        ref="formRef"
        :form="form"
        :rules="rules"
        :data-source-options="dataSourceOptions"
        :status-options="STATUS_OPTIONS"
        :supported-executors="supportedExecutors"
        :current-executor-hint="currentExecutorHint"
        @source-ds-change="handleSourceDataSourceChange"
        @source-table-input="handleSourceTableInput"
        @target-table-input="handleTargetTableInput"
      />

      <div class="side-column">
        <el-card shadow="hover" class="overview-card">
          <template #header><span>配置摘要</span></template>
          <div class="summary-stack">
            <div class="summary-item">
              <span>同步路径</span>
              <strong>{{ routeText }}</strong>
            </div>
            <div class="summary-item">
              <span>执行策略</span>
              <strong>{{ loadTypeLabel(form.loadType) }} / {{ writeModeLabel(form.writeMode) }}</strong>
            </div>
            <div class="summary-item">
              <span>调度方式</span>
              <strong>{{ scheduleTypeLabel(form.scheduleType) }}</strong>
            </div>
            <div class="summary-item">
              <span>当前执行器</span>
              <strong>{{ executorLabel(form.executorType) }}</strong>
            </div>
          </div>
        </el-card>

        <el-card v-if="taskSnapshot" shadow="hover" class="overview-card">
          <template #header><span>任务状态</span></template>
          <div class="status-panel">
            <el-tag :type="statusTagType(taskSnapshot.status)" size="large">{{ statusLabel(taskSnapshot.status) }}</el-tag>
            <p>任务编码：{{ taskSnapshot.taskCode }}</p>
            <p>负责人：{{ taskSnapshot.owner || '未指定' }}</p>
            <p>Cron：{{ taskSnapshot.cronExpression || '未配置' }}</p>
          </div>
        </el-card>

        <el-card shadow="hover" class="overview-card">
          <template #header><span>{{ taskSnapshot ? '设计备注' : '创建提示' }}</span></template>
          <p class="aside-text">
            {{ taskSnapshot?.remark || '先把源数据源、源库名、源表和目标表关系配置准确，再决定调度方式。编排关系暂不放在这里，后续会收敛到发布阶段。' }}
          </p>
        </el-card>
      </div>
    </div>

    <ExecutionRecordsDialog
      v-model="executionDialogVisible"
      v-model:detailVisible="executionDetailVisible"
      :task="taskSnapshot"
      :execution-loading="executionLoading"
      :execution-list="executionList"
      :execution-total="executionTotal"
      :execution-query="executionQueryParams"
      :selected-execution="selectedExecution"
      @refresh="loadExecutions"
      @pagination="loadExecutions"
      @open-detail="openExecutionDetail"
    />
  </div>
</template>

<script setup name="DataIntegrationTaskDetail">
import { ArrowLeft, Histogram, VideoPlay } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import { checkPermi } from '@/utils/permission'
import ExecutionRecordsDialog from './components/ExecutionRecordsDialog.vue'
import IntegrationTaskFormSections from './components/IntegrationTaskFormSections.vue'
import { useIntegrationTaskForm } from './components/useIntegrationTaskForm'
import { executorLabel, loadTypeLabel, scheduleTypeLabel, statusLabel, statusTagType, writeModeLabel } from './components/taskViewMeta'

const route = useRoute()

const {
  STATUS_OPTIONS,
  currentExecutorHint,
  dataSourceOptions,
  executionDetailVisible,
  executionDialogVisible,
  executionList,
  executionLoading,
  executionQueryParams,
  executionTotal,
  form,
  formRef,
  goBack,
  handleExecute,
  handleSourceDataSourceChange,
  handleSourceTableInput,
  handleTargetTableInput,
  handleValidate,
  isEditMode,
  loadExecutions,
  loading,
  openExecutionDetail,
  openExecutionDialog,
  pageTitle,
  rules,
  selectedExecution,
  submitting,
  supportedExecutors,
  submitForm,
  taskSnapshot,
  validating,
} = useIntegrationTaskForm()

const routeText = computed(() => {
  const sourceName = form.value.sourceDatabaseName
    ? `${form.value.sourceDatabaseName}.${form.value.sourceTableName || '未填写源表'}`
    : (form.value.sourceTableName || '未填写源表')
  const targetName = form.value.targetSchemaName ? `${form.value.targetSchemaName}.${form.value.targetTableName || '未命名目标表'}` : (form.value.targetTableName || '未命名目标表')
  return `${sourceName} -> ${targetName}`
})

const isFromTaskOps = computed(() => ['task-center', 'task-detail'].includes(route.query.from))
const canSubmit = computed(() => (isEditMode.value ? checkPermi(['dataintegration:task:edit']) : checkPermi(['dataintegration:task:add'])))

const pageBreadcrumb = computed(() => (isFromTaskOps.value ? '任务运维 / 数据集成' : '数据集成 / 任务详情'))

const backButtonText = computed(() => (isFromTaskOps.value ? '返回任务运维' : '返回数据集成'))
</script>

<style scoped>
.integration-detail-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-head,
.page-actions {
  display: flex;
  gap: 12px;
}

.page-head {
  justify-content: space-between;
  align-items: flex-start;
}

.page-head h1 {
  margin: 6px 0 10px;
}

.page-head p,
.page-breadcrumb,
.aside-text,
.status-panel p {
  color: var(--el-text-color-secondary);
}

.page-breadcrumb {
  font-size: 13px;
}

.page-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.page-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.9fr) minmax(280px, 0.9fr);
  gap: 20px;
  align-items: start;
}

.side-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.overview-card {
  border-radius: 18px;
}

.summary-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.summary-item span {
  display: block;
  margin-bottom: 6px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.summary-item strong {
  line-height: 1.6;
}

.status-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-panel p,
.aside-text {
  margin: 0;
  line-height: 1.7;
}

@media (max-width: 1200px) {
  .page-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-head {
    flex-direction: column;
  }

  .page-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
