# 数据ETL模块

## 概述

数据ETL模块（DataETL）是 Data Admin 平台的数据集成层，负责数据抽取（Extract）、转换（Transform）、加载（Load）的全流程管理。该模块实现了跨数据源的数据同步、数据清洗转换、数据仓库分层加载等核心功能，支持多种执行引擎和灵活的任务配置。

---

## 功能特性

### 1. ETL任务管理

**核心能力：**
- 多种ETL类型：STG采集、DWD转换、ODS加载、全量ETL
- 多执行器支持：Mock执行器（测试）、DataX、Spark SQL、Python脚本
- 灵活的执行策略：全量抽取、增量抽取
- 源目标映射：支持跨数据源的数据传输
- SQL配置：支持自定义采集、转换、加载SQL
- 任务版本管理：配置快照、版本对比、一键回滚

**ETL任务类型：**
```
STG采集（Extract）
  外部数据源 → STG缓冲层
  用于数据快速采集，保持原样

DWD转换（Transform）
  STG/ODS → DWD明细层
  数据清洗、去重、标准化

ODS加载（Load）
  STG → ODS原始层
  原始数据加载和归档

全量ETL（Full）
  跨层级全流程处理
  支持复杂的多阶段转换
```

### 2. 字段映射管理

**映射配置：**
- 源字段到目标字段的映射关系
- 字段转换规则（类型转换、默认值、表达式）
- 数据清洗规则（空值处理、格式转换）
- 主键字段标识
- 字段排序控制

**批量操作：**
- 支持批量导入字段映射配置
- 自动字段类型推断
- 智能字段名称匹配

### 3. 任务执行引擎

**执行器类型：**

| 执行器 | 说明 | 适用场景 | 状态 |
|--------|------|----------|------|
| Mock | 模拟执行器 | 开发测试 | ✅ 已实现 |
| DataX | 阿里DataX | 离线数据同步 | 🚧 计划中 |
| Spark SQL | Spark SQL引擎 | 大数据计算 | 🚧 计划中 |
| Python | Python脚本 | 自定义逻辑 | 🚧 计划中 |

**执行特性：**
- 异步执行：后台线程执行，不阻塞界面
- 执行超时控制：可配置超时时间
- 失败重试：支持配置重试次数
- 资源限制：CPU、内存、并发度控制

### 4. 执行监控

**实时监控：**
- 执行状态跟踪（等待/执行中/成功/失败/已取消）
- 进度统计：总行数、成功行数、失败行数
- 性能指标：执行时长、吞吐量
- 错误信息记录：详细的错误堆栈

**执行历史：**
- 完整的执行日志记录
- 执行参数快照
- 多种触发方式记录（手动/调度/API）

---

## 架构设计

### 数据模型

```
ETLTask (ETL任务)
  ├─ N → 1 → DataSource (源数据源)
  ├─ N → 1 → DataSource (目标数据源)
  ├─ N → 1 → MetaTable (源表)
  ├─ 1 → N → ETLFieldMapping (字段映射)
  └─ 1 → N → ETLExecutionLog (执行日志)

ETLTaskVersion (任务版本)
  └─ N → 1 → ETLTask

ETLFieldMapping (字段映射)
  └─ N → 1 → ETLTask

ETLExecutionLog (执行日志)
  └─ N → 1 → ETLTask
```

### 数据库表

| 表名 | 模型 | 说明 |
|------|------|------|
| `dataetl_task` | ETLTask | ETL任务配置表 |
| `dataetl_task_version` | ETLTaskVersion | 任务版本历史表 |
| `dataetl_field_mapping` | ETLFieldMapping | 字段映射配置表 |
| `dataetl_execution_log` | ETLExecutionLog | 执行日志表 |

### 核心字段说明

