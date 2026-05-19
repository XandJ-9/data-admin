<template>
  <div class="app-container dev-overview" v-loading="loading">
    <el-card shadow="hover" class="hero-panel">
      <div class="hero-copy">
        <span class="hero-eyebrow">数据开发</span>
        <h1>把模型设计、加工作业和发布运行放在一个清晰的开发入口</h1>
        <p>
          数据开发处于平台第 3 步“建模与加工”。首页只负责看清开发资产规模、近期关注作业和下一步入口，
          具体 SQL / Python 编写、模型字段维护与运行治理继续进入对应工作面完成。
        </p>
        <div class="hero-actions">
          <el-button type="primary" @click="goToJobs()">进入加工作业</el-button>
          <el-button plain type="primary" @click="goToModeling">管理数据模型</el-button>
          <el-button text type="primary" @click="goToTaskOps">查看任务运维</el-button>
        </div>
        <div class="hero-tags">
          <el-tag size="small" type="primary" effect="light" round>模型先行</el-tag>
          <el-tag size="small" effect="plain" round>SQL / Python 加工</el-tag>
          <el-tag size="small" effect="plain" round>发布后统一纳管</el-tag>
        </div>
      </div>
      <div class="hero-highlight">
        <div class="highlight-card">
          <span class="highlight-label">首页定位</span>
          <ul>
            <li>先看模型和加工作业的当前规模</li>
            <li>再进入模型设计或加工作业继续维护</li>
            <li>运行、调度和依赖治理统一交给任务运维</li>
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
                <p>帮助用户先理解数据开发在平台中的职责，再进入具体工作面处理。</p>
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
                <p>从设计模型到发布作业，建议按这个顺序推进。</p>
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
                <h2>近期关注作业</h2>
                <p>首页只保留少量加工作业，帮助快速判断谁需要继续编辑、发布或回看运行情况。</p>
              </div>
              <el-button text type="primary" @click="goToJobs()">查看完整作业列表</el-button>
            </div>
          </template>
          <div v-if="recentScripts.length" class="activity-list">
            <article v-for="item in recentScripts" :key="item.scriptId" class="activity-item" @click="openScript(item)">
              <div class="activity-main">
                <div class="activity-topline">
                  <strong>{{ item.scriptName }}</strong>
                  <el-tag size="small" :type="statusTagType(item.status)" effect="plain">{{ statusLabel(item.status) }}</el-tag>
                  <el-tag size="small" effect="plain">{{ scriptTypeLabel(item.scriptType) }}</el-tag>
                </div>
                <p>{{ item.targetModelName || '未绑定目标模型' }}<span v-if="item.targetLayer"> · {{ item.targetLayer }}</span></p>
                <div class="activity-tags">
                  <el-tag size="small" effect="plain">{{ roleLabel(item.scriptRole) }}</el-tag>
                  <el-tag size="small" effect="plain">{{ engineLabel(item.engineType) }}</el-tag>
                  <el-tag v-if="item.taskId" size="small" type="success" effect="plain">已纳管</el-tag>
                </div>
              </div>
              <div class="activity-side">
                <small>{{ item.owner || '未指定负责人' }}</small>
              </div>
            </article>
          </div>
          <el-empty v-else description="暂无加工作业" :image-size="68" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { Collection, DataAnalysis, Document, Finished, Guide, SetUp } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listExecutions, listModels, listScripts } from '@/api/data/datadev'

defineOptions({ name: 'DataDevHome' })

const router = useRouter()
const loading = ref(false)
const recentScripts = ref([])

const overview = reactive({
  scriptCount: 0,
  modelCount: 0,
  publishedScriptCount: 0,
  successRate: '--',
})

const overviewCards = computed(() => [
  {
    title: '加工作业总数',
    value: overview.scriptCount,
    hint: '当前已维护的 SQL / Python 作业数量',
    icon: Document,
    tone: 'tone-blue',
    action: () => goToJobs(),
  },
  {
    title: '数据模型总数',
    value: overview.modelCount,
    hint: '用于承接加工结果的目标模型数量',
    icon: Collection,
    tone: 'tone-green',
    action: goToModeling,
  },
  {
    title: '已发布作业',
    value: overview.publishedScriptCount,
    hint: '已经进入发布态、可继续纳管运行的作业',
    icon: Finished,
    tone: 'tone-orange',
    action: () => goToJobs(),
  },
  {
    title: '最近成功率',
    value: overview.successRate,
    hint: '基于最近 20 条执行记录计算，反映近期稳定性',
    icon: DataAnalysis,
    tone: 'tone-violet',
    action: goToTaskOps,
  },
])

const capabilities = [
  {
    title: '模型设计',
    description: '先维护层级、目标表、字段注释和负责人，让加工结果有明确承接对象。',
    points: ['维护 ODS/DWD/DWS/ADS 层级', '定义目标表和字段结构', '从模型直接创建加工作业'],
    actionText: '进入模型设计',
    action: goToModeling,
    icon: Collection,
  },
  {
    title: '加工作业',
    description: '围绕模型编写 SQL / Python 作业，完成调试、版本发布和任务纳管前准备。',
    points: ['支持 SQL 与 Python 作业', '支持绑定目标模型', '支持调试执行与版本发布'],
    actionText: '查看加工作业',
    action: () => goToJobs(),
    icon: SetUp,
  },
  {
    title: '任务运维衔接',
    description: '开发态定义确认后发布到统一任务中心，运行实例、调度和依赖由任务运维承接。',
    points: ['发布后进入统一 Task', '执行记录进入 TaskInstance', 'Cron 与依赖编排不放在开发首页'],
    actionText: '进入任务运维',
    action: goToTaskOps,
    icon: Guide,
  },
]

