<template>
  <div class="app-container task-overview-page" v-loading="loading">
    <el-card shadow="hover" class="hero-card">
      <div class="hero-layout">
        <div class="hero-main">
          <span class="hero-eyebrow">任务运维中心</span>
          <h1>统一纳管数据集成任务和建模与加工任务</h1>
          <p>
            这个页面负责回答三件事：近一段时间运行是否稳定、当前纳管任务来自哪里、哪些任务需要立刻处理。
            数据集成与建模与加工继续共用统一 Task 中轴，配置、治理、执行记录和依赖维护则下沉到各自工作面。
          </p>
          <div class="hero-actions">
            <el-button type="primary" :icon="Plus" @click="handleCreateIntegrationTask" v-hasPermi="['dataintegration:task:add']">新建集成任务</el-button>
            <el-button :icon="EditPen" @click="goToDataDevelopment" v-hasPermi="['datadev:ide:view']">进入建模与加工</el-button>
            <el-button :icon="Histogram" @click="goToInstances" v-hasPermi="['datatask:instance:list']">查看执行记录</el-button>
            <el-button :icon="Share" @click="goToOrchestration" v-hasPermi="['datatask:dependency:query']">进入依赖编排</el-button>
            <el-button :icon="Refresh" @click="loadOverview">刷新总览</el-button>
          </div>
        </div>
        <div class="hero-side">
          <div class="control-card">
            <span class="control-label">观察周期</span>
            <el-radio-group v-model="activeWindowDays" size="default" class="window-switch">
              <el-radio-button v-for="item in periodOptions" :key="item.value" :value="item.value">{{ item.label }}</el-radio-button>
            </el-radio-group>
            <div class="control-meta">
              <div>
                <span>统计口径</span>
                <strong>{{ rangeText }}</strong>
              </div>
              <div>
                <span>最近刷新</span>
                <strong>{{ lastUpdatedText }}</strong>
              </div>
              <div>
                <span>纳管任务数</span>
                <strong>{{ filteredTasks.length }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <div class="metric-grid">
      <div v-for="item in overviewCards" :key="item.title">
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
      </div>
    </div>

    <el-card shadow="hover" class="content-card chart-card chart-card-large">
      <template #header>
        <div class="section-head">
          <div>
            <h2>执行趋势柱状图</h2>
            <p>按天观察当前观察周期内的成功、失败和未完成实例波动。</p>
          </div>
          <el-tag effect="plain">{{ rangeText }}</el-tag>
        </div>
      </template>
      <div v-if="canViewInstances" ref="trendChartRef" class="chart-canvas chart-canvas-large" />
      <el-empty v-else description="当前角色暂无执行记录查看权限" :image-size="68" />
    </el-card>

    <el-row :gutter="16" class="content-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="content-card chart-card pie-card">
          <template #header>
            <div class="section-head">
              <div>
                <h2>来源分布饼图</h2>
                <p>看当前纳管任务主要来自数据集成还是建模与加工。</p>
              </div>
            </div>
          </template>
          <div class="pie-panel">
            <div ref="sourcePieRef" class="chart-canvas pie-canvas" />
            <el-empty v-if="!filteredTasks.length" description="暂无任务数据" :image-size="56" class="chart-empty" />
          </div>
          <div class="pie-legend pie-legend-grid">
            <div v-for="item in sourceDistribution" :key="item.label" class="pie-legend-item">
              <span class="dot" :style="{ backgroundColor: item.color }" />
              <div>
                <strong>{{ item.label }}</strong>
                <small>{{ item.value }} 个 · {{ item.percent }}%</small>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="content-card chart-card pie-card">
          <template #header>
            <div class="section-head">
              <div>
                <h2>调度分布饼图</h2>
                <p>看任务是以手动、Cron 还是依赖方式运转。</p>
              </div>
            </div>
          </template>
          <div class="pie-panel">
            <div ref="schedulePieRef" class="chart-canvas pie-canvas" />
            <el-empty v-if="!filteredTasks.length" description="暂无任务数据" :image-size="56" class="chart-empty" />
          </div>
          <div class="pie-legend pie-legend-grid">
            <div v-for="item in scheduleDistribution" :key="item.label" class="pie-legend-item">
              <span class="dot" :style="{ backgroundColor: item.color }" />
              <div>
                <strong>{{ item.label }}</strong>
                <small>{{ item.value }} 个 · {{ item.percent }}%</small>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="content-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="content-card">
          <template #header>
            <div class="section-head">
              <div>
                <h2>异常看板</h2>
                <p>优先暴露最近失败、连续失败和超出观察周期未运行的任务。</p>
              </div>
              <el-button text type="primary" @click="goToInstances" v-hasPermi="['datatask:instance:list']">查看全部实例</el-button>
            </div>
          </template>

          <div class="alert-group">
            <el-empty v-if="!canViewInstances" description="当前角色暂无执行记录查看权限" :image-size="68" />
            <template v-else>
              <div class="alert-section">
                <div class="alert-title">最近失败</div>
                <el-empty v-if="!recentFailedTasks.length" description="最近没有失败任务" :image-size="56" />
                <div v-else class="alert-list">
                  <button
                    v-for="item in recentFailedTasks"
                    :key="`failed-${item.taskId}`"
                    type="button"
                    class="alert-item danger"
                    @click="openTaskDetail(item)"
                  >
                    <div>
                      <strong>{{ item.taskName }}</strong>
                      <span>{{ formatTime(item.instanceTime) }}</span>
                    </div>
                    <small>{{ item.errorMessage || '最近一次执行失败' }}</small>
                  </button>
                </div>
              </div>

              <div class="alert-section">
                <div class="alert-title">连续失败</div>
                <el-empty v-if="!consecutiveFailureTasks.length" description="暂无连续失败任务" :image-size="56" />
                <div v-else class="alert-list">
                  <button
                    v-for="item in consecutiveFailureTasks"
                    :key="`continuous-${item.taskId}`"
                    type="button"
                    class="alert-item warning"
                    @click="openTaskDetail(item)"
                  >
                    <div>
                      <strong>{{ item.taskName }}</strong>
                      <span>连续失败 {{ item.failureCount }} 次</span>
                    </div>
                    <small>{{ scheduleTypeLabel(item.scheduleType) }} · {{ sourceModuleLabel(item.sourceModule) }}</small>
                  </button>
                </div>
              </div>

              <div class="alert-section">
                <div class="alert-title">久未运行</div>
                <el-empty v-if="!staleTasks.length" description="没有超出观察周期未运行的任务" :image-size="56" />
                <div v-else class="alert-list">
                  <button
                    v-for="item in staleTasks"
                    :key="`stale-${item.taskId}`"
                    type="button"
                    class="alert-item neutral"
                    @click="openTaskDetail(item)"
                  >
                    <div>
                      <strong>{{ item.taskName }}</strong>
                      <span>{{ item.lastInstanceAt ? formatTime(item.lastInstanceAt) : '从未运行' }}</span>
                    </div>
                    <small>{{ statusLabel(item.status) }} · {{ sourceModuleLabel(item.sourceModule) }}</small>
                  </button>
                </div>
              </div>
            </template>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="content-card">
          <template #header>
            <div class="section-head">
              <div>
                <h2>最近动态</h2>
                <p>看最近哪些任务刚被触发、状态如何、耗时多久。</p>
              </div>
              <el-button text type="primary" @click="goToInstances" v-hasPermi="['datatask:instance:list']">进入执行记录</el-button>
            </div>
          </template>

          <el-empty v-if="!canViewInstances" description="当前角色暂无执行记录查看权限" :image-size="68" />
          <div v-else-if="recentActivities.length" class="activity-list">
            <article v-for="item in recentActivities" :key="item.taskInstanceId" class="activity-item">
              <div class="activity-main">
                <div class="activity-topline">
                  <strong>{{ item.taskName }}</strong>
                  <el-tag size="small" :type="executionStatusTag(item.status)">{{ executionStatusLabel(item.status) }}</el-tag>
                </div>
                <p>
                  {{ triggerModeLabel(item.triggerMode) }}
                  <span v-if="item.triggeredBy">· {{ item.triggeredBy }}</span>
                  <span v-if="item.executorType">· {{ item.executorType }}</span>
                </p>
              </div>
              <div class="activity-side">
                <span>{{ formatDuration(item.durationSeconds) }}</span>
                <small>{{ formatTime(getInstanceTime(item)) }}</small>
              </div>
            </article>
          </div>
          <el-empty v-else description="当前观察周期内暂无执行动态" :image-size="68" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="DataTaskIndex">
import { CircleCheck, Clock, EditPen, Histogram, Plus, Refresh, Share, Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useRouter } from 'vue-router'
import { listTaskInstances, listTasks } from '@/api/data/datatask'
import { checkPermi } from '@/utils/permission'
import {
  executionStatusLabel,
  executionStatusTag,
  scheduleTypeLabel,
  sourceModuleLabel,
  statusLabel,
} from './taskMeta'

const router = useRouter()
const loading = ref(false)
const allTasks = ref([])
const allInstances = ref([])
const lastUpdatedAt = ref(null)
const requestSerial = ref(0)
const canViewInstances = checkPermi(['datatask:instance:list'])
const periodOptions = [
  { label: '近 7 天', value: 7 },
  { label: '近 14 天', value: 14 },
  { label: '近 30 天', value: 30 },
]
const activeWindowDays = ref(7)

const trendChartRef = ref(null)
const sourcePieRef = ref(null)
const schedulePieRef = ref(null)

const filteredTasks = computed(() => allTasks.value)

const windowDateRange = computed(() => {
  const end = new Date()
  end.setHours(23, 59, 59, 999)
  const start = new Date(end)
  start.setDate(end.getDate() - activeWindowDays.value + 1)
  start.setHours(0, 0, 0, 0)
  return [start, end]
})

const filteredTaskIds = computed(() => new Set(filteredTasks.value.map(item => item.taskId)))

const filteredInstances = computed(() => {
  if (!canViewInstances) {
    return []
  }
  const [startDate, endDate] = windowDateRange.value
  return allInstances.value.filter(item => {
    if (!filteredTaskIds.value.has(item.taskId)) {
      return false
    }
    const instanceTime = parseDate(getInstanceTime(item))
    if (!instanceTime) {
      return false
    }
    return instanceTime >= startDate && instanceTime <= endDate
  })
})

const successInstanceCount = computed(() => filteredInstances.value.filter(item => item.status === 'success').length)
const failedInstanceCount = computed(() => filteredInstances.value.filter(item => item.status === 'failed').length)

const overviewCards = computed(() => [
  {
    title: '任务总量',
    value: filteredTasks.value.length,
    hint: '任务运维当前纳管的数据集成与建模加工任务规模',
    icon: Histogram,
    tone: 'tone-blue',
  },
  {
    title: '启用任务',
    value: filteredTasks.value.filter(item => item.status === 'active').length,
    hint: '当前仍处于启用态，可继续调度的任务数',
    icon: CircleCheck,
    tone: 'tone-green',
  },
  {
    title: `近 ${activeWindowDays.value} 天执行`,
    value: canViewInstances ? filteredInstances.value.length : '--',
    hint: canViewInstances ? '观察周期内产生的任务实例总数' : '当前角色暂无执行记录查看权限',
    icon: Clock,
    tone: 'tone-cyan',
  },
  {
    title: '周期成功率',
    value: canViewInstances && filteredInstances.value.length
      ? `${Math.round((successInstanceCount.value / filteredInstances.value.length) * 100)}%`
      : '--',
    hint: canViewInstances ? '观察周期内任务实例的成功占比' : '当前角色暂无执行记录查看权限',
    icon: CircleCheck,
    tone: 'tone-violet',
  },
  {
    title: '失败实例',
    value: canViewInstances ? failedInstanceCount.value : '--',
    hint: canViewInstances ? '观察周期内执行失败的任务实例数' : '当前角色暂无执行记录查看权限',
    icon: Warning,
    tone: 'tone-red',
  },
])

const rangeText = computed(() => {
  const [startDate, endDate] = windowDateRange.value
  return `${formatDateValue(startDate)} 至 ${formatDateValue(endDate)}`
})

const lastUpdatedText = computed(() => {
  if (!lastUpdatedAt.value) {
    return '--'
  }
  return formatTime(lastUpdatedAt.value, true)
})

const sourceDistribution = computed(() => buildDistribution(
  [
    { label: '数据集成', value: filteredTasks.value.filter(item => item.sourceModule === 'dataintegration.task').length, color: '#67C23A' },
    { label: '建模与加工', value: filteredTasks.value.filter(item => item.sourceModule === 'datadev.script').length, color: '#E6A23C' },
    { label: '源数据采集', value: filteredTasks.value.filter(item => item.sourceModule === 'datasource.collection').length, color: '#409EFF' },
    { label: '未归类', value: filteredTasks.value.filter(item => !item.sourceModule).length, color: '#909399' },
  ],
  filteredTasks.value.length,
))

const scheduleDistribution = computed(() => buildDistribution(
  [
    { label: '手动触发', value: filteredTasks.value.filter(item => item.scheduleType === 'manual').length, color: '#409EFF' },
    { label: 'Cron 调度', value: filteredTasks.value.filter(item => item.scheduleType === 'cron').length, color: '#67C23A' },
    { label: '依赖触发', value: filteredTasks.value.filter(item => item.scheduleType === 'dependency').length, color: '#E6A23C' },
  ],
  filteredTasks.value.length,
))

const recentActivities = computed(() => {
  return [...filteredInstances.value]
    .sort((left, right) => parseDate(getInstanceTime(right)) - parseDate(getInstanceTime(left)))
    .slice(0, 10)
})

const taskMap = computed(() => new Map(filteredTasks.value.map(item => [item.taskId, item])))

const recentFailedTasks = computed(() => {
  const latestFailureByTask = new Map()
  filteredInstances.value
    .filter(item => item.status === 'failed')
    .sort((left, right) => parseDate(getInstanceTime(right)) - parseDate(getInstanceTime(left)))
    .forEach(item => {
      if (!latestFailureByTask.has(item.taskId) && taskMap.value.has(item.taskId)) {
        latestFailureByTask.set(item.taskId, {
          ...taskMap.value.get(item.taskId),
          instanceTime: getInstanceTime(item),
          errorMessage: item.errorMessage,
        })
      }
    })
  return Array.from(latestFailureByTask.values()).slice(0, 5)
})

const consecutiveFailureTasks = computed(() => {
  const instancesByTask = new Map()
  filteredInstances.value.forEach(item => {
    if (!instancesByTask.has(item.taskId)) {
      instancesByTask.set(item.taskId, [])
    }
    instancesByTask.get(item.taskId).push(item)
  })
  return Array.from(instancesByTask.entries())
    .map(([taskId, rows]) => {
      const sortedRows = [...rows].sort((left, right) => parseDate(getInstanceTime(right)) - parseDate(getInstanceTime(left)))
      let failureCount = 0
      for (const row of sortedRows) {
        if (row.status === 'failed') {
          failureCount += 1
        } else {
          break
        }
      }
      if (failureCount < 2 || !taskMap.value.has(taskId)) {
        return null
      }
      return {
        ...taskMap.value.get(taskId),
        failureCount,
      }
    })
    .filter(Boolean)
    .sort((left, right) => right.failureCount - left.failureCount)
    .slice(0, 5)
})

const staleTasks = computed(() => {
  const [staleThreshold] = windowDateRange.value
  return filteredTasks.value
    .filter(item => item.status === 'active')
    .filter(item => {
      const lastRun = parseDate(item.lastInstanceAt)
      return !lastRun || lastRun < staleThreshold
    })
    .sort((left, right) => {
      const leftTime = parseDate(left.lastInstanceAt)
      const rightTime = parseDate(right.lastInstanceAt)
      if (!leftTime && !rightTime) return 0
      if (!leftTime) return -1
      if (!rightTime) return 1
      return leftTime - rightTime
    })
    .slice(0, 5)
})

let trendChart = null
let sourcePieChart = null
let schedulePieChart = null
let chartResizeObserver = null

function formatDateValue(date) {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function parseDate(value) {
  if (!value) return null
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value
  }
  const normalizedValue = typeof value === 'string' ? value.replace(' ', 'T') : value
  const date = new Date(normalizedValue)
  return Number.isNaN(date.getTime()) ? null : date
}

function getInstanceTime(item) {
  return item.finishedAt || item.startedAt || item.createTime || item.scheduledAt
}

function formatTime(value, includeYear = false) {
  const date = parseDate(value)
  if (!date) return value || '--'
  return date.toLocaleString('zh-CN', {
    ...(includeYear ? { year: 'numeric' } : {}),
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDuration(value) {
  if (value === undefined || value === null || value === '') {
    return '--'
  }
  return `${value}s`
}

function triggerModeLabel(value) {
  if (value === 'manual') return '手动触发'
  if (value === 'schedule') return '定时触发'
  if (value === 'dependency') return '依赖触发'
  return value || '未知触发'
}

function buildDistribution(items, total) {
  return items.map(item => ({
    ...item,
    percent: total ? Math.round((item.value / total) * 100) : 0,
  }))
}

function buildPieOption(data) {
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}<br/>{c} 个（{d}%）',
    },
    legend: { show: false },
    series: [
      {
        type: 'pie',
        radius: ['46%', '72%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        label: { show: false },
        emphasis: {
          scale: true,
          label: {
            show: true,
            formatter: '{b}\n{d}%',
            fontWeight: 600,
          },
        },
        data: data.map(item => ({
          value: item.value,
          name: item.label,
          itemStyle: { color: item.color },
        })),
      },
    ],
  }
}

function buildTrendOption() {
  const [startDate, endDate] = windowDateRange.value
  const days = []
  const cursor = new Date(startDate)
  while (cursor <= endDate) {
    days.push(formatDateValue(cursor))
    cursor.setDate(cursor.getDate() + 1)
  }

  const dayBuckets = new Map(days.map(day => [day, { success: 0, failed: 0, unfinished: 0 }]))
  filteredInstances.value.forEach(item => {
    const instanceTime = parseDate(getInstanceTime(item))
    if (!instanceTime) return
    const dayKey = formatDateValue(instanceTime)
    const bucket = dayBuckets.get(dayKey)
    if (!bucket) return
    if (item.status === 'success') {
      bucket.success += 1
    } else if (item.status === 'failed') {
      bucket.failed += 1
    } else {
      bucket.unfinished += 1
    }
  })

  return {
    tooltip: { trigger: 'axis' },
    legend: {
      top: 0,
      data: ['成功', '失败', '未完成'],
    },
    grid: { top: 40, left: 12, right: 12, bottom: 12, containLabel: true },
    xAxis: {
      type: 'category',
      data: days.map(item => item.slice(5)),
      axisTick: { alignWithLabel: true },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
    },
    series: [
      {
        name: '成功',
        type: 'bar',
        stack: 'total',
        barMaxWidth: 26,
        itemStyle: { color: '#67C23A', borderRadius: [6, 6, 0, 0] },
        data: days.map(day => dayBuckets.get(day).success),
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        barMaxWidth: 26,
        itemStyle: { color: '#F56C6C', borderRadius: [6, 6, 0, 0] },
        data: days.map(day => dayBuckets.get(day).failed),
      },
      {
        name: '未完成',
        type: 'bar',
        stack: 'total',
        barMaxWidth: 26,
        itemStyle: { color: '#E6A23C', borderRadius: [6, 6, 0, 0] },
        data: days.map(day => dayBuckets.get(day).unfinished),
      },
    ],
  }
}

function ensureChart(targetRef, chartRef) {
  if (!targetRef.value) return null
  if (!chartRef) {
    return echarts.init(targetRef.value)
  }
  return chartRef
}

function renderCharts() {
  if (canViewInstances && trendChartRef.value) {
    trendChart = ensureChart(trendChartRef, trendChart)
    trendChart?.setOption(buildTrendOption())
    trendChart?.resize()
  }
  if (sourcePieRef.value && filteredTasks.value.length) {
    sourcePieChart = ensureChart(sourcePieRef, sourcePieChart)
    sourcePieChart?.setOption(buildPieOption(sourceDistribution.value))
    sourcePieChart?.resize()
  }
  if (schedulePieRef.value && filteredTasks.value.length) {
    schedulePieChart = ensureChart(schedulePieRef, schedulePieChart)
    schedulePieChart?.setOption(buildPieOption(scheduleDistribution.value))
    schedulePieChart?.resize()
  }
  setupChartResizeObserver()
}

async function loadAllRows(loader, baseQuery = {}) {
  const rows = []
  let pageNum = 1
  const pageSize = 100
  let total = 0

  while (pageNum === 1 || rows.length < total) {
    const response = await loader({
      ...baseQuery,
      pageNum,
      pageSize,
    })
    const pageRows = response.rows || []
    total = response.total || pageRows.length
    rows.push(...pageRows)
    if (!pageRows.length || pageRows.length < pageSize) {
      break
    }
    pageNum += 1
  }
  return rows
}

async function loadRecentTaskInstances(startDate) {
  const rows = []
  let pageNum = 1
  const pageSize = 100

  while (true) {
    const response = await listTaskInstances({ pageNum, pageSize })
    const pageRows = response.rows || []
    if (!pageRows.length) {
      break
    }
    rows.push(...pageRows.filter(item => {
      const instanceTime = parseDate(getInstanceTime(item))
      return instanceTime && instanceTime >= startDate
    }))
    if (pageRows.length < pageSize) {
      break
    }
    const oldestPageTime = parseDate(getInstanceTime(pageRows[pageRows.length - 1]))
    if (oldestPageTime && oldestPageTime < startDate) {
      break
    }
    pageNum += 1
  }

  return rows
}

function getErrorMessage(error, fallback = '加载任务总览失败') {
  return error?.response?.data?.msg || error?.response?.data?.message || error?.message || fallback
}

function notifyError(error, fallback = '加载任务总览失败') {
  if (error?.__handled) {
    return
  }
  ElMessage.error(getErrorMessage(error, fallback))
}

async function loadOverview() {
  const currentRequestId = requestSerial.value + 1
  requestSerial.value = currentRequestId
  loading.value = true
  try {
    const [windowStartDate] = windowDateRange.value
    const [taskRows, instanceRows] = await Promise.all([
      loadAllRows(listTasks),
      canViewInstances ? loadRecentTaskInstances(windowStartDate) : Promise.resolve([]),
    ])
    if (currentRequestId !== requestSerial.value) {
      return
    }
    allTasks.value = taskRows
    allInstances.value = instanceRows
    lastUpdatedAt.value = new Date()
    await nextTick()
    renderCharts()
  } catch (error) {
    if (currentRequestId !== requestSerial.value) {
      return
    }
    allTasks.value = []
    allInstances.value = []
    notifyError(error)
  } finally {
    if (currentRequestId === requestSerial.value) {
      loading.value = false
    }
  }
}

function handleCreateIntegrationTask() {
  router.push({ name: 'DataIntegrationTaskCreate', query: { from: 'task-center' } })
}

function goToDataDevelopment() {
  router.push({ name: 'DataDevHome' })
}

function goToInstances() {
  router.push({ name: 'DataTaskInstances' })
}

function goToOrchestration() {
  router.push({ name: 'DataTaskDependency' })
}

function openTaskDetail(task) {
  router.push({ name: 'DataTaskDetail', params: { id: task.taskId } })
}

function handleResize() {
  trendChart?.resize()
  sourcePieChart?.resize()
  schedulePieChart?.resize()
}

function setupChartResizeObserver() {
  if (chartResizeObserver || typeof ResizeObserver === 'undefined') {
    return
  }
  chartResizeObserver = new ResizeObserver(() => {
    handleResize()
  })
  ;[trendChartRef.value, sourcePieRef.value, schedulePieRef.value]
    .filter(Boolean)
    .forEach(element => chartResizeObserver.observe(element))
}

watch(
  [filteredTasks, filteredInstances],
  async () => {
    await nextTick()
    renderCharts()
  },
  { deep: true }
)

watch(activeWindowDays, () => {
  loadOverview()
})

onMounted(() => {
  loadOverview()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartResizeObserver?.disconnect()
  chartResizeObserver = null
  trendChart?.dispose()
  sourcePieChart?.dispose()
  schedulePieChart?.dispose()
})
</script>

<style scoped>
.task-overview-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
}

.hero-card,
.metric-card,
.content-card {
  border-radius: 8px;
}

.hero-card {
  border: 1px solid #ebeef5;
}

.hero-card :deep(.el-card__body) {
  padding: 20px 22px;
}

.hero-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(320px, 0.85fr);
  gap: 16px;
  align-items: stretch;
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

.hero-main h1 {
  margin: 12px 0 10px;
  font-size: 28px;
  line-height: 1.35;
  font-weight: 600;
  color: #303133;
}

.hero-main p,
.section-head p,
.metric-hint,
.activity-main p,
.activity-side small,
.alert-item span,
.alert-item small,
.control-label,
.control-meta span,
.pie-legend-item small {
  color: var(--el-text-color-secondary);
}

.hero-main p,
.section-head p {
  margin: 0;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.control-card {
  height: 100%;
  padding: 18px 20px;
  border-radius: 8px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.window-switch {
  width: fit-content;
}

.control-meta {
  display: grid;
  gap: 12px;
}

.control-meta div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.control-meta strong {
  color: var(--el-text-color-primary);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
}

.metric-card :deep(.el-card__body) {
  display: flex;
  gap: 14px;
  align-items: center;
  min-height: 112px;
  padding: 18px 20px;
}

.metric-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
  flex-shrink: 0;
}

.tone-blue { background: linear-gradient(135deg, #409eff, #66b1ff); }
.tone-green { background: linear-gradient(135deg, #67c23a, #85ce61); }
.tone-cyan { background: linear-gradient(135deg, #36cfc9, #5cdbd3); }
.tone-violet { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }
.tone-red { background: linear-gradient(135deg, #f56c6c, #f78989); }

.metric-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.metric-value {
  font-size: 26px;
  line-height: 1;
}

.content-row {
  margin: 0 !important;
}

.chart-card-large {
  height: 100%;
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
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.section-head h2 {
  margin: 0 0 6px;
  font-size: 18px;
}

.chart-canvas {
  width: 100%;
}

.chart-canvas-large {
  height: 420px;
}

.pie-card {
  height: 100%;
}

.pie-canvas {
  height: 340px;
}

.pie-panel {
  position: relative;
}

.chart-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(1px);
}

.pie-legend {
  display: grid;
  gap: 10px;
}

.pie-legend-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 8px;
}

.pie-legend-item {
  display: flex;
  gap: 10px;
  align-items: center;
}

.pie-legend-item .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.pie-legend-item strong {
  display: block;
  margin-bottom: 2px;
}

.alert-group {
  display: grid;
  gap: 20px;
}

.alert-title {
  margin: 0 0 12px;
  font-size: 15px;
}

.alert-list,
.activity-list {
  display: grid;
  gap: 0;
}

.alert-item {
  display: grid;
  gap: 6px;
  padding: 14px 0 14px 14px;
  border-radius: 0;
  border: none;
  border-bottom: 1px solid var(--el-border-color-light);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-item div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.alert-item.danger {
  box-shadow: inset 3px 0 0 #f56c6c;
}

.alert-item.warning {
  box-shadow: inset 3px 0 0 #e6a23c;
}

.alert-item.neutral {
  box-shadow: inset 3px 0 0 #909399;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 14px;
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

@media (max-width: 1280px) {
  .hero-layout {
    grid-template-columns: 1fr;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .section-head,
  .activity-item,
  .alert-item div,
  .control-meta div {
    flex-direction: column;
    align-items: flex-start;
  }

  .chart-canvas-large {
    height: 280px;
  }

  .pie-canvas {
    height: 280px;
  }

  .pie-legend-grid {
    grid-template-columns: 1fr;
  }
}
</style>