**ETLTask 关键字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_name` | String(128) | 任务名称 |
| `task_code` | String(64) | 任务编码（唯一） |
| `etl_type` | String(20) | ETL类型：extract/transform/load/full |
| `executor_type` | String(20) | 执行器类型：mock/datax/spark/python |
| `execute_strategy` | String(20) | 执行策略：full/increment |
| `source_datasource_id` | Integer | 源数据源ID |
| `target_datasource_id` | Integer | 目标数据源ID |
| `source_table_id` | Integer | 源表ID |
| `target_table` | String(256) | 目标表名 |
| `sql_config` | Text | SQL配置（JSON格式） |
| `executor_params` | JSONField | 执行器参数 |
| `status` | String(1) | 状态：0-启用，1-停用 |

**ETLExecutionLog 关键字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `execution_id` | String(64) | 执行ID（唯一） |
| `status` | String(20) | 状态：pending/running/success/failed/cancelled |
| `trigger_type` | String(20) | 触发方式：manual/schedule/api |
| `total_rows` | Integer | 总行数 |
| `success_rows` | Integer | 成功行数 |
| `failed_rows` | Integer | 失败行数 |
| `duration_seconds` | Integer | 执行时长（秒） |
| `error_message` | Text | 错误信息 |

---

## API 端点

### 基础规则

- **基础路径**: `/data-api/dataetl/`
- **认证**: JWT Token (Bearer)
- **响应格式**: JSON
- **分页参数**: `pageNum`, `pageSize`

### ETL任务管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/tasks/` | GET | 任务列表 |
| `/tasks/simple` | GET | 任务简单列表（下拉框） |
| `/tasks/` | POST | 新增任务 |
| `/tasks/{id}` | GET | 任务详情 |
| `/tasks/{id}` | PUT | 修改任务 |
| `/tasks/{id}` | DELETE | 删除任务 |
| `/tasks/{id}/execute` | POST | 执行任务 |
| `/tasks/{id}/create-version` | POST | 创建版本快照 |
| `/tasks/{id}/versions` | GET | 版本列表 |
| `/tasks/{id}/rollback` | POST | 回滚到指定版本 |

**查询参数：**
- `taskName`: 按任务名称模糊查询
- `taskCode`: 按任务编码模糊查询
- `etlType`: 按ETL类型过滤
- `executorType`: 按执行器类型过滤
- `status`: 按状态过滤（0-启用，1-停用）
- `sourceDatasourceId`: 按源数据源ID过滤
- `targetDatasourceId`: 按目标数据源ID过滤

**创建任务请求示例：**
```json
{
  "taskName": "用户数据同步任务",
  "taskCode": "SYNC_USER_DATA_001",
  "description": "从业务库同步用户数据到数仓",
  "etlType": "extract",
  "executorType": "mock",
  "executeStrategy": "increment",
  "sourceDatasourceId": 1,
  "targetDatasourceId": 2,
  "sourceTableId": 10,
  "targetTable": "ods.user_info",
  "sqlConfig": "SELECT * FROM user_info WHERE update_time >= '{{last_sync_time}}'",
  "executorParams": {
    "timeout": 300,
    "retryTimes": 3
  },
  "status": "0"
}
```

**执行任务响应示例：**
```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "executionId": "ETL-A1B2C3D4E5F6G7H8"
  }
}
```

### 字段映射管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/field-mappings/` | GET | 字段映射列表 |
| `/field-mappings/` | POST | 新增字段映射 |
| `/field-mappings/{id}` | GET | 字段映射详情 |
| `/field-mappings/{id}` | PUT | 修改字段映射 |
| `/field-mappings/{id}` | DELETE | 删除字段映射 |
| `/field-mappings/batch` | POST | 批量创建字段映射 |

**查询参数：**
- `taskId`: 按任务ID过滤
- `sourceFieldName`: 按源字段名模糊查询
- `targetFieldName`: 按目标字段名模糊查询

**批量创建请求示例：**
```json
{
  "mappings": [
    {
      "taskId": 1,
      "sourceFieldName": "user_id",
      "targetFieldName": "id",
      "transformRule": "CAST AS BIGINT",
      "cleanRule": "TRIM",
      "dataType": "BIGINT",
      "isPrimaryKey": true,
      "sortOrder": 1
    },
    {
      "taskId": 1,
      "sourceFieldName": "user_name",
      "targetFieldName": "name",
      "transformRule": "UPPER",
      "cleanRule": "TRIM",
      "dataType": "VARCHAR(100)",
      "isPrimaryKey": false,
      "sortOrder": 2
    }
  ]
}
```

