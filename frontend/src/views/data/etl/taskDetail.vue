<template>
  <div class="app-container etl-task-detail">
    <!-- 页面头部 -->
    <el-page-header @back="handleBack" class="page-header">
      <template #content>
        <div class="header-content">
          <span v-if="!isEdit">{{ taskForm.taskName || '新建ETL任务' }}</span>
          <el-input
            v-else
            v-model="taskForm.taskName"
            placeholder="请输入任务名称"
            style="width: 300px"
          />
        </div>
      </template>
      <template #extra>
        <div class="header-actions">
          <template v-if="isEdit">
            <el-button @click="isEdit = false">取消</el-button>
            <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
          </template>
          <template v-else>
            <el-button @click="handleExecute" :disabled="taskForm.status !== '0'">
              <el-icon><VideoPlay /></el-icon> 执行任务
            </el-button>
            <el-button @click="isEdit = true">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-dropdown @command="handleMoreCommand">
              <el-button>
                更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="clone">克隆任务</el-dropdown-item>
                  <el-dropdown-item command="version">版本管理</el-dropdown-item>
                  <el-dropdown-item command="validate">验证配置</el-dropdown-item>
                  <el-dropdown-item command="datx" divided>生成DataX配置</el-dropdown-item>
                  <el-dropdown-item command="dryRun">模拟执行</el-dropdown-item>
                  <el-dropdown-item command="delete" divided style="color: #f56c6c">删除任务</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </div>
      </template>
    </el-page-header>

    <!-- 任务状态标签 -->
    <div class="task-status-bar">
      <el-tag :type="taskForm.status === '0' ? 'success' : 'danger'" size="large">
        {{ taskForm.status === '0' ? '已启用' : '已停用' }}
      </el-tag>
      <el-tag v-if="taskForm.etlType" :type="getEtlTypeColor(taskForm.etlType)" size="large">
        {{ getEtlTypeText(taskForm.etlType) }}
      </el-tag>
      <el-tag size="large">{{ getExecutorTypeText(taskForm.executorType) }}</el-tag>
      <el-tag :type="taskForm.executeStrategy === 'full' ? 'success' : 'warning'" size="large">
        {{ taskForm.executeStrategy === 'full' ? '全量' : '增量' }}
      </el-tag>
    </div>

    <!-- 内容区域 -->
    <el-card class="detail-card">
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="基本信息" name="basic">
          <BasicInfoTab :form="taskForm" :is-edit="isEdit" />
        </el-tab-pane>

        <el-tab-pane label="数据源配置" name="datasource">
          <DatasourceTab
            :form="taskForm"
            :is-edit="isEdit"
            :datasource-list="datasourceList"
            @columns-loaded="handleColumnsLoaded"
          />
        </el-tab-pane>

        <el-tab-pane label="数据映射" name="mapping">
          <DataMappingTab
            :form="taskForm"
            :is-edit="isEdit"
            :source-columns="sourceColumns"
            :field-mappings="fieldMappings"
          />
        </el-tab-pane>

        <el-tab-pane label="执行配置" name="execution">
          <ExecutionConfigTab :form="taskForm" :is-edit="isEdit" />
        </el-tab-pane>

        <el-tab-pane label="质检规则" name="quality">
          <QualityRulesTab
            :rules="qualityRules"
            @add="handleAddQualityRule"
            @toggle="handleToggleQualityRule"
            @view="handleViewQualityRule"
            @delete="handleDeleteQualityRule"
          />
        </el-tab-pane>

        <el-tab-pane label="执行历史" name="history">
          <ExecutionHistoryTab
            :logs="executionLogs"
            :total="totalLogs"
            :query="logQuery"
            :loading="loadingLogs"
            @view="handleViewExecution"
            @load="loadExecutionLogs"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 执行详情对话框 -->
    <el-dialog
      v-model="executionDetailVisible"
      title="执行详情"
      width="900px"
      append-to-body
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="执行ID">{{ currentExecution.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getExecutionStatusColor(currentExecution.status)">
            {{ getExecutionStatusText(currentExecution.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="读取行数">{{ formatNumber(currentExecution.rowsRead) }}</el-descriptions-item>
        <el-descriptions-item label="写入行数">{{ formatNumber(currentExecution.rowsWritten) }}</el-descriptions-item>
        <el-descriptions-item label="数据大小">{{ formatBytes(currentExecution.dataSize) }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ formatDuration(currentExecution.duration) }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ currentExecution.startTime }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ currentExecution.endTime }}</el-descriptions-item>
        <el-descriptions-item label="执行者">{{ currentExecution.executedBy }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2">
          <span style="color: #f56c6c">{{ currentExecution.errorMessage || '-' }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup name="ETLTaskDetail">
import { VideoPlay, Edit, ArrowDown } from '@element-plus/icons-vue'
import BasicInfoTab from './components/BasicInfoTab.vue'
import DatasourceTab from './components/DatasourceTab.vue'
import DataMappingTab from './components/DataMappingTab.vue'
import ExecutionConfigTab from './components/ExecutionConfigTab.vue'
import QualityRulesTab from './components/QualityRulesTab.vue'
import ExecutionHistoryTab from './components/ExecutionHistoryTab.vue'
import { useETLTaskDetail } from './composables/useETLTaskDetail'
import {
  getEtlTypeColor, getEtlTypeText, getExecutorTypeText,
  getExecutionStatusText, getExecutionStatusColor,
  formatNumber, formatBytes, formatDuration
} from './composables/useETLFormatters'

const {
  isEdit, saving, loadingLogs, activeTab, executionDetailVisible,
  taskId, datasourceList, fieldMappings, sourceColumns,
  qualityRules, executionLogs, totalLogs, currentExecution,
  taskForm, logQuery,
  handleColumnsLoaded, handleSave, handleExecute,
  handleMoreCommand, handleBack,
  handleAddQualityRule, handleToggleQualityRule,
  handleViewQualityRule, handleDeleteQualityRule,
  handleViewExecution, loadExecutionLogs
} = useETLTaskDetail()
</script>

<style scoped lang="scss">
.etl-task-detail {
  .page-header {
    margin-bottom: 16px;

    .header-content {
      display: flex;
      align-items: center;
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .task-status-bar {
    margin-bottom: 16px;
    display: flex;
    gap: 12px;
  }
}

:deep(.json-dialog) {
  .el-message-box__content {
    text-align: left;
    pre {
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }
}
</style>
