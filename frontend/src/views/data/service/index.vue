<template>
  <div class="app-container service-overview" v-loading="loading">
    <el-card shadow="hover" class="hero-panel">
      <div class="hero-copy">
        <span class="hero-eyebrow">数据服务</span>
        <h1>把临时查询、对外接口和执行审计放在同一个工作入口</h1>
        <p>
          数据服务用于连接现有数据源，快速执行 SQL 查询、沉淀可复用的数据接口，并通过查询日志追踪使用情况与执行结果。
        </p>
        <div class="hero-actions">
          <el-button type="primary" @click="goTo('/data-service/query')">开始 SQL 查询</el-button>
          <el-button plain type="primary" @click="goTo('/data-service/interface')">管理服务接口</el-button>
          <el-button text type="primary" @click="goTo('/data-service/query-log')">查看执行日志</el-button>
        </div>
        <div class="hero-tags">
          <el-tag size="small" type="primary" effect="light" round>临时分析查询</el-tag>
          <el-tag size="small" effect="plain" round>模板化接口发布</el-tag>
          <el-tag size="small" effect="plain" round>日志审计追踪</el-tag>
        </div>
      </div>
      <div class="hero-highlight">
        <div class="highlight-card">
          <span class="highlight-label">主要作用</span>
          <ul>
            <li>面向分析人员提供可直接执行的 SQL 查询能力</li>
            <li>面向业务系统沉淀标准化接口，减少重复造数</li>
            <li>面向运维与排障保留查询日志，便于追溯和审计</li>
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
                <h2>核心能力</h2>
                <p>告诉用户这个模块能做什么，以及应该从哪里开始。</p>
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
                <ul>
                  <li v-for="point in item.points" :key="point">{{ point }}</li>
                </ul>
                <el-button text type="primary" @click="goTo(item.path)">{{ item.action }}</el-button>
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
                <h2>使用流程</h2>
                <p>从探索数据到发布服务，建议按这个顺序使用。</p>
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
                <h2>接口定义概览</h2>
                <p>首页只保留接口信息，便于快速判断当前已沉淀了哪些服务接口。</p>
              </div>
              <el-button text type="primary" @click="goTo('/data-service/interface')">进入接口管理</el-button>
            </div>
          </template>
          <div v-if="recentInterfaces.length" class="interface-list">
            <article v-for="item in recentInterfaces" :key="item.interfaceId" class="interface-item">
              <div class="interface-main">
                <h3>{{ item.interfaceName }}</h3>
                <p>{{ item.interfaceCode || '未设置接口编码' }}</p>
              </div>
              <div class="interface-meta">
                <el-tag size="small" effect="plain">{{ item.interfaceDbType || '未知库型' }}</el-tag>
                <span>{{ item.platformName || '未设置业务平台' }}</span>
              </div>
            </article>
          </div>
          <el-empty v-else description="暂无接口定义" :image-size="68" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="DataService">
import { CircleCheck, Connection, Document, Files, Guide, Monitor, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listDatasource } from '@/api/data/datasource'
import { listInterfaceInfo, listQueryLog } from '@/api/data/service'

const router = useRouter()
const loading = ref(false)

const overview = reactive({
  dataSourceCount: 0,
  interfaceCount: 0,
  logCount: 0,
  successRate: '--',
})

const recentInterfaces = ref([])

const overviewCards = computed(() => [
  {
    title: '可用数据源',
    value: overview.dataSourceCount,
    hint: '用于执行查询和承载接口的数据连接数',
    icon: Connection,
    tone: 'tone-blue',
  },
  {
    title: '已定义接口',
    value: overview.interfaceCount,
    hint: '已经沉淀为可复用服务接口的定义数量',
    icon: Guide,
    tone: 'tone-green',
  },
  {
    title: '累计查询日志',
    value: overview.logCount,
    hint: '用于追踪执行历史、排障和审计的日志记录数',
    icon: Document,
    tone: 'tone-orange',
  },
  {
    title: '最近成功率',
    value: overview.successRate,
    hint: '基于最近 20 条查询记录计算，反映近期稳定性',
    icon: CircleCheck,
    tone: 'tone-violet',
  },
])