### 执行日志管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/execution-logs/` | GET | 执行日志列表 |
| `/execution-logs/{id}` | GET | 执行日志详情 |
| `/execution-logs/{id}/detail` | GET | 执行日志详细信息 |

**查询参数：**
- `taskId`: 按任务ID过滤
- `executionId`: 按执行ID模糊查询
- `status`: 按执行状态过滤
- `triggerType`: 按触发方式过滤
- `executedBy`: 按执行者模糊查询

---

## 执行器架构

### 执行器接口

所有执行器必须实现 `BaseETLExecutor` 接口：

```python
class BaseETLExecutor(ABC):
    @abstractmethod
    def validate(self) -> Tuple[bool, str]:
        """验证任务配置"""
        pass

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """执行ETL任务"""
        pass

    @abstractmethod
    def cancel(self) -> bool:
        """取消执行"""
        pass
```

### 执行器工厂

```python
ExecutorFactory.create_executor(
    executor_type='mock',
    task=task_instance,
    config=executor_params
)
```

### Mock执行器特性

**用途**: 开发测试阶段的模拟执行器

**特点**:
- 无需真实数据源连接
- 随机执行结果（90%成功率）
- 随机执行时长（1-5秒）
- 随机数据量（1000-100000行）
- 完整的生命周期模拟

**示例输出**:
```json
{
  "status": "success",
  "total_rows": 45678,
  "success_rows": 45678,
  "failed_rows": 0,
  "duration_seconds": 3
}
```

---

## 前端实现

### 组件结构

```
frontend/src/views/data/etl/
├── index.vue                    # ETL任务管理页面 ⭐
├── execution-log.vue            # 执行日志页面 ⭐
├── field-mapping.vue            # 字段映射管理页面 ⭐
├── components/
│   ├── TaskForm.vue             # 任务表单组件（计划中）
│   ├── FieldMappingEditor.vue   # 字段映射编辑器（计划中）
│   └── VersionHistory.vue       # 版本历史组件（计划中）
```

### 页面功能

**ETL任务管理页面** (`index.vue`)
- 搜索栏：任务名称、编码、类型、执行器、状态
- 工具栏：新增、删除、执行
- 数据表格：任务列表展示
- 操作按钮：详情、执行、修改、版本管理、删除
- 表单弹窗：新增/修改任务
- ✅ 源表/目标表下拉选择（自动加载）
- ✅ 版本管理弹窗：创建版本、查看版本历史、版本回滚
- 详情弹窗：查看任务详细信息

**执行日志页面** (`execution-log.vue`)
- 搜索栏：任务、执行ID、状态、触发方式、执行者
- 数据表格：执行日志列表
- 状态标签：等待、执行中、成功、失败、已取消
- 详情弹窗：查看执行详情
- 错误弹窗：查看错误信息

**字段映射管理页面** (`field-mapping.vue`) ⭐ 新增
- 搜索栏：ETL任务、源字段名、目标字段名
- 工具栏：新增、批量删除
- 数据表格：字段映射列表
- 操作按钮：修改、删除
- 表单弹窗：新增/修改字段映射
- 支持配置：源字段、目标字段、转换规则、清洗规则、数据类型、是否主键、排序

### API调用示例

```javascript
import {
  listETLTask,
  addETLTask,
  executeETLTask,
  createETLTaskVersion,
  listETLTaskVersion,
  rollbackETLTaskVersion,
  listETLFieldMapping,
  addETLFieldMapping
} from '@/api/data/etl'

// 查询任务列表
const { rows, total } = await listETLTask({
  pageNum: 1,
  pageSize: 10,
  status: '0'
})

// 创建任务
await addETLTask({
  taskName: '测试任务',
  taskCode: 'TEST_001',
  etlType: 'full',
  executorType: 'mock',
  // ... 其他字段
})

// 执行任务
const { executionId } = await executeETLTask(taskId)

// 创建版本快照
await createETLTaskVersion(taskId, {
  changeLog: '优化SQL查询性能'
})

// 获取版本列表
const versions = await listETLTaskVersion(taskId)

// 回滚到指定版本
await rollbackETLTaskVersion(taskId, {
  versionNumber: 1
})

// 查询字段映射
const { rows } = await listETLFieldMapping({
  taskId: 1,
  pageNum: 1,
  pageSize: 10
})

// 新增字段映射
await addETLFieldMapping({
  taskId: 1,
  sourceFieldName: 'user_id',
  targetFieldName: 'id',
  transformRule: 'CAST AS BIGINT',
  cleanRule: 'TRIM',
  dataType: 'BIGINT',
  isPrimaryKey: true,
  sortOrder: 1
})
```

