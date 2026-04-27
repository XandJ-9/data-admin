<template>
  <div class="overview-layout">
    <el-card shadow="hover" class="overview-hero-card">
      <div class="hero-copy">
        <span class="hero-eyebrow">产品首页</span>
        <h2>先判断任务盘子与风险，再进入任务工作面处理具体动作</h2>
        <p>
          数据集成首页不再承载完整工作台，而是先帮助用户快速理解当前任务规模、样本状态和最近需要关注的同步任务，再决定进入列表筛选、执行或深度编辑。
        </p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" :icon="Plus" @click="$emit('create')" v-hasPermi="['dataintegration:task:add']">新建同步任务</el-button>
        <el-button plain type="primary" :icon="Tickets" @click="$emit('browse-tasks')">进入任务列表</el-button>
      </div>
    </el-card>

    <el-row :gutter="16" class="metric-row">
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="metric-card tone-sand">
          <span class="metric-label">任务总量</span>
          <strong class="metric-value">{{ total }}</strong>
          <p>当前默认口径下的数据集成任务总数，适合作为首页规模感知入口。</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="metric-card tone-mint">
          <span class="metric-label">首页样本任务</span>
          <strong class="metric-value">{{ sampleTaskCount }}</strong>
          <p>当前首页已载入的前序样本，用于快速扫一眼负责人、状态和同步路径。</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="metric-card tone-amber">
          <span class="metric-label">样本内启用 / Cron</span>
          <strong class="metric-value">{{ activeTaskCount }} / {{ cronTaskCount }}</strong>
          <p>这两个数字仅基于首页样本，用来提示当前是否存在待运维关注的任务节奏。</p>
        </el-card>
      </el-col>
    </el-row>

    <div class="overview-grid">
      <el-card shadow="hover" class="focus-card">
        <template #header>
          <div class="section-head">
            <div>
              <h3>最近关注任务</h3>
              <p>保留轻量样本，不把首页重新做成第二个大表格。</p>
            </div>
            <el-button link type="primary" @click="$emit('browse-tasks')">查看完整列表</el-button>
          </div>
        </template>

        <div v-if="focusTasks.length" class="focus-list">
          <button v-for="task in focusTasks" :key="task.taskId" type="button" class="focus-item" @click="$emit('open-task', task)">
            <div class="focus-main">
              <div class="focus-title-row">
                <strong>{{ task.taskName }}</strong>
                <el-tag :type="statusTagType(task.status)" size="small">{{ statusLabel(task.status) }}</el-tag>
              </div>
              <div class="focus-route">
                <span>{{ task.sourceDataSourceName || '未配置源' }}</span>
                <el-icon><Right /></el-icon>
                <span>{{ formatTargetTable(task) }}</span>
              </div>
              <div class="focus-meta">
                <el-tag size="small" effect="plain">{{ scheduleTypeLabel(task.scheduleType) }}</el-tag>
                <el-tag size="small" effect="plain">{{ executorLabel(task.executorType) }}</el-tag>
                <span>{{ task.owner || '未指定负责人' }}</span>
              </div>
            </div>
            <el-icon class="focus-arrow"><ArrowRight /></el-icon>
          </button>
        </div>
        <el-empty v-else description="暂无可展示任务样本" />
      </el-card>

      <div class="side-stack">
        <el-card shadow="hover" class="brief-card">
          <template #header><span>首页职责</span></template>
          <ul>
            <li>回答“目前任务盘子有多大、谁值得优先关注”</li>
            <li>不在首页叠加完整筛选、详情抽屉和执行记录工作台</li>
            <li>把批量筛选、执行与维护动作留给任务列表和详情页</li>
          </ul>
        </el-card>

        <el-card shadow="hover" class="brief-card">
          <template #header><span>推荐动作</span></template>
          <div class="action-stack">
            <button type="button" class="action-item" @click="$emit('browse-tasks')">
              <span class="action-index">01</span>
              <div>
                <strong>进入任务列表</strong>
                <p>适合做筛选、分页、执行、删除和快速查看。</p>
              </div>
            </button>
            <button type="button" class="action-item" @click="$emit('create')" v-hasPermi="['dataintegration:task:add']">
              <span class="action-index">02</span>
              <div>
                <strong>新建同步任务</strong>
                <p>直接进入配置页，完成源表到目标表的路径设计。</p>
              </div>
            </button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowRight, Plus, Right, Tickets } from '@element-plus/icons-vue'
