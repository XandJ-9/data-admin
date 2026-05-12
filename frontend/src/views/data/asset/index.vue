<template>
  <div class="app-container asset-overview" v-loading="loading">
    <el-card shadow="hover" class="hero-panel">
      <div class="hero-copy">
        <span class="hero-eyebrow">数据资产</span>
        <h1>把数据源、元数据目录和表级血缘收拢到统一资产入口</h1>
        <p>
          数据资产模块负责把“有什么数据、结构长什么样、上下游关系如何”讲清楚。
          首页只做资产视角总览，具体浏览、采集和血缘维护继续进入对应工作面。
        </p>
        <div class="hero-actions">
          <el-button type="primary" @click="navigateTo('DataAssetMetadata')">浏览元数据目录</el-button>
          <el-button plain type="primary" @click="navigateTo('DataSourceManage')">管理数据源</el-button>
          <el-button text type="primary" @click="navigateTo('TableLineage')">查看血缘关系</el-button>
        </div>
        <div class="hero-tags">
          <el-tag size="small" type="primary" effect="light" round>数据源连接管理</el-tag>
          <el-tag size="small" effect="plain" round>元数据目录浏览</el-tag>
          <el-tag size="small" effect="plain" round>表级血缘治理</el-tag>
        </div>
      </div>
      <div class="hero-highlight">
        <div class="highlight-card">
          <span class="highlight-label">首页定位</span>
          <ul>
            <li>先判断当前资产覆盖规模和采集活跃度</li>
            <li>再决定去数据源、元数据浏览还是血缘页面继续处理</li>
            <li>避免把资产首页做成堆叠表格和零散跳转入口</li>
          </ul>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="metric-row">
      <el-col v-for="item in overviewCards" :key="item.title" :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="metric-card" @click="navigateTo(item.route)">
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
                <p>先明确这个模块能解决什么问题，再进入对应页面操作。</p>
              </div>
            </div>
          </template>
          <div class="capability-grid">
            <article v-for="item in capabilities" :key="item.title" class="capability-item" @click="navigateTo(item.route)">
              <div class="capability-icon">
                <el-icon><component :is="item.icon" /></el-icon>
              </div>
              <div class="capability-content">
                <h3>{{ item.title }}</h3>
                <p>{{ item.description }}</p>
                <ul>
                  <li v-for="point in item.points" :key="point">{{ point }}</li>
                </ul>
                <el-button text type="primary" @click.stop="navigateTo(item.route)">{{ item.action }}</el-button>
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
                <p>从接入数据源到建立血缘，建议按这个顺序推进。</p>
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
                <h2>最近采集资产</h2>
                <p>帮助快速判断最近新增或更新了哪些表资产。</p>
              </div>
              <el-button text type="primary" @click="navigateTo('DataAssetMetadata')">查看全部</el-button>
            </div>
          </template>
          <div v-if="recentTables.length" class="activity-list">
            <article v-for="item in recentTables" :key="item.tableId || item.tableName + item.createTime" class="activity-item">
              <div class="activity-main">
                <div class="activity-topline">
                  <strong>{{ item.tableName }}</strong>
                  <el-tag size="small" effect="plain">{{ item.dataSourceName || '未知数据源' }}</el-tag>
                </div>
                <p>
                  {{ item.databaseName || '未知库' }}
                  <span v-if="item.comment">· {{ item.comment }}</span>
                </p>
              </div>
              <div class="activity-side">
                <small>{{ formatTime(item.createTime) }}</small>
              </div>
            </article>
          </div>
          <el-empty v-else description="暂无采集资产" :image-size="68" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="DataAssetIndex">
import { Connection, Grid, List, Management, Share } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { listDatasource } from '@/api/data/datasource'
import { listAssetColumns, listAssets, listTableLineage } from '@/api/data/asset'

const router = useRouter()
const loading = ref(false)

const stats = reactive({
  datasourceCount: 0,
  tableCount: 0,
  columnCount: 0,
  lineageCount: 0,
})

const recentTables = ref([])

function normalizeAssetTable(item) {
  return {
    ...item,
    assetId: item.id,
    tableId: item.legacyMetaTableId || item.id,
    tableName: item.objectName,
  }
}