---

## 使用指南

### 快速开始

#### 1. 创建数据源和元数据

在使用ETL模块前，需要先配置：
- 数据源：源数据库和目标数据库连接
- 元数据：采集源表和目标表的元数据信息

#### 2. 创建ETL任务

**步骤**：
1. 进入"数据ETL管理" → "ETL任务管理"
2. 点击"新增"按钮
3. 填写基本信息：
   - 任务名称：用户数据同步
   - 任务编码：SYNC_USER_001（唯一）
   - ETL类型：STG采集
   - 执行器类型：Mock（测试）
   - 执行策略：增量
4. 选择源目标：
   - 源数据源：业务库
   - 目标数据源：数据仓库
   - 源表：user_info
   - 目标表：stg.user_info
5. 配置SQL（可选）：
   ```sql
   SELECT * FROM user_info WHERE update_time >= '{{last_sync_time}}'
   ```
6. 配置执行参数（可选）：
   ```json
   {
     "timeout": 300,
     "retryTimes": 3
   }
   ```
7. 点击"确定"保存

#### 3. 配置字段映射（可选）

如果需要精细化控制字段映射：

**步骤**：
1. 进入"字段映射管理"
2. 点击"新增"
3. 配置字段映射关系：
   - 源字段：user_id → 目标字段：id
   - 转换规则：CAST AS BIGINT
   - 清洗规则：TRIM
   - 是否主键：是
4. 保存配置

#### 4. 执行任务

**手动执行**：
1. 在任务列表中找到要执行的任务
2. 点击"执行"按钮
3. 系统创建执行记录并异步执行
4. 查看执行日志了解结果

**查看执行日志**：
1. 进入"执行日志"页面
2. 筛选特定任务的执行记录
3. 点击"详情"查看完整信息
4. 如果失败，点击"错误"查看错误详情

### 配置字段映射

如果需要精细化控制字段映射关系：

**步骤**：
1. 进入"字段映射管理"页面
2. 点击"新增"按钮
3. 填写字段映射信息：
   - **ETL任务**：选择关联的任务
   - **源字段名**：源表中的字段名称（如：`user_id`）
   - **目标字段名**：目标表中的字段名称（如：`id`）
   - **转换规则**：字段转换表达式（如：`CAST AS BIGINT`、`UPPER`、`TRIM`）
   - **清洗规则**：数据清洗规则（如：去除空格、默认值）
   - **数据类型**：目标字段数据类型（如：`VARCHAR(100)`、`BIGINT`）
   - **是否主键**：勾选表示该字段是主键
   - **排序**：字段在映射中的顺序
4. 点击"确定"保存

**批量配置**：
- 可以通过 API 批量导入字段映射
- 支持从源表结构自动生成映射关系

### 版本管理

#### 创建版本快照

在修改重要任务配置前，建议创建版本快照：

```javascript
// 调用API
POST /data-api/dataetl/tasks/{id}/create-version
{
  "changeLog": "优化SQL查询性能"
}
```

#### 查看版本历史

```javascript
// 获取版本列表
GET /data-api/dataetl/tasks/{id}/versions

响应：
[
  {
    "versionId": 1,
    "versionNumber": 1,
    "changeLog": "初始版本",
    "isCurrent": false,
    "createTime": "2025-01-20 10:00:00"
  },
  {
    "versionId": 2,
    "versionNumber": 2,
    "changeLog": "优化SQL查询性能",
    "isCurrent": true,
    "createTime": "2025-01-21 15:30:00"
  }
]
```

#### 回滚到指定版本

```javascript
// 回滚到版本1
POST /data-api/dataetl/tasks/{id}/rollback
{
  "versionNumber": 1
}
```

---

## 数据仓库分层

