<template>
  <div class="config-summary">
    <el-descriptions :column="2" border>
      <el-descriptions-item label="场景类型">
        {{ scenarioInfo.title }}
      </el-descriptions-item>
      <el-descriptions-item label="任务名称">
        {{ config.taskName }}
      </el-descriptions-item>

      <el-descriptions-item label="源数据源">
        {{ config.sourceDatasourceId || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="源表">
        {{ config.sourceTable || '-' }}
      </el-descriptions-item>

      <el-descriptions-item label="目标数据源">
        {{ config.targetDatasourceId || '数仓' }}
      </el-descriptions-item>
      <el-descriptions-item label="目标表">
        {{ config.targetTable || '-' }}
      </el-descriptions-item>

      <el-descriptions-item label="同步方式">
        <el-tag :type="config.syncMode === 'full' ? 'success' : 'warning'" size="small">
          {{ config.syncMode === 'full' ? '全量同步' : '增量同步' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="执行方式">
        <el-tag :type="config.scheduleType === 'manual' ? 'primary' : 'info'" size="small">
          {{ config.scheduleType === 'manual' ? '立即执行' : '定时执行' }}
        </el-tag>
        <span v-if="config.scheduleType === 'scheduled'" style="margin-left: 8px; color: #909399">
          {{ config.scheduleCron }}
        </span>
      </el-descriptions-item>

      <el-descriptions-item label="字段映射" :span="2">
        <span v-if="fieldMappingCount > 0">
          已映射 <strong>{{ fieldMappingCount }}</strong> 个字段
        </span>
        <span v-else style="color: #909399">暂无映射</span>
      </el-descriptions-item>

      <el-descriptions-item v-if="config.whereCondition" label="过滤条件" :span="2">
        <code>{{ config.whereCondition }}</code>
      </el-descriptions-item>

      <el-descriptions-item v-if="config.transformRules" label="清洗规则" :span="2">
        <div style="white-space: pre-wrap">{{ config.transformRules }}</div>
      </el-descriptions-item>
    </el-descriptions>

    <!-- 执行预览 -->
    <el-alert
      type="info"
      :closable="false"
      style="margin-top: 16px"
    >
      <template #default>
        <div class="execution-preview">
          <div class="preview-title">
            <el-icon><InfoFilled /></el-icon>
            执行预览
          </div>
          <ul class="preview-steps">
            <li v-for="(step, index) in executionSteps" :key="index">
              <el-icon class="step-icon"><Check /></el-icon>
              {{ step }}
            </li>
          </ul>
        </div>
      </template>
    </el-alert>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { InfoFilled, Check } from '@element-plus/icons-vue'
import { getScenarioInfo } from './scenarioConfig'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  scenario: {
    type: String,
    required: true
  }
})

const scenarioInfo = computed(() => getScenarioInfo(props.scenario))

const fieldMappingCount = computed(() => {
  return props.config.fieldMappings?.length || 0
})

const executionSteps = computed(() => {
  const steps = []

  if (props.scenario === 'biz_to_stg') {
    steps.push(`从 ${props.config.sourceTable} 读取数据`)
    if (props.config.whereCondition) {
      steps.push('应用过滤条件')
    }
    steps.push('写入STG层并创建日期分区')
  } else if (props.scenario === 'stg_to_ods') {
    steps.push(`从STG层读取 ${props.config.sourceTable}`)
    if (props.config.transformRules) {
      steps.push('应用数据清洗规则')
    }
    steps.push('写入ODS层')
  } else if (props.scenario === 'warehouse_transform') {
    steps.push('执行Spark SQL脚本')
    steps.push(`写入 ${props.config.targetLayer?.toUpperCase()} 层`)
  } else if (props.scenario === 'warehouse_to_biz') {
    steps.push(`从数仓读取 ${props.config.sourceTable}`)
    steps.push(`写入 ${props.config.targetTable}`)
  } else if (props.scenario === 'db_to_db') {
    steps.push(`从源库读取 ${props.config.sourceTable}`)
    steps.push(`写入目标库 ${props.config.targetTable}`)
  }

  if (props.config.syncMode === 'incremental') {
    steps.push(`只同步增量数据（基于 ${props.config.incrementalField} 字段）`)
  } else {
    steps.push('全量同步数据')
  }

  if (props.config.scheduleType === 'manual') {
    steps.push('保存后立即执行')
  } else {
    steps.push(`按照 ${props.config.scheduleCron} 定时执行`)
  }

  return steps
})
</script>

<style scoped>
.config-summary code {
  padding: 2px 6px;
  background-color: #f5f7fa;
  border-radius: 3px;
  color: #606266;
  font-size: 12px;
}

.execution-preview {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #409EFF;
  white-space: nowrap;
}

.preview-steps {
  margin: 0;
  padding-left: 20px;
  flex: 1;
}

.preview-steps li {
  color: #606266;
  font-size: 13px;
  line-height: 1.8;
  display: flex;
  align-items: center;
  gap: 6px;
}

.step-icon {
  color: #67C23A;
  font-size: 14px;
}
</style>
