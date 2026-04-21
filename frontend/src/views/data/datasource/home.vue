<template>
  <div class="app-container datasource-home" v-loading="loading">
    <el-card shadow="hover" class="hero-panel">
      <div class="hero-copy">
        <span class="hero-eyebrow">数据源管理</span>
        <h1>把连接配置、连通性验证和源数据发现放在统一入口</h1>
        <p>
          数据源管理处于平台第 1 步“破冰与连接”。这里负责维护数据库连接、判断是否可连通，
          并把用户引导到源数据浏览、元数据采集和后续数据集成链路。
        </p>
        <div class="hero-actions">
          <el-button type="primary" @click="goToList()">进入数据源列表</el-button>
          <el-button plain type="primary" @click="goToList('create')">新增数据源</el-button>
          <el-button text type="primary" @click="goToView">查看源数据</el-button>
        </div>
        <div class="hero-tags">
          <el-tag size="small" type="primary" effect="light" round>连接配置管理</el-tag>
          <el-tag size="small" effect="plain" round>连通性验证</el-tag>
          <el-tag size="small" effect="plain" round>源数据发现</el-tag>
        </div>
      </div>
      <div class="hero-highlight">
        <div class="highlight-card">
          <span class="highlight-label">首页定位</span>
          <ul>
            <li>先判断当前连接规模、可用性和待处理连接</li>
            <li>再进入列表维护连接信息，或进入源数据页浏览库表</li>
            <li>数据集成、建模加工和服务发布继续在后续模块完成</li>
          </ul>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="metric-row">
      <el-col v-for="item in overviewCards" :key="item.title" :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="metric-card" @click="item.action?.()">
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
                <p>明确这个模块回答什么问题，再进入对应页面继续操作。</p>
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
                <h2>推荐使用路径</h2>
                <p>从配置连接到进入后续模块，建议按这个顺序推进。</p>
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
                <h2>最近维护的数据源</h2>
                <p>帮助快速判断最近接入了哪些连接，以及是否已经完成连通性验证。</p>
              </div>
              <el-button text type="primary" @click="goToList()">查看全部</el-button>
            </div>
          </template>
          <div v-if="recentSources.length" class="activity-list">
            <article v-for="item in recentSources" :key="item.dataSourceId" class="activity-item">
              <div class="activity-main">
                <div class="activity-topline">
                  <strong>{{ item.dataSourceName }}</strong>
                  <div class="tag-stack">
                    <el-tag size="small" effect="plain">{{ item.dbType }}</el-tag>
                    <el-tag size="small" :type="item.status === '0' ? 'success' : 'danger'" effect="plain">{{ item.status === '0' ? '正常' : '停用' }}</el-tag>
                    <el-tag size="small" :type="connectivityTag(item.connectivityStatus)" effect="plain">{{ connectivityLabel(item.connectivityStatus) }}</el-tag>
                  </div>
                </div>
                <p>{{ item.dbName || '未填写数据库名' }}<span v-if="item.host"> · {{ item.host }}:{{ item.port }}</span></p>
                <small>{{ item.connectivityTestedAt || '尚未测试或配置已变更' }}</small>
              </div>
              <div class="activity-side">
                <el-button link type="primary" @click="openDetail(item)">详情</el-button>
              </div>
            </article>
          </div>
          <el-empty v-else description="暂无数据源" :image-size="68" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="DataSourceHome">
import { CircleCheck, Connection, DataAnalysis, Grid, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listDatasource } from '@/api/data/datasource'
import { listMetaTables } from '@/api/data/asset'

const router = useRouter()
const loading = ref(false)
const sourceRows = ref([])
const metaTableCount = ref(0)