### 五层架构

```
外部数据源
    ↓ Extract
STG缓冲层（Staging）
    ↓ Load
ODS原始层（Original Data Storage）
    ↓ Transform
DWD明细层（Data Warehouse Detail）
    ↓ Aggregate
DWS汇总层（Data Warehouse Summary）
    ↓ Application
ADS应用层（Application Data Service）
```

### 层级说明

| 层级 | 全称 | 说明 | ETL类型 |
|------|------|------|----------|
| STG | Staging | 缓冲层，快速采集原样存储 | extract |
| ODS | Original Data Storage | 原始数据层，保持历史 | load |
| DWD | Data Warehouse Detail | 明细数据层，清洗标准化 | transform |
| DWS | Data Warehouse Summary | 汇总数据层，主题汇总 | transform |
| ADS | Application Data Service | 应用数据层，面向业务 | full |

---

## 权限说明

### 菜单权限

| 权限标识 | 说明 |
|----------|------|
| `system:dataetl:task:query` | 查询ETL任务 |
| `system:dataetl:task:add` | 新增ETL任务 |
| `system:dataetl:task:edit` | 修改ETL任务 |
| `system:dataetl:task:remove` | 删除ETL任务 |
| `system:dataetl:task:execute` | 执行ETL任务 |
| `system:dataetl:fieldmapping:query` | 查询字段映射 |
| `system:dataetl:fieldmapping:edit` | 编辑字段映射 |
| `system:dataetl:executionlog:query` | 查询执行日志 |

### 角色建议

**数据管理员**：所有权限
**开发人员**：任务查询、执行、日志查询
**运维人员**：任务执行、日志查询

---

## 故障排查

### 常见问题

#### 1. 任务执行失败

**可能原因**：
- 源数据源连接失败
- SQL语法错误
- 字段映射不匹配
- 目标表不存在

**解决方法**：
1. 检查执行日志的错误信息
2. 验证数据源连接是否正常
3. 在数据查询模块测试SQL
4. 检查字段映射配置

#### 2. 执行超时

**可能原因**：
- 数据量过大
- 网络延迟
- SQL查询效率低

**解决方法**：
1. 增加`executorParams`中的`timeout`值
2. 优化SQL查询
3. 考虑分批执行

#### 3. 版本回滚失败

**可能原因**：
- 版本号不存在
- 配置快照损坏

**解决方法**：
1. 确认版本号正确
2. 查看版本历史详情
3. 联系管理员检查数据库

### 调试技巧

**开启详细日志**：
```python
# 在 settings.py 中配置
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'apps.dataetl': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
}
```

**查看数据库记录**：
```sql
-- 查看任务配置
SELECT * FROM dataetl_task WHERE del_flag = '0';

-- 查看最新执行日志
SELECT * FROM dataetl_execution_log
ORDER BY create_time DESC
LIMIT 10;

-- 查看字段映射
SELECT * FROM dataetl_field_mapping
WHERE task_id = 1
ORDER BY sort_order;
```

---

## 开发指南

### 前端开发规范

**重要**：ETL 模块前端开发必须遵循以下规范：

1. **使用 API 模块封装**
   - ✅ 正确：从 `@/api/data/etl` 导入 API 函数
   - ❌ 错误：使用 `proxy.request()` 直接发起请求

2. **导入 getCurrentInstance**
   - 如果需要使用 `proxy`（如 `proxy.$modal`、`proxy.resetForm`），必须先导入：
   ```javascript
   import { getCurrentInstance } from 'vue'
   const { proxy } = getCurrentInstance()
   ```

3. **示例对比**
   ```javascript
   // ❌ 错误示例（违反规范）
   function loadData() {
     return proxy.request({
       url: '/dataetl/tasks',
       method: 'get'
     })
   }

   // ✅ 正确示例（遵循规范）
   import { listETLTask } from '@/api/data/etl'

   function loadData() {
     return listETLTask()
   }
   ```

### 添加新执行器

#### 1. 创建执行器类

在 `backend/apps/dataetl/executors/` 下创建新文件：