const overviewCards = computed(() => [
  {
    title: '已接入数据源',
    value: stats.datasourceCount,
    hint: '用于采集、查询和服务编排的连接数',
    icon: Connection,
    tone: 'tone-blue',
    route: 'DataSourceManage',
  },
  {
    title: '表级资产',
    value: stats.tableCount,
    hint: '当前已纳入元数据目录的表资产数量',
    icon: Grid,
    tone: 'tone-green',
    route: 'DataAssetMetadata',
  },
  {
    title: '字段元数据',
    value: stats.columnCount,
    hint: '用于支撑字段检索和结构理解的字段量',
    icon: List,
    tone: 'tone-orange',
    route: 'DataAssetMetadata',
  },
  {
    title: '血缘关系',
    value: stats.lineageCount,
    hint: '当前已维护的表级上下游血缘关系数量',
    icon: Share,
    tone: 'tone-violet',
    route: 'TableLineage',
  },
])

const capabilities = [
  {
    title: '数据源管理',
    description: '负责维护各类数据库连接，是所有资产采集、查询和服务编排的基础入口。',
    points: ['统一维护连接信息', '支持连通性校验', '作为资产采集的起点'],
    action: '进入数据源管理',
    route: 'DataSourceManage',
    icon: Management,
  },
  {
    title: '元数据浏览',
    description: '面向表和字段维度统一浏览资产结构，帮助团队快速理解“库表长什么样”。',
    points: ['支持表级查找', '支持字段级检索', '支持查看采集结果'],
    action: '浏览元数据目录',
    route: 'DataAssetMetadata',
    icon: Grid,
  },
  {
    title: '血缘治理',
    description: '用于维护和查看表级上下游关系，辅助影响分析、口径回溯和问题排查。',
    points: ['维护表级血缘', '支持上下游关系查询', '支持关系图查看'],
    action: '进入血缘管理',
    route: 'TableLineage',
    icon: Share,
  },
]

const workflowSteps = [
  {
    order: '01',
    title: '接入数据源',
    description: '先维护可用连接，保证平台知道有哪些数据库和环境可被访问。',
  },
  {
    order: '02',
    title: '执行元数据采集',
    description: '把库表和字段结构同步进平台，形成可浏览的元数据目录。',
  },
  {
    order: '03',
    title: '浏览并校验资产',
    description: '在元数据目录里确认表和字段信息是否完整、命名是否合理。',
  },
  {
    order: '04',
    title: '补齐血缘关系',
    description: '针对关键表维护上游和下游关系，支撑分析和影响排查。',
  },
]

function resolveTotal(response) {
  if (typeof response?.total === 'number') return response.total
  if (Array.isArray(response?.rows)) return response.rows.length
  return 0
}

function navigateTo(name) {
  router.push({ name })
}

function formatTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function loadOverview() {
  loading.value = true
  try {
    const [dataSourceRes, tableRes, columnRes, lineageRes, recentRes] = await Promise.all([
      listDatasource({ pageNum: 1, pageSize: 1 }),
      listAssets({ pageNum: 1, pageSize: 1, assetType: 'table' }),
      listAssetColumns({ pageNum: 1, pageSize: 1 }),
      listTableLineage({ pageNum: 1, pageSize: 1 }),
      listAssets({ pageNum: 1, pageSize: 6, assetType: 'table' }),
    ])

    stats.datasourceCount = resolveTotal(dataSourceRes)
    stats.tableCount = resolveTotal(tableRes)
    stats.columnCount = resolveTotal(columnRes)
    stats.lineageCount = resolveTotal(lineageRes)
    recentTables.value = (recentRes?.rows || []).map(normalizeAssetTable)
  } catch (error) {
    ElMessage.error(error?.msg || '加载数据资产概览失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadOverview()
})
</script>

<style scoped>
.asset-overview {
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
  border-radius: 0;
  border: none;
  border-bottom: 1px solid #ebeef5;
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
  font-size: 24px;
  color: #409eff;
  background: #ecf5ff;
}

.capability-content h3,
.workflow-body h3,
.activity-topline strong,
.coverage-item strong {
  margin: 0;
  color: #303133;
}

.capability-content p,
.workflow-body p,
.activity-main p,
.coverage-item p {
  margin: 6px 0 0;
  color: #606266;
  line-height: 1.7;
  font-size: 13px;
}

.capability-content ul {
  margin: 10px 0 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
  color: #303133;
  line-height: 1.6;
  font-size: 13px;
}

.workflow-item {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  gap: 12px;
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
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
  background: #ecf5ff;
  font-weight: 600;
}

.activity-item,
.coverage-item {
  padding: 14px 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.activity-main,
.activity-side {
  display: flex;
  flex-direction: column;
  gap: 6px;
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

.activity-side small {
  color: #909399;
}

@media (max-width: 1200px) {
  .hero-panel :deep(.el-card__body) {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-actions,
  .section-head,
  .activity-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