import { executorLabel, formatTargetTable, scheduleTypeLabel, statusLabel, statusTagType } from './taskViewMeta'

defineProps({
  total: {
    type: Number,
    default: 0,
  },
  sampleTaskCount: {
    type: Number,
    default: 0,
  },
  activeTaskCount: {
    type: Number,
    default: 0,
  },
  cronTaskCount: {
    type: Number,
    default: 0,
  },
  focusTasks: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['browse-tasks', 'create', 'open-task'])
</script>

<style scoped>
.overview-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.overview-hero-card,
.metric-card,
.focus-card,
.brief-card {
  border-radius: 18px;
}

.overview-hero-card {
  border: 1px solid rgba(207, 179, 122, 0.28);
  background: linear-gradient(135deg, rgba(250, 244, 231, 0.96), rgba(244, 248, 241, 0.96));
}

.overview-hero-card :deep(.el-card__body) {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 24px 26px;
}

.hero-copy {
  max-width: 720px;
}

.hero-eyebrow,
.section-head p,
.metric-card p,
.action-item p,
.focus-meta span,
.brief-card li {
  color: var(--el-text-color-secondary);
}

.hero-copy h2,
.section-head h3 {
  margin: 10px 0 12px;
}

.hero-copy p,
.metric-card p,
.action-item p {
  margin: 0;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-start;
}

.metric-row {
  margin-bottom: 0;
}

.metric-card {
  min-height: 150px;
}

.metric-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
}

.metric-label {
  font-size: 13px;
}

.metric-value {
  font-size: 30px;
  line-height: 1;
  color: #2f2a22;
}

.tone-sand {
  background: linear-gradient(180deg, rgba(246, 235, 214, 0.52), rgba(255, 255, 255, 0.96));
}

.tone-mint {
  background: linear-gradient(180deg, rgba(220, 240, 228, 0.7), rgba(255, 255, 255, 0.96));
}

.tone-amber {
  background: linear-gradient(180deg, rgba(249, 229, 199, 0.68), rgba(255, 255, 255, 0.96));
}

.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(300px, 0.9fr);
  gap: 16px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.section-head h3 {
  font-size: 20px;
}

.focus-list,
.side-stack,
.action-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.focus-item,
.action-item {
  width: 100%;
  border: 0;
  text-align: left;
  cursor: pointer;
}

.focus-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 16px;
  background: #f8f7f2;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.focus-item:hover,
.action-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(31, 35, 41, 0.08);
}

.focus-main,
.focus-title-row,
.focus-meta {
  display: flex;
}

.focus-main {
  flex: 1;
  flex-direction: column;
  gap: 10px;
}

.focus-title-row,
.focus-meta {
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.focus-route {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #5f5a4d;
}

.focus-meta {
  flex-wrap: wrap;
  justify-content: flex-start;
}

.focus-arrow {
  color: #8c6f36;
  font-size: 18px;
  align-self: center;
}

.brief-card ul {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 10px;
  line-height: 1.7;
}

.action-item {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #f7f8f5;
}

.action-index {
  min-width: 36px;
  font-size: 20px;
  line-height: 1;
  color: #8c6f36;
  font-weight: 600;
}

@media (max-width: 992px) {
  .overview-hero-card :deep(.el-card__body),
  .overview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .focus-item,
  .action-item,
  .hero-actions {
    flex-direction: column;
  }

  .focus-title-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>