const workflowSteps = [
  {
    order: '01',
    title: '先定义目标模型',
    description: '明确层级、目标表、字段和负责人，避免作业先跑起来再补治理信息。',
  },
  {
    order: '02',
    title: '再编写加工作业',
    description: '在加工作业中绑定模型，编写 SQL / Python 逻辑并完成基础调试。',
  },
  {
    order: '03',
    title: '发布稳定版本',
    description: '把确认后的作业版本发布出来，形成后续运行可以消费的开发事实。',
  },
  {
    order: '04',
    title: '交给任务运维纳管',
    description: '调度、依赖、实例状态和异常排查统一进入任务运维，不在首页重复承载。',
  },
]

function resolveTotal(response) {
  if (typeof response?.total === 'number') return response.total
  if (Array.isArray(response?.rows)) return response.rows.length
  if (Array.isArray(response?.data)) return response.data.length
  return 0
}

function resolveRows(response) {
  if (Array.isArray(response?.rows)) return response.rows
  if (Array.isArray(response?.data)) return response.data
  return []
}

function resolveSettled(result) {
  return result.status === 'fulfilled' ? result.value : null
}

function statusLabel(status) {
  return { draft: '草稿', published: '已发布', archived: '已归档' }[status] || '未知'
}

function statusTagType(status) {
  return { draft: 'info', published: 'success', archived: 'warning' }[status] || 'info'
}

function scriptTypeLabel(type) {
  return { sql: 'SQL', python: 'Python' }[type] || type || '未知类型'
}

function roleLabel(role) {
  return {
    explore: '探索分析',
    transform: '模型加工',
    quality: '质量校验',
    backfill: '数据回刷',
    python_job: 'Python 作业',
  }[role] || '未设置用途'
}

function engineLabel(engine) {
  return { spark: 'Spark SQL', hive: 'Hive', mvp: 'MVP' }[engine] || engine || '未设置引擎'
}

function goToJobs(quickCreate = '') {
  const query = quickCreate ? { quickCreate } : undefined
  router.push({ path: '/datadev/ide', query })
}

function goToModeling() {
  router.push('/datadev/modeling')
}

function goToTaskOps() {
  router.push('/datatask')
}

function openScript(item) {
  if (!item?.scriptId) return
  router.push(`/datadev/ide/detail/${item.scriptId}`)
}

async function loadOverview() {
  loading.value = true
  try {
    const results = await Promise.allSettled([
      listScripts({ pageNum: 1, pageSize: 6 }),
      listModels({ pageNum: 1, pageSize: 1 }),
      listScripts({ pageNum: 1, pageSize: 1, status: 'published' }),
      listExecutions({ pageNum: 1, pageSize: 20 }),
    ])

    const [scriptRes, modelRes, publishedRes, executionRes] = results.map(resolveSettled)
    const hasFailedRequest = results.some(item => item.status === 'rejected')

    const executionRows = resolveRows(executionRes)
    const successCount = executionRows.filter(item => item.status === 'success').length

    overview.scriptCount = resolveTotal(scriptRes)
    overview.modelCount = resolveTotal(modelRes)
    overview.publishedScriptCount = resolveTotal(publishedRes)
    overview.successRate = executionRows.length ? `${Math.round((successCount / executionRows.length) * 100)}%` : '--'
    recentScripts.value = resolveRows(scriptRes).slice(0, 6)

    if (hasFailedRequest) {
      ElMessage.warning('部分数据开发概览加载失败，已展示可用数据')
    }
  } catch (error) {
    recentScripts.value = []
    ElMessage.error(error?.msg || error?.response?.data?.msg || error?.message || '加载数据开发概览失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(loadOverview)
</script>

<style scoped>
.dev-overview {
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

.hero-actions,
.hero-tags,
.activity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hero-actions {
  margin-top: 20px;
}

.hero-tags {
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
.workflow-body h3,
.activity-topline strong {
  margin: 0;
  color: #303133;
}

.section-head h2 {
  font-size: 17px;
  font-weight: 600;
}

.section-head p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #909399;
}

.capability-grid,
.workflow-list,
.activity-list {
  display: grid;
  gap: 12px;
}

.capability-item {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
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
  color: #409eff;
  background: #ecf5ff;
  font-size: 24px;
}

.capability-content p,
.workflow-body p,
.activity-main p {
  margin: 6px 0 0;
  color: #606266;
  line-height: 1.7;
  font-size: 13px;
}

.capability-content ul {
  display: grid;
  gap: 6px;
  color: #303133;
  font-size: 13px;
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
  min-width: 0;
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
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
}

.activity-side small {
  color: #909399;
}

@media (max-width: 1200px) {
  .hero-panel :deep(.el-card__body) {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dev-overview {
    padding: 12px;
  }

  .hero-copy h1 {
    font-size: 24px;
  }

  .hero-actions,
  .section-head,
  .activity-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .activity-side {
    align-items: flex-start;
  }
}
</style>
