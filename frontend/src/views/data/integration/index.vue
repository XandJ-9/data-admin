<template>
  <div class="app-container integration-overview" v-loading="loading">
    <el-card shadow="hover" class="hero-panel">
      <div class="hero-copy">
        <span class="hero-eyebrow">数据集成</span>
        <h1>把入仓规模、同步节奏和待处理任务先讲清楚，再进入任务工作面执行</h1>
        <p>
          数据集成首页只负责回答“现在有多少同步任务、近期应该关注什么、下一步该去哪里处理”。
          具体的筛选、执行、维护和运行回看，统一收敛到独立的任务列表页面。
        </p>
        <div class="hero-actions">
          <el-button type="primary" @click="goToTaskList">进入任务列表</el-button>
          <el-button plain type="primary" @click="handleAdd()" v-hasPermi="['dataintegration:task:add']">新建同步任务</el-button>
        </div>
        <div class="hero-tags">
          <el-tag size="small" type="primary" effect="light" round>贴源入仓任务配置</el-tag>
          <el-tag size="small" effect="plain" round>执行与运行回看分离</el-tag>
          <el-tag size="small" effect="plain" round>首页只做判断与导航</el-tag>
        </div>
      </div>
      <div class="hero-highlight">
        <div class="highlight-card">
          <span class="highlight-label">首页定位</span>
          <ul>
            <li>先看当前同步任务盘子和启用节奏</li>
            <li>再决定进入任务列表做筛选、执行和编辑</li>
            <li>避免把概览、列表、详情抽屉都堆在同一页</li>
          </ul>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="metric-row">
      <el-col v-for="item in overviewCards" :key="item.title" :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="metric-card" @click="item.action && item.action()">
          <div class="metric-icon" :class="item.tone">
            <el-icon><component :is="item.icon" /></el-icon>
          </div>
          <div class="metric-body">
            <span class="metric-label">{{ item.title }}</span>
            <strong class="metric-value">{{ item.value }}</strong>
            <span class="metric-hint">{{ item.hint }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="content-row">
      <el-col :xs="24" :lg="15">
        <el-card class="content-card capability-card" shadow="hover">
          <template #header>
            <div class="section-head">
              <div>
                <h2>核心能力</h2>
                <p>帮助用户先理解数据集成在平台中的职责，再进入具体页面处理。</p>
              </div>
            </div>
          </template>
          <div class="capability-grid">
            <article v-for="item in capabilities" :key="item.title" class="capability-item" @click="item.action()">
              <div class="capability-icon">
                <el-icon><component :is="item.icon" /></el-icon>
              </div>
              <div class="capability-content">
                <h3>{{ item.title }}</h3>
                <p>{{ item.description }}</p>
                <ul>
                  <li v-for="point in item.points" :key="point">{{ point }}</li>
                </ul>
                <el-button text type="primary" @click.stop="item.action()">{{ item.actionText }}</el-button>
              </div>
            </article>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card class="content-card workflow-card" shadow="hover">
          <template #header>
            <div class="section-head">
              <div>
                <h2>推荐流程</h2>
                <p>从设计同步路径到观察运行结果，建议按这个顺序使用。</p>
              </div>
            </div>
          </template>
          <div class="workflow-list">
            <div v-for="step in workflowSteps" :key="step.order" class="workflow-item">
              <span class="workflow-order">{{ step.order }}</span>
              <div class="workflow-body">
                <h3>{{ step.title }}</h3>
                <p>{{ step.description }}</p>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="content-row">
      <el-col :xs="24">
        <el-card class="content-card" shadow="hover">
          <template #header>
            <div class="section-head">
              <div>
                <h2>近期关注任务</h2>
                <p>首页只保留少量焦点任务，帮助快速判断谁需要立即进入任务列表继续处理。</p>
              </div>
              <el-button text type="primary" @click="goToTaskList">查看完整任务列表</el-button>
            </div>
          </template>
          <div v-if="focusTasks.length" class="activity-list">
            <article v-for="item in focusTasks" :key="item.taskId" class="activity-item" @click="handleUpdate(item)">
              <div class="activity-main">
                <div class="activity-topline">
                  <strong>{{ item.taskName }}</strong>
                  <el-tag size="small" :type="statusTagType(item.status)">{{ statusLabel(item.status) }}</el-tag>
                </div>
                <p>{{ formatTargetTable(item) }}</p>
                <div class="activity-tags">
                  <el-tag size="small" effect="plain">{{ scheduleTypeLabel(item.scheduleType) }}</el-tag>
                  <el-tag size="small" effect="plain">{{ executorLabel(item.executorType) }}</el-tag>
                </div>
              </div>
              <div class="activity-side">
                <small>{{ item.owner || '未指定负责人' }}</small>
              </div>
            </article>
          </div>
          <el-empty v-else description="暂无同步任务" :image-size="68" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="DataIntegrationHome">
import { computed } from 'vue'
import { Connection, DataLine, Guide, Histogram, Promotion, SetUp } from '@element-plus/icons-vue'
import { useIntegrationPage } from './components/useIntegrationPage'
import { executorLabel, formatTargetTable, scheduleTypeLabel, statusLabel, statusTagType } from './components/taskViewMeta'

const {
  activeTaskCount,
  cronTaskCount,
  focusTasks,
  goToTaskList,
  handleAdd,
  handleUpdate,
  loading,
  sampleTaskCount,
  total,
} = useIntegrationPage('overview')

const overviewCards = computed(() => [
  {
    title: '同步任务总数',
    value: total.value,
    hint: '当前已配置的数据集成任务数量',
    icon: Guide,
    tone: 'tone-blue',
    action: goToTaskList,
  },
  {
    title: '首页焦点任务',
    value: sampleTaskCount.value,
    hint: '首页当前展示的重点样本任务数',
    icon: Histogram,
    tone: 'tone-green',
    action: goToTaskList,
  },
  {
    title: '样本内启用任务',
    value: activeTaskCount.value,
    hint: '用于快速判断当前需要关注的活跃任务密度',
    icon: Promotion,
    tone: 'tone-orange',
    action: goToTaskList,
  },
  {
    title: '样本内 Cron 任务',
    value: cronTaskCount.value,
    hint: '帮助判断当前自动同步节奏是否集中',
    icon: DataLine,
    tone: 'tone-violet',
    action: goToTaskList,
  },
])

const capabilities = [
  {
    title: '同步任务管理',
    description: '集中维护源数据源、目标表、装载策略和执行器，是数据集成的正式业务入口。',
    points: ['支持任务筛选与分页浏览', '支持执行、编辑、删除等高频动作', '支持从任务列表进入详情与运行视角'],
    actionText: '进入任务列表',
    action: goToTaskList,
    icon: SetUp,
  },
  {
    title: '路径设计与校验',
    description: '围绕源表到目标表的入仓路径，完成同步规则配置与保存前校验。',
    points: ['填写源库、源表与目标表信息', '定义全量/增量与写入模式', '保存前执行配置校验'],
    actionText: '新建同步任务',
    action: () => handleAdd(),
    icon: Connection,
  },
  {
    title: '运行结果回看',
    description: '任务运行时的信息统一从任务列表和详情进入，不再在首页混排执行工作台。',
    points: ['查看近期执行记录', '观察执行状态与结果摘要', '把运行排障留给任务工作面'],
    actionText: '查看任务工作面',
    action: goToTaskList,
    icon: Guide,
  },
]

const workflowSteps = [
  {
    order: '01',
    title: '确认同步范围',
    description: '先明确源数据源、源表和目标落地位置，避免先做执行再补配置。',
  },
  {
    order: '02',
    title: '配置同步策略',
    description: '在任务详情中定义装载类型、写入模式、执行器与调度方式。',
  },
  {
    order: '03',
    title: '进入任务列表执行',
    description: '把批量筛选、立即执行和详情查看统一放在任务列表工作面完成。',
  },
  {
    order: '04',
    title: '回看运行结果',
    description: '通过任务详情与执行记录确认同步结果，再决定是否继续调整配置。',
  },
]
</script>

<style scoped>
.hero-panel {
  border-radius: 8px;
  border: 1px solid #ebeef5;
  margin-bottom: 16px;
}

.hero-panel :deep(.el-card__body) {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.8fr);
  gap: 16px;
  padding: 20px 22px;
}

