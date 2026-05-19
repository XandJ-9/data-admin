<template>
  <div class="script-list-panel">
    <div class="panel-header">
      <div class="panel-actions">
        <el-button plain v-hasPermi="['datadev:ide:add']" @click="$emit('create', 'python')">新建 Python 作业</el-button>
        <el-button type="primary" v-hasPermi="['datadev:ide:add']" @click="$emit('create', 'sql')">新建 SQL 作业</el-button>
        <el-button circle :icon="Refresh" @click="$emit('refresh')" />
      </div>
    </div>

    <el-form :inline="true" :model="localQuery" class="query-form" @submit.prevent>
      <el-form-item>
        <el-input
          v-model="localQuery.scriptName"
          clearable
          placeholder="搜索作业名称"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-select v-model="localQuery.scriptType" clearable placeholder="作业类型" style="width: 120px">
          <el-option label="SQL" value="sql" />
          <el-option label="Python" value="python" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="localQuery.scriptRole" clearable placeholder="作业用途" style="width: 150px">
          <el-option v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="localQuery.targetModelId" clearable placeholder="目标模型" style="width: 220px">
          <el-option v-for="model in models" :key="model.modelId" :label="model.modelName" :value="model.modelId" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table
      v-loading="loading"
      :data="scripts"
      row-key="scriptId"
      class="script-table"
      highlight-current-row
      @row-click="row => $emit('select', row)"
    >
      <el-table-column label="作业名称" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">
          <el-button link type="primary" @click.stop="$emit('select', row)">{{ row.scriptName }}</el-button>
          <div class="script-code">{{ row.scriptCode }}</div>
        </template>
      </el-table-column>
      <el-table-column label="类型" width="90">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">{{ (row.scriptType || 'sql').toUpperCase() }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="用途" width="120">
        <template #default="{ row }">{{ roleLabel(row.scriptRole) }}</template>
      </el-table-column>
      <el-table-column label="目标模型" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          <span>{{ row.targetModelName || '未绑定' }}</span>
          <span v-if="row.targetLayer" class="sub-text">{{ row.targetLayer }}</span>
        </template>
      </el-table-column>
      <el-table-column label="执行环境" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ getRuntimeLabel(row) }}</template>
      </el-table-column>
      <el-table-column label="任务运维" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="taskStatusTag(row.taskStatus)" effect="plain">{{ taskStatusLabel(row.taskStatus) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="负责人" width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.owner || '-' }}</template>
      </el-table-column>
      <el-table-column label="版本状态" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="statusTagType(row.status)" effect="plain">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="说明" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">{{ row.description || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click.stop="$emit('select', row)">详情</el-button>
          <el-button link type="danger" v-hasPermi="['datadev:ide:remove']" @click.stop="$emit('delete', row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="localQuery.pageNum"
      v-model:limit="localQuery.pageSize"
      @pagination="handlePagination"
    />
  </div>
</template>

<script setup>
import { Refresh } from '@element-plus/icons-vue'

defineOptions({ name: 'DevScriptListPanel' })

const props = defineProps({
  loading: { type: Boolean, default: false },
  scripts: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  models: { type: Array, default: () => [] },
  query: {
    type: Object,
    default: () => ({ pageNum: 1, pageSize: 10, scriptName: '', scriptType: '', scriptRole: '', targetModelId: undefined }),
  },
})

const emit = defineEmits(['select', 'create', 'delete', 'refresh', 'search', 'reset', 'page-change'])

const localQuery = reactive({
  pageNum: 1,
  pageSize: 10,
  scriptName: '',
  scriptType: '',
  scriptRole: '',
  targetModelId: undefined,
})

const roleOptions = [
  { label: '探索分析', value: 'explore' },
  { label: '模型加工', value: 'transform' },
  { label: '质量校验', value: 'quality' },
  { label: '数据回刷', value: 'backfill' },
  { label: 'Python 作业', value: 'python_job' },
]
const engineLabelMap = { spark: 'Spark SQL', hive: 'Hive', mvp: 'MVP 预演' }

function syncLocalQuery() {
  localQuery.pageNum = props.query.pageNum || 1
  localQuery.pageSize = props.query.pageSize || 10
  localQuery.scriptName = props.query.scriptName || ''
  localQuery.scriptType = props.query.scriptType || ''
  localQuery.scriptRole = props.query.scriptRole || ''
  localQuery.targetModelId = props.query.targetModelId ?? undefined
}

function roleLabel(value) {
  return roleOptions.find(item => item.value === value)?.label || '未设置'
}

function statusLabel(status) {
  return { draft: '草稿', published: '正式', archived: '归档' }[status] || '草稿'
}

function statusTagType(status) {
  return { draft: 'info', published: 'success', archived: 'warning' }[status] || 'info'
}

function taskStatusLabel(status) {
  return { active: '已纳管', paused: '已暂停', draft: '草稿', archived: '已归档' }[status] || '未发布'
}

function taskStatusTag(status) {
  return status ? ({ active: 'success', paused: 'warning', draft: 'info', archived: 'danger' }[status] || 'info') : 'info'
}

function getRuntimeLabel(script) {
  if (script?.datasourceName) return script.datasourceName
  return engineLabelMap[script?.engineType] || '未配置'
}

function buildQueryPayload() {
  return {
    pageNum: localQuery.pageNum,
    pageSize: localQuery.pageSize,
    scriptName: localQuery.scriptName.trim(),
    scriptType: localQuery.scriptType || '',
    scriptRole: localQuery.scriptRole || '',
    targetModelId: localQuery.targetModelId,
  }
}

function handleSearch() {
  emit('search', { ...buildQueryPayload(), pageNum: 1 })
}

function handleReset() {
  syncLocalQuery()
  localQuery.scriptName = ''
  localQuery.scriptType = ''
  localQuery.scriptRole = ''
  localQuery.targetModelId = undefined
  localQuery.pageNum = 1
  emit('reset')
}

function handlePagination() {
  emit('page-change', buildQueryPayload())
}

watch(
  () => props.query,
  () => {
    syncLocalQuery()
  },
  { immediate: true, deep: true },
)
</script>

<style lang="scss" scoped>
.script-list-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  background: #fff;
}

.panel-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.query-form {
  margin-bottom: 12px;
}

.script-table {
  flex: 1;
  min-height: 0;
}

.script-code,
.sub-text {
  font-size: 12px;
  line-height: 1.5;
  color: #8a97a8;
}

.sub-text {
  display: block;
}

@media (max-width: 768px) {
  .script-list-panel {
    padding: 12px;
  }

  .panel-header {
    justify-content: flex-start;
  }

  .panel-actions {
    width: 100%;
  }
}
</style>
