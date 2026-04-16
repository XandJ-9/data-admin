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
            <div class="stat-value">{{ stats.tableTotal ?? '-' }}</div>
            <div class="stat-label">元数据表</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card card-col">
          <div class="stat-icon"><el-icon :size="32"><List /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.columnTotal ?? '-' }}</div>
            <div class="stat-label">元数据字段</div>
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
              <span>各数据源资产概览</span>
            </div>
          </template>
          <div ref="assetDistChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="Index">
import { Connection, Grid, List } from '@element-plus/icons-vue'
import { listDatasource } from '@/api/data/datasource'
import { listMetaTables, listMetaColumns } from '@/api/data/asset'
import * as echarts from 'echarts'

const stats = ref({})
const dsList = ref([])

const dsTypeChartRef = ref(null)
const assetDistChartRef = ref(null)

let dsTypeChart = null
let assetDistChart = null

function loadStats() {
  const p1 = listDatasource({ pageNum: 1, pageSize: 1 })
  const p2 = listMetaTables({ pageNum: 1, pageSize: 1 })
  const p3 = listMetaColumns({ pageNum: 1, pageSize: 1 })

  Promise.all([p1, p2, p3]).then(([r1, r2, r3]) => {
    stats.value = {
      dsTotal: r1.total ?? 0,
      tableTotal: r2.total ?? 0,
      columnTotal: r3.total ?? 0,
    }
  })
}

function loadDatasources() {
  listDatasource({ pageNum: 1, pageSize: 1000 }).then(res => {
    dsList.value = res.rows || []
    nextTick(() => {
      renderDsTypeChart()
      loadAssetDist()
    })
  })
}

function loadAssetDist() {
  if (!dsList.value.length) return
  const reqs = dsList.value.map(ds =>
    listMetaTables({ pageNum: 1, pageSize: 1, dataSourceId: ds.dataSourceId }).then(r => ({
      name: ds.dataSourceName,
      count: r.total ?? 0,
    }))
  )
  Promise.all(reqs).then(items => {
    const data = items.filter(item => item.count > 0).sort((left, right) => right.count - left.count)
    nextTick(() => renderAssetDistChart(data))
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

function renderAssetDistChart(data) {
  if (!assetDistChartRef.value) return
  if (!assetDistChart) assetDistChart = echarts.init(assetDistChartRef.value)

  assetDistChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 30, bottom: 20, left: 100 },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', data: data.map(item => item.name), inverse: true },
    series: [{
      type: 'bar',
      data: data.map(item => item.count),
      itemStyle: { color: '#409EFF' },
      label: { show: true, position: 'right' },
    }],
  })
}

function handleResize() {
  dsTypeChart?.resize()
  assetDistChart?.resize()
}

onMounted(() => {
  loadStats()
  loadDatasources()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  dsTypeChart?.dispose()
  assetDistChart?.dispose()
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