const recentSources = computed(() => [...(sourceRows.value || [])].sort((left, right) => {
  const leftTime = new Date(left.updateTime || left.createTime || 0).getTime()
  const rightTime = new Date(right.updateTime || right.createTime || 0).getTime()
  return rightTime - leftTime
}).slice(0, 6))
const activeSourceCount = computed(() => sourceRows.value.filter(item => item.status === '0').length)
const connectedSourceCount = computed(() => sourceRows.value.filter(item => item.connectivityStatus === 'success').length)
const pendingSourceCount = computed(() => sourceRows.value.filter(item => item.connectivityStatus !== 'success').length)

const overviewCards = computed(() => [
  {
    title: '已接入数据源',
    value: sourceRows.value.length,
    hint: '当前已维护的数据库连接数量',
    icon: Connection,
    tone: 'tone-blue',
    action: () => goToList(),
  },
  {
    title: '正常状态连接',
    value: activeSourceCount.value,
    hint: '状态为正常，可继续参与后续链路的连接数',
    icon: CircleCheck,
    tone: 'tone-green',
    action: () => goToList(),
  },
  {
    title: '已通过连通性验证',
    value: connectedSourceCount.value,
    hint: '最近一次测试结果为成功的数据源数',
    icon: Promotion,
    tone: 'tone-orange',
    action: () => goToList(),
  },
  {
    title: '已纳入元数据表',
    value: metaTableCount.value,
    hint: pendingSourceCount.value ? `仍有 ${pendingSourceCount.value} 个连接待测试或异常` : '当前连接已完成基本验证',
    icon: Grid,
    tone: 'tone-violet',
    action: () => router.push({ name: 'DataAssetMetadata' }),
  },
])

const capabilities = [
  {
    title: '连接管理',
    description: '维护数据库类型、主机、账号和连接参数，是整个平台后续所有能力的起点。',
    points: ['统一维护连接信息', '支持新增、修改和停用', '支持从首页直达新建动作'],
    actionText: '进入数据源列表',
    action: () => goToList(),
    icon: Connection,
  },
  {
    title: '源数据发现',
    description: '直接浏览数据库、表和字段，并按库或表触发元数据采集，完成“发现”阶段。',
    points: ['查看库表结构', '触发整库或单表采集', '适合验证接入范围'],
    actionText: '进入源数据查看',
    action: () => goToView(),
    icon: DataAnalysis,
  },
  {
    title: '元数据衔接',
    description: '采集完成后进入元数据目录继续浏览和校验，再决定是否进入数据集成与服务模块。',
    points: ['查看采集结果', '确认字段结构和注释', '为后续集成与服务做准备'],
    actionText: '查看元数据目录',
    action: () => router.push({ name: 'DataAssetMetadata' }),
    icon: Grid,
  },
]

const workflowSteps = [
  {
    order: '01',
    title: '新增连接',
    description: '先维护数据库类型、主机、账号和连接参数，确保平台能访问到目标库。',
  },
  {
    order: '02',
    title: '测试连通性',
    description: '在列表页确认连接是否成功，把异常连接和未测试连接先处理干净。',
  },
  {
    order: '03',
    title: '浏览源数据',
    description: '进入源数据查看或详情页，确认有哪些库表可被浏览和采集。',
  },
  {
    order: '04',
    title: '进入后续链路',
    description: '元数据确认后再进入数据集成、数据服务或数据资产模块继续工作。',
  },
]

function connectivityLabel(status) {
  return { success: '已连通', failed: '异常', unknown: '未测试' }[status] || '未测试'
}

function connectivityTag(status) {
  return { success: 'success', failed: 'danger', unknown: 'info' }[status] || 'info'
}

function goToList(action = '') {
  const query = action ? { action } : undefined
  router.push({ name: 'DataSourceManage', query })
}

function goToView() {
  router.push({ name: 'DataSourceView' })
}

function openDetail(item) {
  if (!item?.dataSourceId) return
  router.push({ name: 'DataSourceDetail', params: { id: item.dataSourceId } })
}

function resolveRows(response) {
  return Array.isArray(response?.rows) ? response.rows : []
}

function resolveTotal(response) {
  if (typeof response?.total === 'number') return response.total
  return resolveRows(response).length
}

