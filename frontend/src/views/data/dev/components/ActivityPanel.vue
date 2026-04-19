<template>
  <div class="activity-panel">
    <el-tabs v-model="currentTab" class="activity-tabs">
      <el-tab-pane label="版本历史" name="versions">
        <el-scrollbar class="activity-scroll">
          <div class="version-filter">
            <el-radio-group v-model="currentVersionView" size="small">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="released">正式</el-radio-button>
              <el-radio-button label="draft">草稿</el-radio-button>
            </el-radio-group>
          </div>
          <div v-if="filteredVersions.length === 0" class="empty-tip">{{ versionEmptyText }}</div>
          <div
            v-for="version in filteredVersions"
            :key="version.versionId"
            class="version-item"
            :class="{ current: version.isCurrent, selected: selectedVersionId === version.versionId }"
            @click="$emit('preview-version', version)"
          >
            <div class="version-head">
              <span class="version-num">v{{ version.versionNumber }}</span>
              <div class="version-tags">
                <el-tag :type="version.isReleased ? 'success' : 'info'" size="small" effect="plain">
                  {{ version.isReleased ? '正式' : '草稿' }}
                </el-tag>
                <el-tag v-if="version.isCurrent" type="success" size="small" effect="plain">当前</el-tag>
              </div>
              <el-button
                v-if="!version.isCurrent && version.isReleased"
                link
                type="primary"
                size="small"
                @click.stop="$emit('rollback-version', version)"
              >回滚</el-button>
            </div>
            <div class="version-meta">
              <span>{{ version.createBy || '-' }}</span>
              <span>{{ version.createTime }}</span>
            </div>
            <div v-if="version.changeLog" class="version-log">{{ version.changeLog }}</div>
          </div>
        </el-scrollbar>
      </el-tab-pane>
      <el-tab-pane label="执行记录" name="executions">
        <el-scrollbar class="activity-scroll">
          <div v-if="executions.length === 0" class="empty-tip">暂无记录</div>
          <div v-for="execution in executions" :key="execution.executionId" class="exec-item">
            <div class="exec-head">
              <el-tag :type="execTagType(execution.status)" size="small" effect="plain">
                {{ execStatusLabel(execution.status) }}
              </el-tag>
              <span class="exec-time">{{ execution.createTime }}</span>
            </div>
            <div class="exec-meta">
              <span v-if="execution.durationSeconds !== null">耗时 {{ execution.durationSeconds }}s</span>
              <span>{{ execution.executedBy }}</span>
            </div>
            <div v-if="execution.errorMessage" class="exec-error">{{ execution.errorMessage }}</div>
          </div>
        </el-scrollbar>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
defineOptions({ name: 'DevActivityPanel' })

const props = defineProps({
  activeTab: { type: String, default: 'versions' },
  versionView: { type: String, default: 'all' },
  filteredVersions: { type: Array, default: () => [] },
  selectedVersionId: { type: Number, default: null },
  versionEmptyText: { type: String, default: '暂无版本' },
  executions: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:activeTab', 'update:versionView', 'preview-version', 'rollback-version'])

const currentTab = computed({
  get: () => props.activeTab,
  set: (value) => emit('update:activeTab', value),
})

const currentVersionView = computed({
  get: () => props.versionView,
  set: (value) => emit('update:versionView', value),
})

function execTagType(status) {
  const map = { pending: 'info', running: 'warning', success: 'success', failed: 'danger', cancelled: 'info' }
  return map[status] || 'info'
}

function execStatusLabel(status) {
  const map = { pending: '已提交', running: '执行中', success: '成功', failed: '失败', cancelled: '已取消' }
  return map[status] || status
}
</script>

<style lang="scss" scoped>
.activity-panel {
  height: 100%;
}

.activity-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;

  :deep(.el-tabs__header) {
    margin-bottom: 0;
    padding: 0 12px;
  }

  :deep(.el-tabs__content) {
    flex: 1;
    min-height: 0;
  }

  :deep(.el-tab-pane) {
    height: 100%;
  }
}

.activity-scroll {
  height: 100%;
  padding: 8px 12px 12px;
}

.version-filter {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.empty-tip {
  text-align: center;
  color: #66768b;
  font-size: 13px;
  padding: 32px 0;
}

.version-item,
.exec-item {
  padding: 10px 12px;
  border-radius: 10px;
  margin-bottom: 8px;
  border: 1px solid #e5ebf3;
  background: #fbfdff;
}

.version-item {
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    border-color: #b9d4f0;
  }

  &.selected {
    border-color: #7fb2e6;
    box-shadow: inset 0 0 0 1px rgba(127, 178, 230, 0.4);
  }

  &.current {
    border-color: #9ad7b7;
    background: #e5f6f1;
  }
}

.version-head,
.exec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.version-tags {
  display: flex;
  align-items: center;
  gap: 6px;
}

.version-num {
  font-weight: 600;
  font-size: 13px;
  color: #303133;
}

.version-meta,
.exec-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.version-log,
.exec-error {
  font-size: 12px;
  margin-top: 4px;
}

.version-log {
  color: #606266;
}

.exec-time {
  font-size: 12px;
  color: #909399;
}

.exec-error {
  color: #f56c6c;
  word-break: break-all;
}
</style>
