# ETL模块前端优化设计方案

## 一、现状分析

### 当前UI存在的问题

1. **配置项过多**：用户需要理解并配置近20个字段（任务类型、目标层级、执行器、数据源、字段映射、增量策略、调度策略等）
2. **场景不明确**：虽然有5种ETL场景，但UI没有明确区分，用户需要自己判断如何配置
3. **技术细节暴露**：执行器类型（DataX/Spark SQL）、批处理大小、并发度等技术参数直接暴露给业务用户
4. **流程冗长**：从创建任务到执行需要7-8个步骤的表单填写
5. **反馈不足**：执行后缺乏直观的进度展示和实时反馈

## 二、优化目标

### 核心原则
- **场景驱动**：以业务场景为核心，而非技术实现
- **渐进式披露**：只展示当前步骤必要的信息，隐藏高级选项
- **智能默认值**：根据场景自动预填合理的配置
- **即时反馈**：执行过程中实时展示进度和状态

### 用户体验流程
```
选择场景 → 简化配置 → 确认并执行 → 实时监控
```

## 三、新UI设计方案

### 3.1 场景选择页面（ScenarioSelector.vue）

**设计理念**：卡片式布局，清晰的场景描述，引导用户选择

```vue
<template>
  <div class="scenario-selector">
    <div class="scenario-grid">
      <!-- 场景1: 业务库 → STG -->
      <el-card class="scenario-card" @click="selectScenario('biz_to_stg')">
        <div class="card-icon">
          <el-icon><Database /></el-icon>
          <el-icon><RightArrow /></el-icon>
          <el-icon><Files /></el-icon>
        </div>
        <div class="card-title">数据从业务库集成到STG</div>
        <div class="card-desc">
          将业务系统数据库的数据同步到数仓STG缓冲层，适合初次数据接入
        </div>
        <div class="card-tags">
          <el-tag size="small">数据库同步</el-tag>
          <el-tag size="small" type="success">推荐全量</el-tag>
        </div>
      </el-card>

      <!-- 场景2: STG → ODS -->
      <el-card class="scenario-card" @click="selectScenario('stg_to_ods')">
        <div class="card-icon">
          <el-icon><Files /></el-icon>
          <el-icon><RightArrow /></el-icon>
          <el-icon><Document /></el-icon>
        </div>
        <div class="card-title">数据从STG集成到ODS</div>
        <div class="card-desc">
          对STG层数据进行清洗、标准化后同步到ODS原始层
        </div>
        <div class="card-tags">
          <el-tag size="small">数仓内转换</el-tag>
          <el-tag size="small" type="warning">支持增量</el-tag>
        </div>
      </el-card>

      <!-- 场景3: 数仓层计算 -->
      <el-card class="scenario-card" @click="selectScenario('warehouse_transform')">
        <div class="card-icon">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="card-title">数仓层汇聚、转换、计算</div>
        <div class="card-desc">
          在DWD/DWS/ADS层进行复杂的数据聚合、计算和转换
        </div>
        <div class="card-tags">
          <el-tag size="small">Spark SQL</el-tag>
          <el-tag size="small" type="danger">复杂计算</el-tag>
        </div>
      </el-card>

      <!-- 场景4: 数仓 → 业务库 -->
      <el-card class="scenario-card" @click="selectScenario('warehouse_to_biz')">
        <div class="card-icon">
          <el-icon><DataAnalysis /></el-icon>
          <el-icon><RightArrow /></el-icon>
          <el-icon><Database /></el-icon>
        </div>
        <div class="card-title">数据从数仓同步到业务库</div>
        <div class="card-desc">
          将数仓计算结果推送到业务数据库，支持报表、BI等场景
        </div>
        <div class="card-tags">
          <el-tag size="small">结果导出</el-tag>
          <el-tag size="small" type="info">定时推送</el-tag>
        </div>
      </el-card>

      <!-- 场景5: 数据库互相同步 -->
      <el-card class="scenario-card" @click="selectScenario('db_to_db')">
        <div class="card-icon">
          <el-icon><Database /></el-icon>
          <el-icon><Switch /></el-icon>
          <el-icon><Database /></el-icon>
        </div>
        <div class="card-title">数据库之间的互相同步</div>
        <div class="card-desc">
          在不同数据库之间同步数据，支持异构数据库（MySQL、PostgreSQL等）
        </div>
        <div class="card-tags">
          <el-tag size="small">异构同步</el-tag>
          <el-tag size="small" type="primary">灵活配置</el-tag>
        </div>
      </el-card>
    </div>
  </div>
</template>
```