async function loadOverview() {
  loading.value = true
  try {
    const [sourceRes, tableRes] = await Promise.allSettled([
      listDatasource({ pageNum: 1, pageSize: 200 }),
      listMetaTables({ pageNum: 1, pageSize: 1 }),
    ])

    if (sourceRes.status !== 'fulfilled') {
      throw sourceRes.reason
    }

    sourceRows.value = resolveRows(sourceRes.value)
    metaTableCount.value = tableRes.status === 'fulfilled' ? resolveTotal(tableRes.value) : 0
  } catch (error) {
    sourceRows.value = []
    metaTableCount.value = 0
    ElMessage.error(error?.response?.data?.msg || error?.message || '加载数据源概览失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadOverview)
</script>

<style scoped>
.hero-panel,
.metric-card,
.content-card,
.highlight-card,
.capability-item {
  border-radius: 16px;
}

.hero-panel,
.metric-card,
.content-card {
  border: 1px solid #e5eaf3;
}

.hero-panel {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 16px;
}

:deep(.hero-panel .el-card__body) {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  width: 100%;
}

.hero-copy {
  flex: 1;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  background: #edf5ff;
  border-radius: 999px;
  font-size: 12px;
  color: #409eff;
  margin-bottom: 12px;
}

.hero-copy h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.3;
  color: #1f2d3d;
}

.hero-copy p {
  margin: 12px 0 0;
  color: #5b6b7b;
  line-height: 1.8;
}

.hero-actions,
.hero-tags,
.tag-stack {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hero-actions {
  margin-top: 18px;
}

.hero-tags {
  margin-top: 14px;
}

.hero-highlight {
  width: 320px;
  flex-shrink: 0;
}

.highlight-card {
  height: 100%;
  padding: 20px;
  background: linear-gradient(180deg, #f7faff 0%, #f3f7ff 100%);
}

.highlight-label {
  display: inline-block;
  margin-bottom: 12px;
  font-weight: 600;
  color: #303133;
}

.highlight-card ul,
.capability-content ul {
  margin: 0;
  padding-left: 18px;
  color: #5b6b7b;
  line-height: 1.8;
}

.metric-row,
.content-row {
  margin-bottom: 16px;
}

.metric-card {
  cursor: pointer;
}

:deep(.metric-card .el-card__body) {
  display: flex;
  align-items: center;
  gap: 14px;
}

.metric-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
}

.metric-body {
  display: flex;
  flex-direction: column;
}

.metric-label {
  font-size: 13px;
  color: #7b8794;
}

.metric-value {
  margin-top: 4px;
  font-size: 28px;
  line-height: 1.2;
  color: #1f2d3d;
}

.metric-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}

.tone-blue { background: linear-gradient(135deg, #409eff, #66b1ff); }
.tone-green { background: linear-gradient(135deg, #67c23a, #8ad35d); }
.tone-orange { background: linear-gradient(135deg, #e6a23c, #f3be62); }
.tone-violet { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }

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
  color: #1f2d3d;
}

.section-head p,
.capability-content p,
.workflow-body p,
.activity-main p,
.activity-main small {
  margin: 6px 0 0;
  color: #5b6b7b;
  line-height: 1.7;
}

.capability-grid {
  display: grid;
  gap: 14px;
}

.capability-item {
  display: flex;
  gap: 14px;
  padding: 16px;
  border: 1px solid #edf1f7;
  background: #fbfcff;
  cursor: pointer;
}

.capability-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #edf5ff;
  color: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.workflow-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.workflow-order {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: #edf5ff;
  color: #409eff;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid #eef2f7;
}

.activity-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.activity-topline {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.activity-main strong {
  color: #1f2d3d;
}

.activity-side {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

@media (max-width: 992px) {
  :deep(.hero-panel .el-card__body) {
    flex-direction: column;
  }

  .hero-highlight {
    width: 100%;
  }
}
</style>
