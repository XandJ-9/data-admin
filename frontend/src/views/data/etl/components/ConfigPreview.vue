<template>
  <div class="config-preview">
    <el-descriptions :column="1" border>
      <!-- 基本信息 -->
      <el-descriptions-item label="任务名称">
        {{ config.taskName || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="任务编码">
        {{ config.taskCode || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="ETL类型">
        <el-tag :type="getEtlTypeTag(config.etlType)">
          {{ getEtlTypeLabel(config.etlType) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="业务域">
        {{ config.businessDomain || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="优先级">
        <el-tag :type="getPriorityTag(config.priority)">
          {{ getPriorityLabel(config.priority) }}
        </el-tag>
      </el-descriptions-item>

      <!-- 源端配置 -->
      <el-descriptions-item label="源数据源">
        {{ getDatasourceName(config.sourceDatasourceId) || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="源数据库">
        {{ config.sourceDatabase || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="源表/查询">
        <span v-if="config.sourceQueryType === 'table'">
          {{ config.sourceTableName || '-' }}
        </span>
        <pre v-else class="sql-preview">{{ config.sourceQuery || '-' }}</pre>
      </el-descriptions-item>
      <el-descriptions-item label="抽取模式">
        <el-tag :type="config.extractMode === 'full' ? 'success' : 'warning'">
          {{ config.extractMode === 'full' ? '全量' : '增量' }}
        </el-tag>
        <span v-if="config.extractMode === 'increment'" style="margin-left: 8px">
          字段：{{ config.incrementField || '-' }}
        </span>
      </el-descriptions-item>

      <!-- 转换配置 -->
      <el-descriptions-item label="字段映射数">
        {{ config.fieldMappings?.length || 0 }} 对
      </el-descriptions-item>

      <!-- 目标端配置 -->
      <el-descriptions-item label="目标数据源">
        {{ getDatasourceName(config.targetDatasourceId) || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="目标数据库">
        {{ config.targetDatabase || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="目标表">
        {{ config.targetTableName || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="写入模式">
        <el-tag :type="getWriteModeTag(config.writeMode)">
          {{ getWriteModeLabel(config.writeMode) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="分区字段" v-if="config.partitionFields?.length">
        {{ config.partitionFields.join(', ') }}
      </el-descriptions-item>

      <!-- 高级配置 -->
      <el-descriptions-item label="执行方式">
        <el-tag :type="config.scheduleType === 'manual' ? 'info' : 'primary'">
          {{ config.scheduleType === 'manual' ? '手动执行' : '定时调度' }}
        </el-tag>
        <span v-if="config.scheduleType === 'scheduled'" style="margin-left: 8px">
          {{ config.scheduleCron || '-' }}
        </span>
      </el-descriptions-item>
      <el-descriptions-item label="资源配置">
        {{ config.executorMemory || '-' }} × {{ config.executorInstances || 1 }} 实例
        ({{ config.executorCores || 2 }}核)
      </el-descriptions-item>
      <el-descriptions-item label="失败重试">
        {{ config.retryTimes || 0 }} 次，间隔 {{ config.retryInterval || 60 }} 秒
      </el-descriptions-item>
      <el-descriptions-item label="超时时间">
        {{ config.timeout || 300 }} 秒
      </el-descriptions-item>
    </el-descriptions>

    <!-- 字段映射详情 -->
    <el-divider content-position="left">字段映射详情</el-divider>
    <el-table
      :data="config.fieldMappings || []"
      border
      size="small"
      max-height="300"
    >
      <el-table-column type="index" label="#" width="50" />
      <el-table-column prop="source" label="源字段" min-width="150" />
      <el-table-column prop="target" label="目标字段" min-width="150" />
      <el-table-column prop="transform" label="转换规则" min-width="200" />
    </el-table>

    <!-- SQL脚本 -->
    <template v-if="etlType === 'sql_task' && config.sqlScript">
      <el-divider content-position="left">SQL脚本</el-divider>
      <pre class="sql-script">{{ config.sqlScript }}</pre>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  etlType: {
    type: String,
    default: 'data_integration'
  },
  datasourceOptions: {
    type: Array,
    default: () => []
  }
})

// 获取数据源名称
function getDatasourceName(id) {
  const ds = props.datasourceOptions.find(d => d.id === id)
  return ds?.name || id
}

// 获取ETL类型标签
function getEtlTypeTag(type) {
  const tags = {
    data_integration: 'success',
    sql_task: 'primary'
  }
  return tags[type] || 'info'
}

function getEtlTypeLabel(type) {
  const labels = {
    data_integration: '数据集成',
    sql_task: 'SQL任务'
  }
  return labels[type] || type || '-'
}

// 获取优先级标签
function getPriorityTag(priority) {
  const tags = {
    low: 'info',
    medium: 'warning',
    high: 'danger'
  }
  return tags[priority] || 'info'
}

function getPriorityLabel(priority) {
  const labels = {
    low: '低',
    medium: '中',
    high: '高'
  }
  return labels[priority] || priority || '-'
}

// 获取写入模式标签
function getWriteModeTag(mode) {
  const tags = {
    append: 'primary',
    overwrite: 'danger',
    upsert: 'success'
  }
  return tags[mode] || 'info'
}

function getWriteModeLabel(mode) {
  const labels = {
    append: '追加',
    overwrite: '覆盖',
    upsert: '更新'
  }
  return labels[mode] || mode || '-'
}
</script>

<style scoped lang="scss">
.config-preview {
  .sql-preview {
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: monospace;
    font-size: 12px;
    background: #f5f7fa;
    padding: 8px;
    border-radius: 4px;
  }

  .sql-script {
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: monospace;
    font-size: 13px;
    background: #f5f7fa;
    padding: 16px;
    border-radius: 4px;
    max-height: 400px;
    overflow-y: auto;
  }
}
</style>