.hero-eyebrow {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: #ecf5ff;
  color: #409eff;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.hero-copy h1 {
  margin: 12px 0 10px;
  font-size: 28px;
  line-height: 1.35;
  font-weight: 600;
  color: #303133;
}

.highlight-label,
.metric-hint,
.section-head p,
.workflow-body p,
.activity-main p,
.activity-side small {
  color: #909399;
}

.hero-copy p,
.workflow-body p,
.activity-main p {
  margin: 0;
  line-height: 1.8;
  color: #606266;
}

.hero-actions,
.hero-tags,
.activity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.hero-actions {
  margin-top: 20px;
}

.hero-tags {
  margin-top: 14px;
}

.hero-highlight {
  display: flex;
  align-items: stretch;
}

.highlight-card {
  width: 100%;
  height: 100%;
  padding: 18px 20px;
  border-radius: 8px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
}

.highlight-card ul,
.capability-content ul {
  margin: 12px 0 0;
  padding-left: 18px;
  line-height: 1.65;
  color: #303133;
}

.metric-row,
.content-row {
  margin-top: 0;
  margin-bottom: 16px;
}

.metric-card,
.content-card {
  border-radius: 8px;
}

.metric-card {
  cursor: pointer;
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
  font-size: 20px;
  border-radius: 12px;
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

.tone-violet {
  color: #fff;
  background: linear-gradient(135deg, #909399, #b1b3b8);
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

.content-card :deep(.el-card__body) {
  padding: 18px 20px;
}

.content-card :deep(.el-card__header) {
  border-bottom: 1px solid #ebeef5;
  padding: 16px 20px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-head h2,
.capability-content h3,
.workflow-body h3 {
  margin: 0;
  color: #303133;
}

.section-head p {
  margin: 4px 0 0;
}

.capability-grid {
  display: grid;
  gap: 18px;
}

.capability-item {
  display: flex;
  gap: 14px;
  padding: 0 0 18px;
  border: none;
  border-bottom: 1px solid #ebeef5;
  background: transparent;
  cursor: pointer;
}

.capability-item:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.capability-icon {
  width: 52px;
  height: 52px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #ecf5ff;
  color: #409eff;
  font-size: 20px;
}

.capability-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.capability-content p {
  margin: 0;
  line-height: 1.65;
  color: #606266;
}

.capability-content ul {
  color: #606266;
  line-height: 1.65;
}

.workflow-list {
  display: grid;
  gap: 16px;
}

.workflow-item {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
  padding: 0 0 16px;
  border: none;
  border-bottom: 1px dashed #dcdfe6;
}

.workflow-item:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.workflow-order {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ecf5ff;
  color: #409eff;
  font-weight: 700;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
}

.activity-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.activity-topline {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.activity-side {
  align-items: flex-end;
  flex-shrink: 0;
}

@media (max-width: 992px) {
  .hero-panel :deep(.el-card__body) {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-copy h1 {
    font-size: 24px;
  }

  .hero-actions,
  .section-head,
  .activity-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
