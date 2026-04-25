<template>
  <div class="app-container dashboard">
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card card-ds">
          <div class="stat-icon"><el-icon :size="32"><Connection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.dsTotal ?? '-' }}</div>
            <div class="stat-label">数据源</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card card-table">
          <div class="stat-icon"><el-icon :size="32"><Grid /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.connectedTotal ?? '-' }}</div>
            <div class="stat-label">已连通数据源</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card card-col">
          <div class="stat-icon"><el-icon :size="32"><List /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.pendingTotal ?? '-' }}</div>
            <div class="stat-label">待处理连接</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :sm="12">
        <el-card shadow="hover">
          <template #header><span>数据源类型分布</span></template>
          <div ref="dsTypeChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>连接状态分布</span>
            </div>
          </template>
          <div ref="connectivityChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="Index">
import { Connection, Grid, List } from '@element-plus/icons-vue'
import { listDatasource } from '@/api/data/datasource'
import * as echarts from 'echarts'

const stats = ref({})
const dsList = ref([])

const dsTypeChartRef = ref(null)
const connectivityChartRef = ref(null)

let dsTypeChart = null
let connectivityChart = null

function loadStats() {
  listDatasource({ pageNum: 1, pageSize: 1000 }).then(response => {
    const rows = response.rows || []
    stats.value = {
      dsTotal: rows.length,
      connectedTotal: rows.filter(item => item.connectivityStatus === 'success').length,
      pendingTotal: rows.filter(item => item.connectivityStatus !== 'success').length,
    }
  })
}

function loadDatasources() {
  listDatasource({ pageNum: 1, pageSize: 1000 }).then(res => {
    dsList.value = res.rows || []
    nextTick(() => {
      renderDsTypeChart()
      renderConnectivityChart()
    })
  })
}

function renderDsTypeChart() {
  if (!dsTypeChartRef.value) return
  if (!dsTypeChart) dsTypeChart = echarts.init(dsTypeChartRef.value)

  const typeCount = {}
  dsList.value.forEach(ds => {
    typeCount[ds.dbType] = (typeCount[ds.dbType] || 0) + 1
  })

  const data = Object.entries(typeCount).map(([name, value]) => ({ name, value }))
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

function renderConnectivityChart() {
  if (!connectivityChartRef.value) return
  if (!connectivityChart) connectivityChart = echarts.init(connectivityChartRef.value)

  const statusCount = { success: 0, failed: 0, unknown: 0 }
  dsList.value.forEach(ds => {
    const key = ds.connectivityStatus || 'unknown'
    statusCount[key] = (statusCount[key] || 0) + 1
  })

  connectivityChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '45%'],
      label: { formatter: '{b}\n{c}' },
      data: [
        { name: '已连通', value: statusCount.success || 0 },
        { name: '连接异常', value: statusCount.failed || 0 },
        { name: '未测试', value: statusCount.unknown || 0 },
      ],
    }],
  })
}

function handleResize() {
  dsTypeChart?.resize()
  connectivityChart?.resize()
}

onMounted(() => {
  loadStats()
  loadDatasources()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  dsTypeChart?.dispose()
  connectivityChart?.dispose()
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
}
</style>
