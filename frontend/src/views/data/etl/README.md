# ETL 模块前端实现说明

## 概述

ETL（Extract-Transform-Load）模块提供了完整的数据抽取、转换和加载任务管理功能。前端基于 Vue 3 + Element Plus 实现，包含任务管理、执行监控、日志查看等功能。

## 功能模块

### 1. ETL首页 (`index.vue`)

**功能特性：**
- 统计信息展示（总任务数、启用任务、今日执行、失败任务）
- 快速操作入口（STG采集、DWD转换、ODS加载、全量ETL）
- 最近任务列表
- 支持快速执行和查看任务

**主要API：**
- `listETLTask()` - 获取任务列表
- `executeETLTask()` - 执行任务

### 2. 任务列表 (`taskList.vue`)

**功能特性：**
- 多条件查询（任务名称、任务编码、ETL类型、执行器类型、状态）
- 任务列表展示
- 批量操作（执行、删除）
- 任务克隆功能
- 任务状态管理（启用/停用）

**查询参数：**
```javascript
{
  pageNum: 1,
  pageSize: 10,
  taskName: '',      // 任务名称
  taskCode: '',      // 任务编码
  etlType: '',       // ETL类型: extract/transform/load/full
  executorType: '',  // 执行器类型: mock/datax/spark/python
  status: ''         // 状态: 0-启用, 1-停用
}
```

**主要API：**
- `listETLTask()` - 查询任务列表
- `delETLTask()` - 删除任务
- `executeETLTask()` - 执行任务
- `cloneETLTask()` - 克隆任务

### 3. 任务详情 (`taskDetail.vue`)

**功能特性：**
- 多标签页展示：
  - **基本信息**：任务名称、编码、类型、状态等
  - **数据源配置**：源/目标数据源选择、表名配置
  - **SQL配置**：SQL脚本编辑和格式化
  - **字段映射**：源字段到目标字段的映射关系
  - **执行配置**：执行参数配置（JSON格式）
  - **质检规则**：数据质量检查规则
  - **执行历史**：任务执行历史记录

**编辑模式：**
- 查看模式：只读展示所有信息
- 编辑模式：可修改所有配置信息
- 支持保存、取消、执行等操作

**主要API：**
- `getETLTask()` - 获取任务详情
- `addETLTask()` - 创建任务
- `updateETLTask()` - 更新任务
- `delETLTask()` - 删除任务
- `executeETLTask()` - 执行任务
- `cloneETLTask()` - 克隆任务
- `validateETLConfig()` - 验证配置
- `generateDataXConfig()` - 生成DataX配置
- `dryRunETLTask()` - 模拟执行
- `listETLFieldMapping()` - 获取字段映射
- `batchCreateFieldMapping()` - 批量创建字段映射
- `listETLQualityRule()` - 获取质检规则
- `delETLQualityRule()` - 删除质检规则
- `listETLExecutionLog()` - 获取执行日志

### 4. 执行日志 (`executionLogs.vue`)

**功能特性：**
- 执行日志查询（任务、状态、执行者、时间范围）
- 统计信息展示（总次数、成功率、失败率、平均耗时）
- 执行详情查看：
  - 基本信息（读取/写入行数、数据大小、耗时等）
  - 执行日志（详细日志输出）
  - DataX配置（配置JSON）
  - 质检结果（数据质量检查结果）
  - 执行进度（实时进度展示）
- 支持取消正在执行的任务
- 支持重新执行失败的任务

**查询参数：**
```javascript
{
  pageNum: 1,
  pageSize: 10,
  taskId: '',        // 任务ID
  status: '',        // 执行状态: pending/running/success/failed/cancelled
  executedBy: '',    // 执行者
  startTime: '',     // 开始时间
  endTime: ''        // 结束时间
}
```

**主要API：**
- `listETLExecutionLog()` - 查询执行日志
- `getETLExecutionLogDetail()` - 获取执行详情
- `cancelETLExecution()` - 取消执行
- `executeETLTask()` - 重新执行
- `listETLTaskSimple()` - 获取任务简单列表

## 路由配置

ETL模块路由配置位于 `frontend/src/router/menu.js`：

```javascript
{
  path: '/data-etl',
  component: Layout,
  name: 'DataETL',
  meta: { title: '数据ETL', icon: 'data-integration' },
  children: [
    {
      path: 'home',
      component: () => import('@/views/data/etl/index'),
      name: 'ETLHome',
      meta: { title: 'ETL首页' }
    },
    {
      path: 'tasks',
      component: () => import('@/views/data/etl/taskList'),
      name: 'ETLTaskList',
      meta: { title: 'ETL任务' }
    },
    {
      path: 'execution-logs',
      component: () => import('@/views/data/etl/executionLogs'),
      name: 'ETLExecutionLogs',
      meta: { title: '执行日志' }
    }
  ]
}
```

## API 接口说明

所有API接口定义在 `frontend/src/api/data/etl.js` 中，主要接口分类：

### 任务管理
- `listETLTask(query)` - 查询任务列表
- `getETLTask(id)` - 获取任务详情
- `addETLTask(data)` - 创建任务
- `updateETLTask(data)` - 更新任务
- `delETLTask(ids)` - 删除任务
- `executeETLTask(id)` - 执行任务
- `cloneETLTask(id, data)` - 克隆任务