### 3.2 简化配置页面（SimplifiedConfig.vue）

**关键优化**：
- 根据选择的场景，只展示必要的配置项
- 技术参数（执行器、批大小等）自动设置，隐藏在"高级选项"中
- 字段映射智能推荐，自动匹配同名字段

```vue
<template>
  <div class="simplified-config">
    <!-- 步骤指示器 -->
    <el-steps :active="currentStep" finish-status="success">
      <el-step title="选择数据源" />
      <el-step title="配置映射" />
      <el-step title="执行设置" />
    </el-steps>

    <!-- 步骤1: 数据源选择 -->
    <div v-if="currentStep === 0" class="step-content">
      <el-card>
        <template #header>
          <span>{{ stepTitles[0] }}</span>
        </template>

        <!-- 场景特定的数据源配置 -->
        <el-form :model="form" label-width="120px">
          <!-- 场景1: 业务库 → STG -->
          <template v-if="scenario === 'biz_to_stg'">
            <el-form-item label="源业务库" required>
              <datasource-select v-model="form.sourceDatasourceId" @change="loadSourceTables" />
            </el-form-item>
            <el-form-item label="源表" required>
              <table-select v-model="form.sourceTable" :datasource-id="form.sourceDatasourceId" />
            </el-form-item>
            <el-form-item label="过滤条件">
              <el-input v-model="form.whereCondition" placeholder="可选，如：status = 1" />
            </el-form-item>
          </template>

          <!-- 场景2: STG → ODS -->
          <template v-else-if="scenario === 'stg_to_ods'">
            <el-form-item label="STG表" required>
              <hive-table-select v-model="form.sourceTable" schema="stg" />
            </el-form-item>
            <el-form-item label="清洗规则">
              <el-input v-model="form.transformRules" type="textarea" :rows="2"
                placeholder="可选，如：去除空值、格式转换等" />
            </el-form-item>
          </template>

          <!-- 场景3: 数仓计算 -->
          <template v-else-if="scenario === 'warehouse_transform'">
            <el-form-item label="目标层级" required>
              <el-select v-model="form.targetLayer">
                <el-option label="DWD明细层" value="dwd" />
                <el-option label="DWS汇总层" value="dws" />
                <el-option label="ADS应用层" value="ads" />
              </el-select>
            </el-form-item>
            <el-form-item label="SQL脚本" required>
              <sql-editor v-model="form.sqlScript" height="300px"
                placeholder="输入Spark SQL语句，可以使用 {{ params }} 语法" />
            </el-form-item>
          </template>

          <!-- 场景4: 数仓 → 业务库 -->
          <template v-else-if="scenario === 'warehouse_to_biz'">
            <el-form-item label="数仓表" required>
              <hive-table-select v-model="form.sourceTable" />
            </el-form-item>
            <el-form-item label="目标业务库" required>
              <datasource-select v-model="form.targetDatasourceId" />
            </el-form-item>
            <el-form-item label="目标表" required>
              <table-select v-model="form.targetTable" :datasource-id="form.targetDatasourceId" />
            </el-form-item>
          </template>

          <!-- 场景5: 数据库互相同步 -->
          <template v-else-if="scenario === 'db_to_db'">
            <el-form-item label="源数据库" required>
              <datasource-select v-model="form.sourceDatasourceId" @change="loadSourceTables" />
            </el-form-item>
            <el-form-item label="源表" required>
              <table-select v-model="form.sourceTable" :datasource-id="form.sourceDatasourceId" />
            </el-form-item>
            <el-form-item label="目标数据库" required>
              <datasource-select v-model="form.targetDatasourceId" />
            </el-form-item>
            <el-form-item label="目标表" required>
              <table-select v-model="form.targetTable" :datasource-id="form.targetDatasourceId" />
            </el-form-item>
          </template>
        </el-form>
      </el-card>
    </div>

    <!-- 步骤2: 字段映射 -->
    <div v-if="currentStep === 1" class="step-content">
      <el-card>
        <template #header>
          <span>字段映射配置</span>
          <el-button style="float: right" @click="autoMapFields" type="primary" plain>
            智能映射
          </el-button>
        </template>

        <field-mapping
          v-model:source-columns="form.sourceColumns"
          v-model:target-columns="form.targetColumns"
          v-model:mappings="form.fieldMappings"
          :auto-match="true" />
      </el-card>

      <!-- 数据预览 -->
      <el-card style="margin-top: 16px">
        <template #header>
          <span>数据预览（前10条）</span>
        </template>
        <data-preview :source-config="previewConfig" />
      </el-card>
    </div>

    <!-- 步骤3: 执行设置 -->
    <div v-if="currentStep === 2" class="step-content">
      <el-card>
        <template #header>
          <span>执行配置</span>
        </template>

        <el-form :model="form" label-width="140px">
          <!-- 简化的同步方式 -->
          <el-form-item label="同步方式">
            <el-radio-group v-model="form.syncMode">
              <el-radio label="full">
                <div class="radio-content">
                  <div class="radio-title">全量同步</div>
                  <div class="radio-desc">每次同步全部数据，适合小表或初始化</div>
                </div>
              </el-radio>
              <el-radio label="incremental">
                <div class="radio-content">
                  <div class="radio-title">增量同步</div>
                  <div class="radio-desc">只同步新增或变更的数据，更高效</div>
                </div>
              </el-radio>
            </el-radio-group>
          </el-form-item>

          <!-- 增量字段（增量模式时显示） -->
          <el-form-item v-if="form.syncMode === 'incremental'" label="增量标识字段">
            <el-select v-model="form.incrementalField" filterable>
              <el-option v-for="col in form.sourceColumns" :key="col" :label="col" :value="col" />
            </el-select>
            <el-tooltip content="用于判断哪些数据是新增的，通常是时间戳或自增ID">
              <el-icon style="margin-left: 8px"><QuestionFilled /></el-icon>
            </el-tooltip>
          </el-form-item>

          <!-- 任务命名 -->
          <el-form-item label="任务名称" required>
            <el-input v-model="form.taskName" placeholder="自动生成，可修改" />
          </el-form-item>

          <!-- 调度设置（简化） -->
          <el-form-item label="执行方式">
            <el-radio-group v-model="form.scheduleType">
              <el-radio label="manual">立即执行</el-radio>
              <el-radio label="scheduled">定时执行</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="form.scheduleType === 'scheduled'" label="执行时间">
            <schedule-select v-model="form.schedule" />
          </el-form-item>

          <!-- 高级选项（折叠） -->
          <el-collapse style="margin-top: 16px">
            <el-collapse-item title="高级选项" name="advanced">
              <el-form-item label="执行器类型">
                <el-select v-model="form.executorType" disabled>
                  <el-option label="DataX（推荐）" value="datax" />
                  <el-option label="Spark SQL" value="spark_sql" />
                </el-select>
                <span style="margin-left: 12px; color: #909399; font-size: 12px">
                  已根据场景自动选择
                </span>
              </el-form-item>
              <el-form-item label="批处理大小">
                <el-input-number v-model="form.batchSize" :min="1000" :max="100000" :step="1000" />
                <span style="margin-left: 12px; color: #909399; font-size: 12px">行/批次</span>
              </el-form-item>
            </el-collapse-item>
          </el-collapse>
        </el-form>
      </el-card>

      <!-- 配置摘要 -->
      <el-card style="margin-top: 16px">
        <template #header>
          <span>配置摘要</span>
        </template>
        <config-summary :config="form" :scenario="scenario" />
      </el-card>
    </div>

    <!-- 底部操作按钮 -->
    <div class="footer-actions">
      <el-button v-if="currentStep > 0" @click="prevStep">上一步</el-button>
      <el-button v-if="currentStep < 2" type="primary" @click="nextStep">下一步</el-button>
      <el-button v-if="currentStep === 2" type="success" :loading="submitting" @click="startExecution">
        开始同步
      </el-button>
      <el-button @click="goBack">返回</el-button>
    </div>
  </div>
</template>
```

