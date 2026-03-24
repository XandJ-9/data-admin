<template>
  <div class="app-container dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card card-ds">
          <div class="stat-icon"><el-icon :size="32"><Connection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.dsTotal ?? '-' }}</div>
            <div class="stat-label">数据源</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card card-table">
          <div class="stat-icon"><el-icon :size="32"><Grid /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.tableTotal ?? '-' }}</div>
            <div class="stat-label">元数据表</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card card-col">
          <div class="stat-icon"><el-icon :size="32"><List /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.columnTotal ?? '-' }}</div>
            <div class="stat-label">元数据字段</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card card-etl">
          <div class="stat-icon"><el-icon :size="32"><DataLine /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.etlTotal ?? '-' }}</div>
            <div class="stat-label">ETL任务</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :sm="12">
        <el-card shadow="hover">
          <template #header><span>数据源类型分布</span></template>
          <div ref="dsTypeChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card shadow="hover">
          <template #header><span>ETL 任务执行状态</span></template>
          <div ref="etlStatusChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :sm="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>各数据源资产概览</span>
            </div>
          </template>
          <div ref="assetDistChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card shadow="hover">
          <template #header><span>ETL 任务类型分布</span></template>
          <div ref="etlTypeChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近执行记录 -->
    <el-card shadow="hover" class="recent-card">
      <template #header><span>最近 ETL 执行记录</span></template>
      <el-table :data="recentLogs" size="small" stripe :max-height="320">
        <el-table-column prop="taskName" label="任务名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="triggerType" label="触发方式" width="100" align="center">
          <template #default="{ row }">{{ triggerLabel(row.triggerType) }}</template>
        </el-table-column>
        <el-table-column prop="totalRows" label="处理行数" width="100" align="right">
          <template #default="{ row }">{{ row.totalRows ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="durationSeconds" label="耗时" width="90" align="right">
          <template #default="{ row }">{{ row.durationSeconds != null ? row.durationSeconds + 's' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="createTime" label="执行时间" width="170" align="center" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup name="Index">
import { Connection, Grid, List, DataLine } from '@element-plus/icons-vue'
import { listDatasource } from '@/api/data/datasource'
import { listMetaTables, listMetaColumns } from '@/api/data/asset'
import { listETLTask, listETLExecutionLog } from '@/api/data/etl'
import * as echarts from 'echarts'

const stats = ref({})
const recentLogs = ref([])
const dsList = ref([])
const etlList = ref([])

const dsTypeChartRef = ref(null)
const etlStatusChartRef = ref(null)
const assetDistChartRef = ref(null)
const etlTypeChartRef = ref(null)

let dsTypeChart = null
let etlStatusChart = null
let assetDistChart = null
let etlTypeChart = null

const statusMap = { pending: '等待', running: '执行中', success: '成功', failed: '失败', cancelled: '已取消' }
const statusTagMap = { pending: 'info', running: 'warning', success: 'success', failed: 'danger', cancelled: 'info' }
const triggerMap = { manual: '手动', schedule: '调度', api: 'API' }

function statusLabel(s) { return statusMap[s] || s }
function statusTagType(s) { return statusTagMap[s] || 'info' }
function triggerLabel(s) { return triggerMap[s] || s }

/** 加载统计卡片数据：复用已有 list 接口，pageSize=1 取 total */
function loadStats() {
  const p1 = listDatasource({ pageNum: 1, pageSize: 1 })
  const p2 = listMetaTables({ pageNum: 1, pageSize: 1 })
  const p3 = listMetaColumns({ pageNum: 1, pageSize: 1 })
  const p4 = listETLTask({ pageNum: 1, pageSize: 1 })

  Promise.all([p1, p2, p3, p4]).then(([r1, r2, r3, r4]) => {
    stats.value = {
      dsTotal: r1.total ?? 0,
      tableTotal: r2.total ?? 0,
      columnTotal: r3.total ?? 0,
      etlTotal: r4.total ?? 0,
    }
  })
}

/** 加载数据源列表用于饼图 */
function loadDatasources() {
  listDatasource({ pageNum: 1, pageSize: 1000 }).then(res => {
    dsList.value = res.rows || []
    nextTick(() => {
      renderDsTypeChart()
      loadAssetDist()
    })
  })
}

/** 加载 ETL 任务列表用于类型饼图 */
function loadEtlTasks() {
  listETLTask({ pageNum: 1, pageSize: 1000 }).then(res => {
    etlList.value = res.rows || []
    nextTick(() => renderEtlTypeChart())
  })
}