const capabilities = [
  {
    title: 'SQL 查询',
    description: '面向分析和排查场景，直接选择数据源执行 SQL，并支持导出结果。',
    points: ['支持按数据源即时查询', '支持结果导出与分页查看', '适合临时分析与验证 SQL'],
    action: '进入查询工作台',
    path: '/data-service/query',
    icon: Search,
  },
  {
    title: '接口管理',
    description: '把稳定的查询逻辑沉淀成对外接口，统一维护模板 SQL、字段和元数据。',
    points: ['维护接口编码与说明', '支持模板 SQL 与接口导入导出', '适合沉淀标准化服务能力'],
    action: '查看接口列表',
    path: '/data-service/interface',
    icon: Files,
  },
  {
    title: '查询日志',
    description: '记录查询人、执行状态和耗时，帮助你追踪使用情况与失败原因。',
    points: ['查看成功与失败记录', '追踪执行耗时', '适合审计、排障与稳定性观察'],
    action: '查看日志详情',
    path: '/data-service/query-log',
    icon: Monitor,
  },
]

const workflowSteps = [
  {
    order: '01',
    title: '选择数据源并验证 SQL',
    description: '先在 SQL 查询中快速验证语句和返回结果，确保逻辑正确。',
  },
  {
    order: '02',
    title: '整理为接口定义',
    description: '把稳定查询沉淀为接口，补齐接口编码、描述、字段和模板参数。',
  },
  {
    order: '03',
    title: '面向业务复用',
    description: '通过标准接口减少重复造数，让业务方或系统按统一口径取数。',
  },
  {
    order: '04',
    title: '回看日志与质量',
    description: '结合执行日志观察调用频率、成功率和耗时，持续优化稳定性。',
  },
]

function goTo(path) {
  router.push(path)
}

function resolveTotal(response) {
  if (typeof response?.total === 'number') return response.total
  if (Array.isArray(response?.rows)) return response.rows.length
  return 0
}

async function loadOverview() {
  loading.value = true
  try {
    const [dataSourceRes, interfaceRes, logRes] = await Promise.all([
      listDatasource({ pageNum: 1, pageSize: 1 }),
      listInterfaceInfo({ pageNum: 1, pageSize: 5 }),
      listQueryLog({ pageNum: 1, pageSize: 20 }),
    ])

    const logRows = logRes?.rows || []
    const successCount = logRows.filter(item => item.status === 'success').length

    overview.dataSourceCount = resolveTotal(dataSourceRes)
    overview.interfaceCount = resolveTotal(interfaceRes)
    overview.logCount = resolveTotal(logRes)
    overview.successRate = logRows.length ? `${Math.round((successCount / logRows.length) * 100)}%` : '--'

    recentInterfaces.value = (interfaceRes?.rows || []).slice(0, 5)
  } catch (error) {
    ElMessage.error(error?.msg || '加载数据服务概览失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadOverview()
})
</script>

<style scoped>
.service-overview {
  padding: 16px;
}

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

.hero-copy p {
  max-width: 760px;
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.highlight-card {
  height: 100%;
  padding: 18px 20px;
  border-radius: 8px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
}

.highlight-label {
  font-size: 13px;
  color: #909399;
}

.highlight-card ul {
  margin: 12px 0 0;
  padding-left: 18px;
  display: grid;
  gap: 10px;
  line-height: 1.65;
  color: #303133;
}

.metric-row,
.content-row {
  margin-top: 0;
  margin-bottom: 16px;
}

.metric-card {
  border-radius: 8px;
  cursor: default;
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
  border-radius: 12px;
  font-size: 24px;
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

.metric-hint {
  font-size: 12px;
  line-height: 1.5;
  color: #909399;
}

.content-card {
  border-radius: 8px;
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

.section-head h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #303133;
}

.section-head p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #909399;
}

.capability-grid {
  display: grid;
  gap: 18px;
}

.capability-item {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
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
  background: #eaf4ff;
  color: #409eff;
  font-size: 24px;
}

.capability-content h3,
.workflow-body h3,
.interface-main h3 {
  margin: 0;
  font-size: 15px;
  color: #303133;
}

.capability-content p,
.workflow-body p,
.activity-main p,
.interface-main p {
  margin: 6px 0 0;
  color: #606266;
  line-height: 1.65;
}

.capability-content ul {
  margin: 10px 0 0;
  padding-left: 18px;
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: #ecf5ff;
  color: #409eff;
  font-weight: 700;
}

.interface-list {
  display: grid;
  gap: 10px;
}

.interface-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
}

.interface-main {
  min-width: 0;
}

.interface-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  white-space: nowrap;
  color: #909399;
}

@media (max-width: 1200px) {
  .hero-panel :deep(.el-card__body) {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .service-overview {
    padding: 12px;
  }

  .hero-panel {
    margin-bottom: 12px;
  }

  .hero-copy h1 {
    font-size: 24px;
  }

  .section-head,
  .interface-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .interface-meta {
    align-items: flex-start;
  }
}
</style>