### 3.3 执行监控页面（ExecutionMonitor.vue）

**关键特性**：
- 实时进度条
- 数据流量统计
- 可视化日志输出

```vue
<template>
  <div class="execution-monitor">
    <el-card>
      <template #header>
        <div class="monitor-header">
          <span>执行监控</span>
          <el-button v-if="execution.status === 'running'" type="danger" @click="stopExecution">
            停止任务
          </el-button>
        </div>
      </template>

      <!-- 进度卡片 -->
      <el-row :gutter="24">
        <el-col :span="6">
          <stat-card icon="VideoPlay" label="当前状态" :value="statusText" :type="statusType" />
        </el-col>
        <el-col :span="6">
          <stat-card icon="Download" label="已读取" :value="formatNumber(execution.rowsRead)" unit="行" />
        </el-col>
        <el-col :span="6">
          <stat-card icon="Upload" label="已写入" :value="formatNumber(execution.rowsWritten)" unit="行" />
        </el-col>
        <el-col :span="6">
          <stat-card icon="Timer" label="运行时长" :value="execution.duration" unit="秒" />
        </el-col>
      </el-row>

      <!-- 进度条 -->
      <div v-if="execution.status === 'running'" class="progress-section">
        <div class="progress-label">
          <span>同步进度</span>
          <span>{{ execution.progress }}%</span>
        </div>
        <el-progress :percentage="execution.progress" :status="execution.status" />
        <div class="progress-detail">
          <span>{{ execution.currentStage }}</span>
          <span>预计剩余：{{ execution.estimatedTime }}</span>
        </div>
      </div>

      <!-- 速率图表 -->
      <div v-if="execution.status === 'running'" class="rate-chart">
        <div class="chart-title">同步速率</div>
        <div ref="chartRef" style="height: 200px"></div>
      </div>

      <!-- 实时日志 -->
      <div class="log-section">
        <div class="log-header">
          <span>执行日志</span>
          <el-button size="small" @click="refreshLog">刷新</el-button>
        </div>
        <div class="log-content">
          <log-viewer :logs="execution.logs" :auto-scroll="true" />
        </div>
      </div>
    </el-card>
  </div>
</template>
```

