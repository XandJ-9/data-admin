<template>
  <div class="script-list-panel">
    <div class="panel-header">
      <div class="panel-actions">
        <el-button plain @click="$emit('create', 'python')">新建 Python</el-button>
        <el-button type="primary" @click="$emit('create', 'sql')">新建 SQL</el-button>
        <el-button circle :icon="Refresh" @click="$emit('refresh')" />
      </div>
    </div>

    <el-form :inline="true" :model="localQuery" class="query-form" @submit.prevent>
      <el-form-item>
        <el-input
          v-model="localQuery.scriptName"
          clearable
          placeholder="搜索脚本名称"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-select v-model="localQuery.scriptType" clearable placeholder="脚本类型" style="width: 120px">
          <el-option label="SQL" value="sql" />
          <el-option label="Python" value="python" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="localQuery.directoryId" clearable placeholder="所属目录" style="width: 180px">
          <el-option label="未分配目录" :value="0" />
          <el-option
            v-for="directory in directories"
            :key="directory.directoryId"
            :label="directory.directoryName"
            :value="directory.directoryId"
          />
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
      <el-table-column label="脚本名称" min-width="220" show-overflow-tooltip>
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
      <el-table-column label="执行环境" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ getRuntimeLabel(row) }}</template>
      </el-table-column>
      <el-table-column label="所属目录" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.directoryName || '未分配目录' }}</template>
      </el-table-column>
      <el-table-column label="负责人" width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.owner || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
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
          <el-button link type="danger" @click.stop="$emit('delete', row)">删除</el-button>
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
  directories: { type: Array, default: () => [] },
  query: {
    type: Object,
    default: () => ({ pageNum: 1, pageSize: 10, scriptName: '', scriptType: '', directoryId: undefined }),
  },
})

const emit = defineEmits(['select', 'create', 'delete', 'refresh', 'search', 'reset', 'page-change'])

const localQuery = reactive({
  pageNum: 1,
  pageSize: 10,
  scriptName: '',
  scriptType: '',
  directoryId: undefined,
})

const engineLabelMap = { spark: 'Spark SQL', hive: 'Hive', mvp: 'MVP预演' }

function syncLocalQuery() {
  localQuery.pageNum = props.query.pageNum || 1
  localQuery.pageSize = props.query.pageSize || 10
  localQuery.scriptName = props.query.scriptName || ''
  localQuery.scriptType = props.query.scriptType || ''
  localQuery.directoryId = props.query.directoryId ?? undefined
}

function statusLabel(status) {
  return { draft: '草稿', published: '正式', archived: '归档' }[status] || '草稿'
}

function statusTagType(status) {
  return { draft: 'info', published: 'success', archived: 'warning' }[status] || 'info'
}

function getRuntimeLabel(script) {
  if (script?.datasourceName) return script.datasourceName
  return engineLabelMap[script?.engineType] || '未配置'
}

function handleSearch() {
  emit('search', {
    pageNum: 1,
    pageSize: localQuery.pageSize,
    scriptName: localQuery.scriptName.trim(),
    scriptType: localQuery.scriptType || '',
    directoryId: localQuery.directoryId,
  })
}

function handleReset() {
  syncLocalQuery()
  localQuery.scriptName = ''
  localQuery.scriptType = ''
  localQuery.directoryId = undefined
  localQuery.pageNum = 1
  emit('reset')
}

function handlePagination() {
  emit('page-change', {
    pageNum: localQuery.pageNum,
    pageSize: localQuery.pageSize,
    scriptName: localQuery.scriptName.trim(),
    scriptType: localQuery.scriptType || '',
    directoryId: localQuery.directoryId,
  })
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

.script-code {
  font-size: 12px;
  line-height: 1.5;
  color: #8a97a8;
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