### 字段映射
- `listETLFieldMapping(query)` - 查询字段映射
- `addETLFieldMapping(data)` - 新增字段映射
- `updateETLFieldMapping(data)` - 更新字段映射
- `delETLFieldMapping(ids)` - 删除字段映射
- `batchCreateFieldMapping(data)` - 批量创建字段映射

### 执行日志
- `listETLExecutionLog(query)` - 查询执行日志
- `getETLExecutionLogDetail(id)` - 获取执行详情
- `cancelETLExecution(id)` - 取消执行

### 其他功能
- `validateETLConfig(id)` - 验证配置
- `generateDataXConfig(id, params)` - 生成DataX配置
- `dryRunETLTask(id)` - 模拟执行
- `getTaskStatistics(id, days)` - 获取任务统计

## 数据模型

### ETL任务对象
```javascript
{
  id: Number,                    // 任务ID
  taskName: String,              // 任务名称
  taskCode: String,              // 任务编码
  description: String,           // 任务描述
  category: String,              // 任务分类
  etlType: String,               // ETL类型: extract/transform/load/full
  executorType: String,          // 执行器类型: mock/datax/spark/python
  executeStrategy: String,       // 执行策略: full/increment
  status: String,                // 状态: 0-启用, 1-停用
  sourceDatasourceId: Number,    // 源数据源ID
  sourceDatasourceName: String,  // 源数据源名称
  targetDatasourceId: Number,    // 目标数据源ID
  targetDatasourceName: String,  // 目标数据源名称
  sourceTableName: String,       // 源表名
  targetTable: String,           // 目标表名
  sqlConfig: String,             // SQL配置
  executorParams: Object,        // 执行参数（JSON）
  createTime: String,            // 创建时间
  updateTime: String             // 更新时间
}
```

### 执行日志对象
```javascript
{
  id: Number,                    // 执行ID
  taskId: Number,                // 任务ID
  taskName: String,              // 任务名称
  taskCode: String,              // 任务编码
  status: String,                // 执行状态: pending/running/success/failed/cancelled
  rowsRead: Number,              // 读取行数
  rowsWritten: Number,           // 写入行数
  dataSize: Number,              // 数据大小（字节）
  duration: Number,              // 耗时（秒）
  progress: Number,              // 进度（百分比）
  startTime: String,             // 开始时间
  endTime: String,               // 结束时间
  executedBy: String,            // 执行者
  errorMessage: String,          // 错误信息
  executionLog: String,          // 执行日志
  datxConfig: String             // DataX配置
}
```

### 字段映射对象
```javascript
{
  id: Number,                    // 映射ID
  taskId: Number,                // 任务ID
  sourceFieldName: String,       // 源字段名
  targetFieldName: String,       // 目标字段名
  dataType: String,              // 数据类型
  transformRule: String,         // 转换规则
  isPrimaryKey: Boolean,         // 是否主键
  sortOrder: Number              // 排序
}
```

## 使用说明

### 创建新任务

1. 点击"新建任务"按钮或选择任务类型
2. 填写基本信息：
   - 任务名称（必填）
   - 任务编码（必填，唯一）
   - ETL类型（STG采集/DWD转换/ODS加载/全量ETL）
   - 执行器类型（模拟/DataX/Spark/Python）
   - 执行策略（全量/增量）
3. 配置数据源：
   - 选择源数据源和源表
   - 选择目标数据源和目标表
4. 配置SQL（可选）
5. 配置字段映射
6. 配置执行参数
7. 保存并执行

### 查看执行日志

1. 进入"执行日志"页面
2. 使用筛选条件查询日志
3. 点击"详情"查看完整执行信息
4. 可查看执行日志、DataX配置、质检结果等

### 任务克隆

1. 在任务列表中点击"克隆"按钮
2. 修改任务名称和编码
3. 确认克隆

## 注意事项

1. **任务编码唯一性**：任务编码必须唯一，创建时系统会自动校验
2. **字段映射**：字段映射需要在任务配置中完整设置，否则可能导致数据转换错误
3. **执行状态**：只有启用状态的任务才能执行
4. **并发限制**：同一任务同时只能有一个实例在执行
5. **数据备份**：建议在执行重要任务前先进行模拟执行验证

## 权限说明

ETL模块相关权限：
- `dataetl:task:query` - 查询任务
- `dataetl:task:create` - 创建任务
- `dataetl:task:edit` - 编辑任务
- `dataetl:task:delete` - 删除任务
- `dataetl:task:execute` - 执行任务
- `dataetl:fieldmapping:query` - 查询字段映射
- `dataetl:executionlog:query` - 查询执行日志

## 扩展开发

如需扩展ETL模块功能，建议遵循以下规范：

1. **组件开发**：使用 Vue 3 Composition API
2. **样式规范**：使用 SCSS，保持与现有风格一致
3. **API调用**：统一使用 `@/api/data/etl.js` 中定义的方法
4. **路由命名**：遵循 `ETL + 功能名称` 的命名规范
5. **状态管理**：简单状态使用组件内 reactive/ref，复杂状态可考虑使用 Pinia
