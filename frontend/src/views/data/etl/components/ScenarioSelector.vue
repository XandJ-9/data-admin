<template>
  <div class="scenario-selector">
    <div class="page-header">
      <h2>选择数据同步场景</h2>
      <p class="subtitle">请选择符合您需求的数据集成场景，我们将引导您完成配置</p>
    </div>

    <div class="scenario-grid">
      <!-- 场景1: 业务库 → STG -->
      <el-card
        class="scenario-card"
        :class="{ selected: modelValue === 'biz_to_stg' }"
        @click="selectScenario('biz_to_stg')"
        shadow="hover"
      >
        <div class="card-icon">
          <el-icon :size="32"><Coin /></el-icon>
          <el-icon :size="24" class="arrow-icon"><Right /></el-icon>
          <el-icon :size="32"><FolderOpened /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-title">业务库 → STG层</div>
          <div class="card-desc">
            将业务系统数据库的数据同步到数仓STG缓冲层，适合首次数据接入或全量初始化
          </div>
          <div class="card-features">
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>自动创建日期分区</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>支持数据预览</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>智能字段映射</span>
            </div>
          </div>
          <div class="card-tags">
            <el-tag size="small" type="success">推荐新手</el-tag>
            <el-tag size="small">全量同步</el-tag>
          </div>
        </div>
      </el-card>

      <!-- 场景2: STG → ODS -->
      <el-card
        class="scenario-card"
        :class="{ selected: modelValue === 'stg_to_ods' }"
        @click="selectScenario('stg_to_ods')"
        shadow="hover"
      >
        <div class="card-icon">
          <el-icon :size="32"><FolderOpened /></el-icon>
          <el-icon :size="24" class="arrow-icon"><Right /></el-icon>
          <el-icon :size="32"><Document /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-title">STG层 → ODS层</div>
          <div class="card-desc">
            对STG层数据进行清洗、去重、格式转换等标准化处理后同步到ODS原始层
          </div>
          <div class="card-features">
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>数据质量检查</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>自动去重逻辑</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>增量更新支持</span>
            </div>
          </div>
          <div class="card-tags">
            <el-tag size="small" type="warning">数据标准化</el-tag>
            <el-tag size="small">增量同步</el-tag>
          </div>
        </div>
      </el-card>

      <!-- 场景3: 数仓层计算 -->
      <el-card
        class="scenario-card"
        :class="{ selected: modelValue === 'warehouse_transform' }"
        @click="selectScenario('warehouse_transform')"
        shadow="hover"
      >
        <div class="card-icon">
          <el-icon :size="32"><TrendCharts /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-title">数仓层计算转换</div>
          <div class="card-desc">
            在DWD/DWS/ADS层使用Spark SQL进行复杂的数据聚合、计算、关联和转换
          </div>
          <div class="card-features">
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>Spark SQL强大算力</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>支持复杂SQL</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>参数化查询</span>
            </div>
          </div>
          <div class="card-tags">
            <el-tag size="small" type="danger">高级用户</el-tag>
            <el-tag size="small">SQL开发</el-tag>
          </div>
        </div>
      </el-card>

      <!-- 场景4: 数仓 → 业务库 -->
      <el-card
        class="scenario-card"
        :class="{ selected: modelValue === 'warehouse_to_biz' }"
        @click="selectScenario('warehouse_to_biz')"
        shadow="hover"
      >
        <div class="card-icon">
          <el-icon :size="32"><TrendCharts /></el-icon>
          <el-icon :size="24" class="arrow-icon"><Right /></el-icon>
          <el-icon :size="32"><Coin /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-title">数仓层 → 业务库</div>
          <div class="card-desc">
            将数仓计算好的结果数据推送到业务数据库，支持报表、BI、业务系统等应用场景
          </div>
          <div class="card-features">
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>定时批量推送</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>覆盖或追加模式</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>性能优化</span>
            </div>
          </div>
          <div class="card-tags">
            <el-tag size="small" type="info">结果导出</el-tag>
            <el-tag size="small">定时推送</el-tag>
          </div>
        </div>
      </el-card>

      <!-- 场景5: 数据库互相同步 -->
      <el-card
        class="scenario-card"
        :class="{ selected: modelValue === 'db_to_db' }"
        @click="selectScenario('db_to_db')"
        shadow="hover"
      >
        <div class="card-icon">
          <el-icon :size="32"><Coin /></el-icon>
          <el-icon :size="24" class="arrow-icon"><Refresh /></el-icon>
          <el-icon :size="32"><Coin /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-title">数据库互相同步</div>
          <div class="card-desc">
            在不同数据库之间同步数据，支持MySQL、PostgreSQL、Oracle等异构数据库
          </div>
          <div class="card-features">
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>异构数据库支持</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>在线数据迁移</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><Check /></el-icon>
              <span>增量实时同步</span>
            </div>
          </div>
          <div class="card-tags">
            <el-tag size="small" type="primary">灵活配置</el-tag>
            <el-tag size="small">数据迁移</el-tag>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 底部操作提示 -->
    <div class="footer-tip">
      <el-alert
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <div class="tip-content">
            <div class="tip-title">💡 选择提示</div>
            <ul class="tip-list">
              <li>首次接入数据：选择【业务库 → STG层】</li>
              <li>数据清洗标准化：选择【STG层 → ODS层】</li>
              <li>复杂计算聚合：选择【数仓层计算转换】</li>
              <li>数据推送到业务：选择【数仓层 → 业务库】</li>
              <li>数据库迁移：选择【数据库互相同步】</li>
            </ul>
          </div>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { Coin, FolderOpened, Document, TrendCharts, Right, Check, Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'select'])

function selectScenario(scenario) {
  emit('update:modelValue', scenario)
  emit('select', scenario)
}
</script>

<style scoped>
.scenario-selector {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h2 {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
}

.subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.scenario-card {
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.scenario-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.scenario-card.selected {
  border-color: #409EFF;
  background-color: #f0f7ff;
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
  color: #409EFF;
}

.arrow-icon {
  color: #909399;
}

.card-content {
  text-align: left;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.card-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 16px;
  min-height: 48px;
}

.card-features {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

.card-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.footer-tip {
  margin-top: 40px;
}

.tip-content {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.tip-title {
  font-weight: 600;
  color: #409EFF;
  white-space: nowrap;
}

.tip-list {
  margin: 0;
  padding-left: 20px;
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.tip-list li {
  color: #606266;
  font-size: 13px;
  line-height: 1.8;
}

@media (max-width: 768px) {
  .scenario-grid {
    grid-template-columns: 1fr;
  }

  .tip-list {
    grid-template-columns: 1fr;
  }
}
</style>
