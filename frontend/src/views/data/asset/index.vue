<template>
  <div class="data-asset-container">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content" @click="navigateTo('DataSourceManage')">
            <el-icon class="stats-icon" :size="40" color="#409EFF"><Management /></el-icon>
            <div class="stats-info">
              <div class="stats-number">{{ stats.datasourceCount }}</div>
              <div class="stats-label">数据源</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content" @click="navigateTo('DataAssetMetadata')">
            <el-icon class="stats-icon" :size="40" color="#67C23A"><Grid /></el-icon>
            <div class="stats-info">
              <div class="stats-number">{{ stats.tableCount }}</div>
              <div class="stats-label">元数据表</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content" @click="navigateTo('DataAssetMetadata')">
            <el-icon class="stats-icon" :size="40" color="#E6A23C"><List /></el-icon>
            <div class="stats-info">
              <div class="stats-number">{{ stats.columnCount }}</div>
              <div class="stats-label">元数据字段</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-content" @click="navigateTo('TableLineage')">
            <el-icon class="stats-icon" :size="40" color="#F56C6C"><Share /></el-icon>
            <div class="stats-info">
              <div class="stats-number">{{ stats.lineageCount }}</div>
              <div class="stats-label">血缘关系</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 功能导航卡片 -->
    <el-row :gutter="20" class="nav-row">
      <el-col :span="8">
        <el-card shadow="hover" class="nav-card" @click="navigateTo('datasource')">
          <div class="nav-header">
            <el-icon :size="32" color="#409EFF"><Management /></el-icon>
            <span class="nav-title">数据源管理</span>
          </div>
          <div class="nav-description">
            管理各类数据源连接，支持MySQL、PostgreSQL、Oracle等多种数据库
          </div>
          <div class="nav-features">
            <el-tag size="small" type="info">连接管理</el-tag>
            <el-tag size="small" type="info">连接测试</el-tag>
            <el-tag size="small" type="success">配置管理</el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="nav-card" @click="navigateTo('metadata')">
          <div class="nav-header">
            <el-icon :size="32" color="#67C23A"><Grid /></el-icon>
            <span class="nav-title">元数据浏览</span>
          </div>
          <div class="nav-description">
            浏览和搜索数据库表和字段元数据，支持表查找和字段查找两种模式
          </div>
          <div class="nav-features">
            <el-tag size="small" type="info">表查找</el-tag>
            <el-tag size="small" type="info">字段查找</el-tag>
            <el-tag size="small" type="success">元数据采集</el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="nav-card" @click="navigateTo('lineage')">
          <div class="nav-header">
            <el-icon :size="32" color="#F56C6C"><Share /></el-icon>
            <span class="nav-title">血缘管理</span>
          </div>
          <div class="nav-description">
            管理表级血缘关系，支持上游/下游查询和血缘关系图可视化
          </div>
          <div class="nav-features">
            <el-tag size="small" type="warning">新建功能</el-tag>
            <el-tag size="small" type="info">血缘配置</el-tag>
            <el-tag size="small" type="success">关系图</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="activity-card">
          <template #header>
            <div class="card-header">
              <span>最近采集活动</span>
              <el-button text @click="navigateTo('metadata')">查看全部</el-button>
            </div>
          </template>
          <el-empty v-if="recentActivities.length === 0" description="暂无采集活动" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="activity in recentActivities"
              :key="activity.id"
              :timestamp="activity.time"
              placement="top"
            >
              <el-card>
                <h4>{{ activity.title }}</h4>
                <p>{{ activity.description }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="DataAssetIndex">
import { listDatasource } from '@/api/data/datasource'
import {
  listMetaTables,
  listMetaColumns,
  listTableLineage
} from '@/api/data/asset'
import { DataBoard, Management } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const stats = ref({
  datasourceCount: 0,
  tableCount: 0,
  columnCount: 0,
  lineageCount: 0
})

const recentActivities = ref([])

// 加载统计数据
function loadStats() {
  // 数据源数量
  listDatasource({ pageNum: 1, pageSize: 1 }).then(response => {
    stats.value.datasourceCount = response.total
  })

  // 表数量
  listMetaTables({ pageNum: 1, pageSize: 1 }).then(response => {
    stats.value.tableCount = response.total
  })

  // 字段数量
  listMetaColumns({ pageNum: 1, pageSize: 1 }).then(response => {
    stats.value.columnCount = response.total
  })

  // 血缘关系数量
  listTableLineage({ pageNum: 1, pageSize: 1 }).then(response => {
    stats.value.lineageCount = response.total
  })
}

// 导航到指定页面
function navigateTo(page) {
  // 根据实际路由配置导航
  router.push({ name: `${page}` })
}

// 初始化
loadStats()
</script>

<style scoped lang="scss">
.data-asset-container {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stats-card {
  cursor: pointer;
  transition: transform 0.2s;

  &:hover {
    transform: translateY(-5px);
  }
}

.stats-content {
  display: flex;
  align-items: center;
  padding: 10px;
}

.stats-icon {
  margin-right: 20px;
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.nav-row {
  margin-bottom: 20px;
}

.nav-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  }
}

.nav-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.nav-title {
  font-size: 18px;
  font-weight: bold;
  margin-left: 10px;
}

.nav-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 15px;
  min-height: 48px;
}

.nav-features {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.activity-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