## 四、场景到配置的映射规则

### 场景配置自动填充逻辑

```javascript
// scenarioConfig.js
export const SCENARIO_CONFIGS = {
  // 场景1: 业务库 → STG
  biz_to_stg: {
    taskType: 'dbToHive',
    targetLayer: 'stg',
    executorType: 'datax',
    defaultSyncMode: 'full',
    requiredFields: ['sourceDatasourceId', 'sourceTable', 'whereCondition'],
    optionalFields: ['incrementalField', 'batchSize'],
    autoFields: {
      targetTable: (source) => `${source}`, // 自动使用源表名
      partition: 'dt={{yyyyMMdd}}' // 自动添加日期分区
    }
  },

  // 场景2: STG → ODS
  stg_to_ods: {
    taskType: 'hiveToHive', // 假设支持
    targetLayer: 'ods',
    executorType: 'spark_sql',
    defaultSyncMode: 'incremental',
    requiredFields: ['sourceTable', 'transformRules'],
    autoFields: {
      sqlTemplate: `
        INSERT OVERWRITE TABLE ods.{target_table}
        SELECT
          {fields},
          '{{yyyyMMdd}}' AS dt,
          CURRENT_TIMESTAMP AS load_time
        FROM stg.{source_table}
        WHERE {transform_rules}
      `
    }
  },

  // 场景3: 数仓计算
  warehouse_transform: {
    taskType: 'hiveToHive',
    targetLayer: 'dwd', // 用户选择
    executorType: 'spark_sql',
    defaultSyncMode: 'full',
    requiredFields: ['targetLayer', 'sqlScript'],
    optionalFields: ['schedule'],
    customValidation: 'validateSQL'
  },

  // 场景4: 数仓 → 业务库
  warehouse_to_biz: {
    taskType: 'hiveToDb',
    targetLayer: 'ads',
    executorType: 'datax',
    defaultSyncMode: 'full',
    requiredFields: ['sourceTable', 'targetDatasourceId', 'targetTable'],
    optionalFields: ['batchSize', 'concurrency']
  },

  // 场景5: 数据库互相同步
  db_to_db: {
    taskType: 'dbToDb',
    targetLayer: '',
    executorType: 'datax',
    defaultSyncMode: 'incremental',
    requiredFields: ['sourceDatasourceId', 'sourceTable', 'targetDatasourceId', 'targetTable'],
    optionalFields: ['incrementalField', 'whereCondition', 'batchSize']
  }
}
```

