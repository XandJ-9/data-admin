<template>
  <div class="app-container datasource-home" v-loading="loading">
    <el-card shadow="hover" class="hero-panel">
      <div class="hero-copy">
        <span class="hero-eyebrow">数据源管理</span>
        <h1>先看连接状态，再进入维护与发现</h1>
        <p>
          数据源管理处于平台第 1 步“连接与发现”。首页只保留连接概览、当前关注和常用入口，
          帮助你快速判断下一步应该去哪里处理。
        </p>
        <div class="hero-actions">
          <el-button type="primary" @click="goToList()">进入数据源列表</el-button>
          <el-button plain type="primary" @click="goToList('create')">新增数据源</el-button>
          <el-button text type="primary" @click="goToView()">快捷查看源数据</el-button>
        </div>
        <div class="hero-insight-grid">
          <article v-for="item in heroInsights" :key="item.label" class="hero-insight-item">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.hint }}</small>
          </article>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="content-row">
      <el-col :xs="24">
        <el-card class="content-card" shadow="hover">
          <template #header>
            <div class="section-head">
              <div>
                <h2>{{ focusSectionTitle }}</h2>
                <p>{{ focusSectionDescription }}</p>
              </div>
            </div>
          </template>
          <div v-if="focusSources.length" class="focus-list">
            <article v-for="item in focusSources" :key="item.dataSourceId" class="focus-item">
              <div class="focus-main">
                <div class="focus-topline">
                  <strong>{{ item.dataSourceName }}</strong>
                  <div class="tag-stack">
                    <el-tag size="small" effect="plain">{{ item.dbType }}</el-tag>
                    <el-tag size="small" :type="item.status === '0' ? 'success' : 'danger'" effect="plain">
                      {{ item.status === '0' ? '正常' : '停用' }}
                    </el-tag>
                    <el-tag size="small" :type="connectivityTag(item.connectivityStatus)" effect="plain">
                      {{ connectivityLabel(item.connectivityStatus) }}
                    </el-tag>
                  </div>
                </div>
                <p>{{ item.dbName || '未填写数据库名' }}<span v-if="item.host"> · {{ item.host }}:{{ item.port }}</span></p>
                <small>{{ focusReason(item) }}</small>
              </div>
              <div class="focus-side">
                <el-button link type="primary" @click="openDetail(item)">查看详情</el-button>
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
import { ElMessage } from 'element-plus'
import { listDatasource } from '@/api/data/datasource'

const router = useRouter()
const loading = ref(false)
const sourceRows = ref([])

const recentSources = computed(() => [...(sourceRows.value || [])].sort((left, right) => {
  const leftTime = new Date(left.updateTime || left.createTime || 0).getTime()
  const rightTime = new Date(right.updateTime || right.createTime || 0).getTime()
  return rightTime - leftTime
}).slice(0, 5))
const connectedSourceCount = computed(() => sourceRows.value.filter(item => item.connectivityStatus === 'success').length)
const pendingSourceCount = computed(() => sourceRows.value.filter(item => item.connectivityStatus !== 'success').length)
const connectivityRate = computed(() => {
  if (!sourceRows.value.length) return '--'
  return `${Math.round((connectedSourceCount.value / sourceRows.value.length) * 100)}%`
})
const prioritySources = computed(() => [...sourceRows.value]
  .filter(item => item.status !== '0' || item.connectivityStatus !== 'success')
  .sort((left, right) => {
    const leftRank = left.connectivityStatus === 'failed' ? 0 : left.connectivityStatus === 'unknown' ? 1 : 2
    const rightRank = right.connectivityStatus === 'failed' ? 0 : right.connectivityStatus === 'unknown' ? 1 : 2
    if (leftRank !== rightRank) return leftRank - rightRank
    const leftTime = new Date(left.updateTime || left.createTime || 0).getTime()
    const rightTime = new Date(right.updateTime || right.createTime || 0).getTime()
    return rightTime - leftTime
  })
  .slice(0, 5))

const heroInsights = computed(() => [
  {
    label: '已接入连接',
    value: sourceRows.value.length,
    hint: '先看规模',
  },
  {
    label: '连通性通过率',
    value: connectivityRate.value,
    hint: '先看是否可用',
  },
  {
    label: '待处理连接',
    value: pendingSourceCount.value,
    hint: '异常或未测试',
  },
])

const focusSources = computed(() => (prioritySources.value.length ? prioritySources.value : recentSources.value))
const focusSectionTitle = computed(() => (prioritySources.value.length ? '当前优先处理' : '最近维护的数据源'))
const focusSectionDescription = computed(() => (
  prioritySources.value.length
    ? '把异常连接和未测试连接前置展示，先清掉阻塞项再进入下游动作。'
    : '当前没有明显阻塞项，首页只保留最近维护的连接帮助快速回看。'
))

function connectivityLabel(status) {
  return { success: '已连通', failed: '异常', unknown: '未测试' }[status] || '未测试'
}

function connectivityTag(status) {
  return { success: 'success', failed: 'danger', unknown: 'info' }[status] || 'info'
}

function focusReason(item) {
  if (item.connectivityStatus === 'failed') {
    return item.connectivityTestedAt
      ? `最近一次测试失败：${item.connectivityTestedAt}`
      : '连接测试失败，请优先检查主机、端口或账号信息'
  }
  if (item.connectivityStatus !== 'success') {
    return '尚未完成连通性测试，建议先验证后再继续后续流程'
  }
  return item.connectivityTestedAt || '最近有维护动作'
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

async function loadOverview() {
  loading.value = true
  try {
    const response = await listDatasource({ pageNum: 1, pageSize: 200 })
    sourceRows.value = resolveRows(response)
  } catch (error) {
    sourceRows.value = []
    ElMessage.error(error?.response?.data?.msg || error?.message || '加载数据源概览失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadOverview)
</script>

<style scoped>
.hero-panel,
.content-card {
  border-radius: 16px;
}

.hero-panel,
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
.tag-stack {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hero-actions {
  margin-top: 18px;
}

.hero-insight-grid {
  display: grid;
  gap: 12px;
}

.hero-insight-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 20px;
}

.hero-insight-item {
  padding: 14px 16px;
  border-radius: 14px;
  background: #f7faff;
  border: 1px solid #edf1f7;
}

.hero-insight-item span {
  display: block;
  font-size: 12px;
  color: #7b8794;
}

.hero-insight-item strong {
  display: block;
  margin-top: 6px;
  font-size: 24px;
  line-height: 1.2;
  color: #1f2d3d;
}

.hero-insight-item small {
  display: block;
  margin-top: 6px;
  line-height: 1.6;
  color: #5b6b7b;
}

.content-row {
  margin-bottom: 16px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-head h2 {
  margin: 0;
  color: #1f2d3d;
}

.section-head p,
.focus-main p,
.focus-main small {
  margin: 6px 0 0;
  color: #5b6b7b;
  line-height: 1.7;
}

.focus-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.focus-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border: 1px solid #edf1f7;
  border-radius: 14px;
  background: #fbfcff;
}

.focus-main {
  min-width: 0;
}

.focus-topline {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.focus-main strong {
  color: #1f2d3d;
}

.focus-side {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

@media (max-width: 992px) {
  .hero-insight-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .focus-item {
    flex-direction: column;
  }
}
</style>
