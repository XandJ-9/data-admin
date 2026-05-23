<template>
  <div class="app-container integration-overview" v-loading="loading">
    <el-card shadow="hover" class="hero-panel">
      <div class="hero-copy">
        <span class="hero-eyebrow">数据集成</span>
        <h1>把同步任务入口和当前规模讲清楚，具体维护交给任务列表</h1>
        <p>
          首页保留模块定位、关键指标和常用入口。任务筛选、字段配置、执行记录和详情维护，
          统一进入任务列表或任务详情页处理。
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
            <li>看同步任务整体规模和入口</li>
            <li>进入列表完成筛选、执行和编辑</li>
            <li>进入详情维护源端、目标端和策略配置</li>
          </ul>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="metric-row">
      <el-col v-for="item in overviewCards" :key="item.title" :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="metric-card">
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
                <h2>职责边界</h2>
                <p>说明数据集成模块负责什么，具体操作入口保留在顶部。</p>
              </div>
            </div>
          </template>
          <div class="capability-grid">
            <article v-for="item in capabilities" :key="item.title" class="capability-item">
              <div class="capability-icon">
                <el-icon><component :is="item.icon" /></el-icon>
              </div>
              <div class="capability-content">
                <h3>{{ item.title }}</h3>
                <p>{{ item.description }}</p>
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
                <h2>处理顺序</h2>
                <p>把具体配置和运行排障留在专门页面。</p>
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
  </div>
</template>

<script setup name="DataIntegrationHome">
import { computed } from 'vue'
import { Connection, DataLine, Guide, Histogram, Promotion, SetUp } from '@element-plus/icons-vue'
import { useIntegrationPage } from './components/useIntegrationPage'

const {
  activeTaskCount,
  cronTaskCount,
  goToTaskList,
  handleAdd,
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
  },
  {
    title: '首页样本任务',
    value: sampleTaskCount.value,
    hint: '首页仅加载少量任务用于估算状态',
    icon: Histogram,
    tone: 'tone-green',
  },
  {
    title: '样本内启用任务',
    value: activeTaskCount.value,
    hint: '完整状态分布请进入任务列表查看',
    icon: Promotion,
    tone: 'tone-orange',
  },
  {
    title: '样本内 Cron 任务',
    value: cronTaskCount.value,
    hint: '完整调度配置在任务详情中维护',
    icon: DataLine,
    tone: 'tone-violet',
  },
])

const capabilities = [
  {
    title: '同步任务定义',
    description: '维护贴源入仓任务的业务配置，不在首页展开任务明细。',
    icon: SetUp,
  },
  {
    title: '路径设计与校验',
    description: '围绕源端、目标端和同步策略形成稳定配置，保存前做必要校验。',
    icon: Connection,
  },
  {
    title: '运行结果回看',
    description: '执行记录、结果摘要和排障信息统一下沉到任务列表与详情页。',
    icon: Guide,
  },
]

const workflowSteps = [
  {
    order: '01',
    title: '新建或选择任务',
    description: '从首页入口进入创建页，或到任务列表选择已有任务。',
  },
  {
    order: '02',
    title: '维护同步配置',
    description: '在详情页维护源端、目标端、装载方式和调度配置。',
  },
  {
    order: '03',
    title: '执行与回看',
    description: '在任务列表触发执行，并进入详情或执行记录查看结果。',
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
.workflow-body p {
  color: #909399;
}

.hero-copy p,
.workflow-body p {
  margin: 0;
  line-height: 1.8;
  color: #606266;
}

.hero-actions,
.hero-tags {
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

.highlight-card ul {
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
  flex-shrink: 0;
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
  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