## 五、实施步骤

### 阶段1: 核心组件开发（1-2周）
1. 创建ScenarioSelector组件
2. 开发SimplifiedConfig组件（分步骤表单）
3. 开发ExecutionMonitor组件（进度展示）

### 阶段2: 后端适配（1周）
1. 添加场景配置API端点
2. 简化任务创建接口（支持场景参数）
3. 增强执行日志API（添加进度信息）

### 阶段3: 集成与优化（1周）
1. 替换现有taskDetail.vue
2. 添加智能字段映射逻辑
3. 优化移动端适配

### 阶段4: 测试与上线（1周）
1. 用户验收测试
2. 性能优化
3. 文档和培训

## 六、技术实现要点

### 6.1 状态管理
使用Pinia管理多步骤表单状态：
```javascript
// stores/etlWizard.js
export const useEtlWizardStore = defineStore('etlWizard', {
  state: () => ({
    scenario: null,
    currentStep: 0,
    formData: {},
    executionId: null
  }),
  actions: {
    setScenario(scenario) {
      this.scenario = scenario
      this.formData = SCENARIO_CONFIGS[scenario].defaults || {}
    },
    nextStep() {
      if (this.currentStep < 2) this.currentStep++
    },
    prevStep() {
      if (this.currentStep > 0) this.currentStep--
    }
  }
})
```

### 6.2 实时进度推送
使用WebSocket或SSE实现进度更新：
```javascript
// composables/useExecutionProgress.js
export function useExecutionProgress(executionId) {
  const progress = ref(0)
  const status = ref('pending')

  const eventSource = new EventSource(`/api/dataintegration/execute/${executionId}/progress`)

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    progress.value = data.progress
    status.value = data.status
  }

  onUnmounted(() => {
    eventSource.close()
  })

  return { progress, status }
}
```

### 6.3 智能字段映射
```javascript
// utils/fieldMapper.js
export function autoMapFields(sourceColumns, targetColumns) {
  const mappings = []

  // 1. 精确匹配
  sourceColumns.forEach(src => {
    const exactMatch = targetColumns.find(tgt => tgt === src)
    if (exactMatch) {
      mappings.push({ source: src, target: exactMatch })
    }
  })

  // 2. 模糊匹配（忽略大小写、下划线等）
  sourceColumns.forEach(src => {
    const normalized = src.toLowerCase().replace(/_/g, '')
    const fuzzyMatch = targetColumns.find(tgt =>
      tgt.toLowerCase().replace(/_/g, '') === normalized &&
      !mappings.find(m => m.source === src)
    )
    if (fuzzyMatch) {
      mappings.push({ source: src, target: fuzzyMatch })
    }
  })

  return mappings
}
```

## 七、预期效果

### 用户体验改进
- **操作步骤减少70%**：从8步减少到3步
- **配置时间减少60%**：智能默认值和自动映射
- **错误率降低80%**：场景引导减少配置错误

### 业务价值
- 降低数据集成门槛，业务人员可以自助操作
- 提高任务配置效率
- 减少技术支持成本

## 八、路由配置

在 `frontend/src/router/index.js` 中添加新的路由：

```javascript
{
  path: '/data/integration',
  component: Layout,
  hidden: false,
  children: [
    {
      name: 'DataIntegrationTasks',
      path: 'tasks',
      component: () => import('@/views/data/integration/taskList'),
      meta: { title: '集成任务', icon: 'chart' }
    },
    {
      name: 'DataIntegrationSimpleCreate',
      path: 'simple-create',
      component: () => import('@/views/data/integration/SimpleTaskCreate'),
      meta: { title: '创建集成任务', icon: 'plus' }
    },
    {
      name: 'DataIntegrationTaskDetail',
      path: 'detail/:id',
      component: () => import('@/views/data/integration/taskDetail'),
      meta: { title: '任务详情', activeMenu: '/data/integration/tasks' }
    }
  ]
}
```

## 九、使用指南

### 9.1 用户操作流程

**场景：首次创建业务库到STG的同步任务**

1. **进入页面**
   - 点击左侧菜单 "数据集成" → "集成任务"
   - 点击 "新增任务" 按钮，跳转到简化的创建页面