```python
from .base import BaseETLExecutor, ExecutorFactory

class MyCustomExecutor(BaseETLExecutor):
    def validate(self):
        # 验证配置
        return True, ""

    def execute(self):
        # 执行ETL逻辑
        return {
            'status': 'success',
            'total_rows': 1000,
            'success_rows': 1000,
            'failed_rows': 0,
            'duration_seconds': 10
        }

    def cancel(self):
        # 取消执行
        return True

# 注册执行器
ExecutorFactory.register_executor('custom', MyCustomExecutor)
```

#### 2. 更新模型选项

在 `ETLTask` 模型中添加新选项：

```python
class ETLTask(BaseModel):
    EXECUTOR_TYPE_CHOICES = [
        ('mock', '模拟执行器'),
        ('datax', 'DataX'),
        ('spark', 'Spark SQL'),
        ('custom', '自定义执行器'),  # 新增
    ]
```

#### 3. 更新前端选项

在前端页面添加新选项：

```vue
<el-select v-model="form.executorType">
  <el-option label="自定义执行器" value="custom" />
</el-select>
```

### 扩展字段映射

添加新的转换规则类型：

1. 在 `ETLFieldMapping` 模型中添加字段
2. 在执行器中实现转换逻辑
3. 在前端表单中添加配置UI

---

## 未来规划

### 短期计划（v1.1.0）

- [x] 字段映射管理页面
- [x] 版本管理功能（创建版本、查看版本、版本回滚）
- [x] 目标表下拉选择功能
- [ ] 可视化字段映射编辑器（拖拽式）
- [ ] 任务依赖关系配置
- [ ] 执行器参数配置UI
- [ ] SQL语法高亮编辑器
- [ ] 执行进度实时展示

### 中期计划（v1.2.0）

- [ ] DataX执行器集成
- [ ] Spark SQL执行器集成
- [ ] 定时调度功能
- [ ] 任务监控大盘
- [ ] 数据质量检查规则

### 长期计划（v2.0.0）

- [ ] 实时数据同步（CDC）
- [ ] 自适应并发控制
- [ ] 智能故障恢复
- [ ] 数据血缘自动生成
- [ ] 元数据自动推荐

---

## 更新日志

### v1.0.1 (2026-02-06)

**前端功能增强**

✨ 新功能：
- ✅ 字段映射管理页面（`field-mapping.vue`）
  - 字段映射 CRUD 操作
  - 支持转换规则和清洗规则配置
  - 主键标识和排序功能
  - 任务关联查询
- ✅ 版本管理功能
  - 创建版本快照（带变更日志）
  - 查看版本历史列表
  - 一键回滚到指定版本
  - 当前版本标识显示
- ✅ 目标表选择优化
  - 下拉选择（支持手动输入）
  - 自动加载目标数据源的表列表
  - 选择数据源后自动刷新表列表

🐛 问题修复：
- 修复 `proxy.request is not a function` 错误
- 遵循开发规范，使用 API 模块封装
- 添加缺失的 `getCurrentInstance` 导入

🔧 技术改进：
- 添加字段映射管理路由配置
- 完善前端组件结构
- 优化用户体验（表单联动、数据加载）

### v1.0.0 (2026-02-05)

**初始版本**

✨ 新功能：
- ETL任务管理（增删改查）
- 字段映射管理
- Mock执行器（开发测试）
- 执行日志查询
- 任务版本管理
- 版本回滚功能
- 完整的权限控制

🔧 技术特性：
- 继承BaseModel（软删除、审计字段）
- 继承BaseModelSerializer（自动字段处理）
- 执行器工厂模式
- 异步任务执行
- RESTful API设计

📝 文档：
- API文档
- 使用指南
- 开发指南
- 故障排查

---

## 相关文档

- [总体架构设计](platform-architecture-design.md) - ETL模块设计规范
- [开发指南](development-guide.md) - 核心抽象和命名规范
- [数据资产模块](data-asset-module.md) - 数据源和元数据管理
- [数据服务模块](data-service-module.md) - 数据查询服务

---

## 联系方式

- **模块负责人**: 数据团队
- **问题反馈**: [GitHub Issues](https://github.com/XandJ-9/data-admin/issues)
- **更新时间**: 2026-02-06

---

**文档版本**: v1.0.1
**最后更新**: 2026-02-06
