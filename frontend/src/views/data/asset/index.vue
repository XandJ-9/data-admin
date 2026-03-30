<template>
  <div class="data-asset-container">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="item in statCards" :key="item.key">
        <el-card shadow="hover" class="stats-card" @click="navigateTo(item.route)">
          <div class="stats-content">
            <div class="stats-icon-wrapper" :style="{ backgroundColor: item.bgColor }">
              <el-icon :size="28" color="#fff"><component :is="item.icon" /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ stats[item.key] }}</div>
              <div class="stats-label">{{ item.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 功能导航卡片 -->
    <el-row :gutter="16" class="nav-row">
      <el-col :xs="24" :sm="8" v-for="nav in navCards" :key="nav.route">
        <el-card shadow="hover" class="nav-card" @click="navigateTo(nav.route)">
          <div class="nav-header">
            <div class="nav-icon-wrapper" :style="{ backgroundColor: nav.bgColor }">
              <el-icon :size="24" color="#fff"><component :is="nav.icon" /></el-icon>
            </div>
            <span class="nav-title">{{ nav.title }}</span>
          </div>
          <div class="nav-description">{{ nav.description }}</div>
          <div class="nav-features">
            <el-tag v-for="tag in nav.tags" :key="tag.text" size="small" :type="tag.type" effect="plain">{{ tag.text }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近采集的表 -->
    <el-card class="recent-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">最近采集的表</span>
          <el-button text type="primary" @click="navigateTo('DataAssetMetadata')">查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentTables" v-loading="recentLoading" stripe size="small" style="width: 100%">
        <el-table-column prop="tableName" label="表名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="dataSourceName" label="数据源" width="140" show-overflow-tooltip />
        <el-table-column prop="databaseName" label="数据库" width="140" show-overflow-tooltip />
        <el-table-column prop="comment" label="描述" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.comment || '-' }}</template>
        </el-table-column>
        <el-table-column prop="createTime" label="采集时间" width="170" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup name="DataAssetIndex">
import { Management, Grid, List, Share } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { listDatasource } from '@/api/data/datasource'
import { listMetaTables, listMetaColumns, listTableLineage } from '@/api/data/asset'

const router = useRouter()

const stats = ref({
  datasourceCount: 0,
  tableCount: 0,
  columnCount: 0,
  lineageCount: 0,
})

const recentTables = ref([])
const recentLoading = ref(false)

const statCards = [
  { key: 'datasourceCount', label: '数据源', icon: 'Management', route: 'DataSourceManage', bgColor: '#409EFF' },
  { key: 'tableCount', label: '元数据表', icon: 'Grid', route: 'DataAssetMetadata', bgColor: '#67C23A' },
  { key: 'columnCount', label: '元数据字段', icon: 'List', route: 'DataAssetMetadata', bgColor: '#E6A23C' },
  { key: 'lineageCount', label: '血缘关系', icon: 'Share', route: 'TableLineage', bgColor: '#F56C6C' },
]

const navCards = [
  {
    route: 'DataSourceManage', icon: 'Management', bgColor: '#409EFF',
    title: '数据源管理',
    description: '管理各类数据源连接，支持 MySQL、PostgreSQL、StarRocks 等多种数据库',
    tags: [{ text: '连接管理', type: 'info' }, { text: '连接测试', type: 'info' }, { text: '配置管理', type: 'success' }],
  },
  {
    route: 'DataAssetMetadata', icon: 'Grid', bgColor: '#67C23A',
    title: '元数据浏览',
    description: '浏览和搜索数据库表和字段元数据，支持表查找和字段查找两种模式',
    tags: [{ text: '表查找', type: 'info' }, { text: '字段查找', type: 'info' }, { text: '元数据采集', type: 'success' }],
  },
  {
    route: 'TableLineage', icon: 'Share', bgColor: '#F56C6C',
    title: '血缘管理',
    description: '管理表级血缘关系，支持上游 / 下游查询和血缘关系图可视化',
    tags: [{ text: '血缘配置', type: 'info' }, { text: '关系图', type: 'success' }, { text: '上下游查询', type: 'warning' }],
  },
]

function loadStats() {
  Promise.allSettled([
    listDatasource({ pageNum: 1, pageSize: 1 }),
    listMetaTables({ pageNum: 1, pageSize: 1 }),
    listMetaColumns({ pageNum: 1, pageSize: 1 }),
    listTableLineage({ pageNum: 1, pageSize: 1 }),
  ]).then(([ds, tables, columns, lineage]) => {
    if (ds.status === 'fulfilled') stats.value.datasourceCount = ds.value.total || 0
    if (tables.status === 'fulfilled') stats.value.tableCount = tables.value.total || 0
    if (columns.status === 'fulfilled') stats.value.columnCount = columns.value.total || 0
    if (lineage.status === 'fulfilled') stats.value.lineageCount = lineage.value.total || 0
  })
}

function loadRecentTables() {
  recentLoading.value = true
  listMetaTables({ pageNum: 1, pageSize: 8, orderByColumn: 'create_time', isAsc: 'desc' })
    .then(res => {
      recentTables.value = res.rows || []
    })
    .finally(() => {
      recentLoading.value = false
    })
}

function navigateTo(name) {
  router.push({ name })
}

loadStats()
loadRecentTables()
</script>

<style scoped lang="scss">
.data-asset-container {
  padding: 20px;
}

.stats-row {
  margin-bottom: 16px;
}

.stats-card {
  cursor: pointer;
  transition: transform 0.25s, box-shadow 0.25s;
  border-radius: 8px;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  }
}

.stats-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 6px 0;
}

.stats-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stats-info {
  flex: 1;
  min-width: 0;
}

.stats-number {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stats-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.nav-row {
  margin-bottom: 16px;
}

.nav-card {
  cursor: pointer;
  transition: transform 0.25s, box-shadow 0.25s;
  border-radius: 8px;
  height: 100%;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  }
}

.nav-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.nav-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-title {
  font-size: 17px;
  font-weight: 600;
  color: #303133;
}

.nav-description {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 14px;
  min-height: 42px;
}

.nav-features {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.recent-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
</style>