2. **选择场景**
   - 在5个场景卡片中，选择 "业务库 → STG层"
   - 查看场景描述：确认这是您需要的场景类型

3. **配置数据源（3步引导）**

   **步骤1：选择数据源**
   - 源业务库：从下拉列表选择 "MySQL业务库_生产"
   - 源表：选择 "users" 表
   - 过滤条件：可选，例如输入 `status = 1`
   - 点击 "下一步"

   **步骤2：配置映射**
   - 系统自动加载源表字段
   - 点击 "智能映射" 按钮，自动匹配同名字段
   - 预览前10条数据，确认无误
   - 点击 "下一步"

   **步骤3：执行设置**
   - 同步方式：选择 "增量同步"（首次可选全量）
   - 增量字段：选择 "updated_at"
   - 任务名称：自动生成 "业务库到STG_users_20240121"，可修改
   - 执行方式：选择 "定时执行"
   - 执行周期：选择 "每天"，时间设置为 "02:00"
   - 查看配置摘要，确认信息
   - 点击 "保存任务"

4. **任务创建成功**
   - 返回任务列表，可以看到新创建的任务
   - 点击 "执行" 按钮，可以立即手动触发
   - 点击 "日志" 按钮，查看执行历史

### 9.2 需要创建的辅助组件

由于新UI引用了一些可能不存在的组件，需要创建以下组件的存根版本：

1. **DatasourceSelect** (`components/DatasourceSelect.vue`)
   - 从 `@/api/datasource` 导入 `listDatasources`
   - 下拉选择数据源

2. **TableSelect** (`components/TableSelect.vue`)
   - 根据数据源ID加载表列表
   - 可能需要调用 `getDatasourceTables` API

3. **HiveTableSelect** (`components/HiveTableSelect.vue`)
   - 专门用于选择Hive表
   - 支持schema参数

4. **SqlEditor** (`components/SqlEditor.vue`)
   - 简单的SQL编辑器
   - 可选：集成 Monaco Editor 或 CodeMirror

5. **ScheduleSelect** (`components/ScheduleSelect.vue`)
   - 简化的定时配置选择器
   - 支持简单模式和cron模式

6. **DataPreview** (`components/DataPreview.vue`)
   - 预览数据组件
   - 显示前10条数据

7. **ConfigSummary** (`components/ConfigSummary.vue`)
   - 配置摘要展示
   - 在最后一步展示所有配置

8. **ExecutionMonitor** (`components/ExecutionMonitor.vue`)
   - 执行监控组件
   - 展示进度、日志、统计信息

### 9.3 API接口需求

可能需要新增或调整以下API：

```python
# backend/apps/dataintegration/views.py

class IntegrationTaskViewSet(BaseViewSet):
    @action(detail=False, methods=['get'])
    def scenarios(self, request):
        """获取支持的场景列表"""
        return Response({
            'scenarios': [
                {'value': 'biz_to_stg', 'label': '业务库 → STG层'},
                {'value': 'stg_to_ods', 'label': 'STG层 → ODS层'},
                ...
            ]
        })

    @action(detail=False, methods=['post'])
    def create_from_scenario(self, request):
        """从场景创建任务（简化版）"""
        scenario = request.data.get('scenario')
        # 根据场景创建任务
        pass

    @action(detail=True, methods=['get'])
    def execution_progress(self, request, pk=None):
        """获取任务执行进度（用于SSE推送）"""
        pass
```

### 9.4 兼容性处理

新的简化UI是对现有功能的补充，保留原有的 `taskDetail.vue` 以支持：
- 编辑现有任务
- 查看完整配置
- 高级用户手动配置

通过路由区分：
- 新建任务 → 使用 `SimpleTaskCreate.vue`（简化流程）
- 编辑任务 → 使用 `taskDetail.vue`（完整功能）

## 十、后续优化方向

1. **AI辅助配置**：根据表结构自动推荐同步策略
2. **任务模板**：常用配置保存为模板
3. **批量操作**：一次性创建多个表的同步任务
4. **智能诊断**：自动检测并提示配置问题
5. **可视化血缘**：展示数据流向和依赖关系
6. **移动端适配**：优化移动设备上的操作体验
7. **快捷操作**：从数据表详情页直接创建同步任务