/** 加载执行日志：最近 10 条 + 状态饼图 */
function loadExecutionLogs() {
  // 最近 10 条
  listETLExecutionLog({ pageNum: 1, pageSize: 10 }).then(res => {
    recentLogs.value = res.rows || []
  })

  // 按状态统计：分别请求各状态的 total
  const statuses = ['success', 'failed', 'running', 'pending', 'cancelled']
  const reqs = statuses.map(s => listETLExecutionLog({ pageNum: 1, pageSize: 1, status: s }))
  Promise.all(reqs).then(results => {
    const statusData = []
    const colorMap = { pending: '#909399', running: '#E6A23C', success: '#67C23A', failed: '#F56C6C', cancelled: '#C0C4CC' }
    results.forEach((r, i) => {
      const count = r.total ?? 0
      if (count > 0) {
        statusData.push({ name: statusMap[statuses[i]], value: count, itemStyle: { color: colorMap[statuses[i]] } })
      }
    })
    nextTick(() => renderEtlStatusChart(statusData))
  })
}

/** 各数据源的元数据表数量 */
function loadAssetDist() {
  if (!dsList.value.length) return
  const reqs = dsList.value.map(ds =>
    listMetaTables({ pageNum: 1, pageSize: 1, dataSourceId: ds.dataSourceId }).then(r => ({
      name: ds.dataSourceName,
      count: r.total ?? 0,
    }))
  )
  Promise.all(reqs).then(items => {
    const data = items.filter(i => i.count > 0).sort((a, b) => b.count - a.count)
    nextTick(() => renderAssetDistChart(data))
  })
}

// ========== ECharts 渲染 ==========

function renderDsTypeChart() {
  if (!dsTypeChartRef.value) return
  if (!dsTypeChart) dsTypeChart = echarts.init(dsTypeChartRef.value)
  // 按 dbType 聚合
  const typeCount = {}
  dsList.value.forEach(ds => {
    typeCount[ds.dbType] = (typeCount[ds.dbType] || 0) + 1
  })
  const data = Object.entries(typeCount).map(([k, v]) => ({ name: k, value: v }))
  dsTypeChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
      label: { formatter: '{b}\n{c}' },
      data,
    }],
  })
}

function renderEtlStatusChart(statusData) {
  if (!etlStatusChartRef.value) return
  if (!etlStatusChart) etlStatusChart = echarts.init(etlStatusChartRef.value)
  etlStatusChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
      label: { formatter: '{b}\n{c}' },
      data: statusData,
    }],
  })
}

function renderAssetDistChart(data) {
  if (!assetDistChartRef.value || !data.length) return
  if (!assetDistChart) assetDistChart = echarts.init(assetDistChartRef.value)
  assetDistChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 30, bottom: 20, left: 100 },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', data: data.map(i => i.name), inverse: true },
    series: [{
      type: 'bar', data: data.map(i => i.count),
      itemStyle: { color: '#409EFF' },
      label: { show: true, position: 'right' },
    }],
  })
}

function renderEtlTypeChart() {
  if (!etlTypeChartRef.value) return
  if (!etlTypeChart) etlTypeChart = echarts.init(etlTypeChartRef.value)
  const typeMap = { extract: 'STG采集', transform: 'DWD转换', load: 'ODS加载', full: '全量ETL' }
  const typeCount = {}
  etlList.value.forEach(t => {
    const label = typeMap[t.etlType] || t.etlType
    typeCount[label] = (typeCount[label] || 0) + 1
  })
  const data = Object.entries(typeCount).map(([k, v]) => ({ name: k, value: v }))
  etlTypeChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
      label: { formatter: '{b}\n{c}' },
      data,
    }],
  })
}

// 窗口 resize
function handleResize() {
  dsTypeChart?.resize()
  etlStatusChart?.resize()
  assetDistChart?.resize()
  etlTypeChart?.resize()
}

onMounted(() => {
  loadStats()
  loadDatasources()
  loadEtlTasks()
  loadExecutionLogs()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  dsTypeChart?.dispose()
  etlStatusChart?.dispose()
  assetDistChart?.dispose()
  etlTypeChart?.dispose()
})
</script>

<style scoped lang="scss">
.dashboard {
  padding: 16px;

  .stat-row {
    margin-bottom: 16px;
  }

  .stat-card {
    display: flex;
    align-items: center;
    border-radius: 8px;
    cursor: default;

    :deep(.el-card__body) {
      display: flex;
      align-items: center;
      width: 100%;
      padding: 20px;
    }

    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      flex-shrink: 0;
    }

    .stat-info {
      margin-left: 16px;
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        line-height: 1.2;
        color: #303133;
      }
      .stat-label {
        font-size: 13px;
        color: #909399;
        margin-top: 4px;
      }
    }
  }

  .card-ds .stat-icon { background: linear-gradient(135deg, #409EFF, #66b1ff); }
  .card-table .stat-icon { background: linear-gradient(135deg, #67C23A, #85ce61); }
  .card-col .stat-icon { background: linear-gradient(135deg, #E6A23C, #ebb563); }
  .card-etl .stat-icon { background: linear-gradient(135deg, #F56C6C, #f78989); }

  .chart-row {
    margin-bottom: 16px;
  }

  .chart-container {
    width: 100%;
    height: 280px;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .recent-card {
    margin-bottom: 16px;
  }
}
</style>

