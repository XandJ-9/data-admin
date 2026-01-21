# ETL模块开发实施计划

> **版本**: v2.0 (更新于 2026-01-21)
> **状态**: ✅ Phase 1-3 已完成，正在进行 Phase 4

## 项目概述

基于现有数据资产管理平台架构，开发完整的数据ETL模块，支持多阶段数据处理（STG→ODS→DWD→DWS→ADS）、场景驱动设计、简化用户操作流程。

## 📊 总体进度

- ✅ **Phase 1**: 数据模型扩展 (已完成)
- ✅ **Phase 2**: 执行器基础框架 (已完成)
- ✅ **Phase 3**: API接口开发 (已完成)
- 🔄 **Phase 4**: 前端开发 (进行中)
- ⏳ **Phase 5**: 高级功能 (待开始)
- ⏳ **Phase 6**: 部署与测试 (待开始)

**整体进度**: 约 60%

## ✅ 已完成的工作 (Phase 1-3)

### Phase 1: 数据模型扩展 ✅

**完成时间**: 2026-01-21

**核心成果**:
- ✅ 模块重命名: `dataintegration` → `dataetl` (更简洁的命名)
- ✅ 旧代码备份: `_old_backup/` 目录保留旧实现
- ✅ 新增简化模型设计:
  - **ETLTask**: 场景驱动的任务主表，支持5种ETL场景
  - **ETLExecution**: 任务执行记录表，完整的执行状态跟踪
  - **ETLTemplate**: 任务模板表，可复用配置

**模型特性**:
- 场景驱动设计 (biz_to_stg, stg_to_ods, warehouse_transform等)
- 智能默认值，减少用户配置
- JSONField 存储灵活配置
- 完整的审计字段 (继承 BaseModel)

**相关文件**:
- [backend/apps/dataetl/models.py](backend/apps/dataetl/models.py)
- [backend/apps/dataetl/migrations/0004_datalineage_integrationtaskversion_and_more.py](backend/apps/dataetl/migrations/0004_datalineage_integrationtaskversion_and_more.py)
- [backend/apps/dataetl/migrations/0005_auto_20260121_1542.py](backend/apps/dataetl/migrations/0005_auto_20260121_1542.py)

### Phase 2: 执行器基础框架 ✅

**完成时间**: 2026-01-21

**核心成果**:
- ✅ 抽象执行器基类
- ✅ DataX执行器框架
- ✅ Spark SQL执行器框架
- ✅ 执行器工厂模式

**执行器特性**:
- 统一的执行器接口
- 配置验证和生成
- 执行状态跟踪
- 日志记录和错误处理

**相关文件**:
- [backend/apps/dataetl/executors/base.py](backend/apps/dataetl/executors/base.py)
- [backend/apps/dataetl/executors/datax_executor.py](backend/apps/dataetl/executors/datax_executor.py)
- [backend/apps/dataetl/executors/sparksql_executor.py](backend/apps/dataetl/executors/sparksql_executor.py)
- [backend/apps/dataetl/executors/factory.py](backend/apps/dataetl/executors/factory.py)

### Phase 3: API接口开发 ✅

**完成时间**: 2026-01-21

**核心成果**:
- ✅ 序列化器
- ✅ 视图集 (ViewSet)
- ✅ URL路由配置
- ✅ 集成到主路由

**API端点**:
- `GET /data-api/etl/tasks/` - 任务列表
- `POST /data-api/etl/tasks/` - 创建任务
- `GET /data-api/etl/tasks/scenarios/` - 获取场景配置
- `POST /data-api/etl/tasks/{id}/execute/` - 执行任务
- `GET /data-api/etl/tasks/{id}/executions/` - 执行历史
- `GET /data-api/etl/executions/` - 执行记录列表
- `GET /data-api/etl/templates/` - 模板列表

**相关文件**:
- [backend/apps/dataetl/serializers.py](backend/apps/dataetl/serializers.py)
- [backend/apps/dataetl/views.py](backend/apps/dataetl/views.py)
- [backend/apps/dataetl/urls.py](backend/apps/dataetl/urls.py)
- [backend/config/urls.py](backend/config/urls.py) (已集成)

### Phase 4: 前端开发 🔄 (进行中)

**完成时间**: 约 70%

**已完成**:
- ✅ 前端API封装
- ✅ 路由配置
- ✅ 任务列表页面
- ✅ 简化创建入口
- ✅ 核心组件框架:
  - ScenarioSelector (场景选择器)
  - SimplifiedWizard (简化配置向导)
  - ExecutionMonitor (执行监控)
  - 多个辅助组件 (数据源选择、表选择、SQL编辑器等)

**相关文件**:
- [frontend/src/api/data/etl.js](frontend/src/api/data/etl.js)
- [frontend/src/router/index.js](frontend/src/router/index.js)
- [frontend/src/views/data/etl/taskList.vue](frontend/src/views/data/etl/taskList.vue)
- [frontend/src/views/data/etl/index.vue](frontend/src/views/data/etl/index.vue)
- [frontend/src/views/data/etl/taskDetail.vue](frontend/src/views/data/etl/taskDetail.vue)

**待完善**:
- ⏳ 辅助组件的完整功能实现
- ⏳ 任务详情页
- ⏳ 执行日志实时显示
- ⏳ 字段映射可视化编辑器

## 当前状态分析

### 已有基础设施 ✓
- **数据模型**: `ETLTask`, `ETLExecution`, `ETLTemplate` 新模型 ✅
- **任务调度**: `TaskScheduler` 支持cron/interval调度
- **任务监控**: `TaskLog`, `AlertRule`, `AlertRecord` 监控告警
- **数据源管理**: `DataSource` 支持多种数据库类型
- **元数据管理**: `MetaTable`, `MetaColumn` 元数据采集
- **执行器抽象**: `dataetl/executors/` 包含ETL执行器框架 ✅

### 缺失的核心功能 ⏳
- **执行器实际执行**: 执行器框架已搭建，需要完善具体执行逻辑 ⏳
- **DataX实际集成**: 框架已就绪，需要完善配置生成和subprocess调用 ⏳
- **Spark SQL实际执行**: 框架已就绪，需要完善作业提交和监控 ⏳
- **版本管理**: 框架未实现
- **血缘追踪**: 框架未实现
- **质量检查**: 未集成
- **多租户优化**: 未实现 (原计划的5000+租户优化)

## 架构设计

### 数据流架构

```
外部数据源（多租户分库）
    ↓ [DataX执行器 - 高效并发]
STG缓冲层（按tenant_id/ds分区，保留原始数据）
    ↓ [Spark SQL执行器 - 多租户聚合]
ODS原始层（跨租户汇总、标准化、去重）
    ↓ [Spark SQL执行器 - 数据转换]
DWD明细层（维度化、业务加工）
    ↓ [Spark SQL执行器 - 指标聚合]
DWS汇总层（聚合计算、指标生成）
    ↓ [Spark SQL执行器 - 应用层处理]
ADS应用层（应用专用、宽表、标签）
    ↓
数据服务/BI报表
```

### 多租户隔离策略（5000+租户优化方案）

### 实际环境约束
- **租户数量**: 5000+
- **数据源架构**: 混合模式（多租户共享同一数据源的不同数据库）
- **同步频率**: 天级（每天一次）
- **保留策略**: 短期保留（1-7天）

### 优化后的STG层采集方案

**关键优化点**：
1. **单DataX任务采集同源多租户库**: 同一MySQL实例下的多个租户库，使用单个DataX任务并发采集
2. **按数据源分组而非按租户**: 任务数 = 数据源数量（如10个数据源），而非5000个租户
3. **DataX多库配置**: 在单个DataX job中配置多个数据库连接

**STG采集任务配置**：
```python
IntegrationTask:
    name = "数据源A_5000租户_用户表_STG采集"
    type = "dbToHive"
    executor_type = "datax"

    # 单个数据源，采集该数据源下所有租户库
    source_datasource = DataSource A (MySQL实例1: host1:3306)
    source_databases = ["tenant_db_001", "tenant_db_002", ..., "tenant_db_500"]  # 500个租户库
    source_table = "user"

    target_datasource = Hive数据源
    target_table = "stg_user"
    target_partition = {"type": "date", "field": "ds", "format": "yyyyMMdd"}

    # 多租户字段标识
    tenant_id_field = "tenant_id"  # 从数据库名提取或表中字段
    is_multi_db_task = True  # 标识为多库采集任务
```

**DataX配置示例（单Job多DB）**：
```json
{
  "job": {
    "content": [{
      "reader": {
        "name": "mysqlreader",
        "parameter": {
          "username": "root",
          "password": "password",
          "column": ["id", "name", "email", "tenant_id"],
          "connection": [
            {"jdbcUrl": ["jdbc:mysql://host1:3306/tenant_db_001"], "table": ["user"]},
            {"jdbcUrl": ["jdbc:mysql://host1:3306/tenant_db_002"], "table": ["user"]},
            "...",
            {"jdbcUrl": ["jdbc:mysql://host1:3306/tenant_db_500"], "table": ["user"]}
          ],
          "concurrency": 10  // 并发度
        }
      },
      "writer": {
        "name": "hivewriter",
        "parameter": {
          "column": ["id", "name", "email", "tenant_id", "ds"],
          "writeMode": "insert",
          "partition": "dt='${bizdate}'",
          "connection": [{
            "jdbcUrl": "jdbc:hive2://hive:10000/dw",
            "table": ["stg_user"]
          }]
        }
      }
    }]
  }
}
```

**任务数量对比**：
- ❌ 原方案: 5000+ DataX任务（每个租户一个）
- ✓ 优化方案: N个任务（N = 数据源数量，如10-20个）

**故障隔离**：
- 按数据源维度隔离：数据源A的采集失败不影响数据源B
- 单库失败不影响同数据源其他库：DataX会记录失败详情
- 断点续传：DataX支持失败重试和断点续传

### ODS层聚合方案

**ODS聚合任务配置**：
```python
MultiTenantAggregationTask:
    ods_task = ODS用户表聚合任务
    stg_tasks = [数据源A_STG任务, 数据源B_STG任务, ...]

    # 去重字段（跨数据源全局唯一）
    deduplication_fields = ["user_id", "tenant_id"]

    # 聚合SQL模板
    aggregation_sql = """
        WITH stg_data AS (
            SELECT *, 'ds_A' as source_datasource FROM stg_user WHERE ds='${bizdate}'
            UNION ALL
            SELECT *, 'ds_B' as source_datasource FROM stg_user WHERE ds='${bizdate}'
            ...
        ),
        deduplicated AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY user_id, tenant_id
                       ORDER BY update_time DESC
                   ) as rn
            FROM stg_data
        )
        INSERT OVERWRITE TABLE ods_user PARTITION (ds='${bizdate}')
        SELECT user_id, name, email, tenant_id, source_datasource
        FROM deduplicated
        WHERE rn = 1
    """
```

### 成本分配策略

**存储成本**（按STG分区）：
```sql
-- 租户A存储成本
SELECT
    tenant_id,
    SUM(size) as storage_bytes
FROM (
    SHOW PARTITIONS stg_user
)
WHERE ds >= '${start_date}' AND ds <= '${end_date}'
GROUP BY tenant_id
```

**计算成本**（按任务执行记录）：
```python
TaskExecutionLog:
    task_id = 数据源A_STG任务
    rows_read = 50,000,000  # 读取5000万行
    duration_seconds = 3600  # 耗时1小时

    # 成本计算
    compute_cost = duration_seconds * cpu_cost_per_second
```

### 分级采集策略（可选优化）

针对不同重要性的租户采用不同策略：

**核心租户（Top 100）**：
- 采集频率: 天级（优先执行）
- SLA保证: 上午6点前完成
- 独立监控: 单独告警规则

**普通租户（剩余4900+）**：
- 采集频率: 天级（批量执行）
- SLA保证: 上午10点前完成
- 批量处理: 合并到同一个DataX任务

## 实施方案

> **注意**: 本章节为原计划，实际实施采用了更简化的场景驱动设计。实际实现见"已完成的工作"章节。

### 阶段1: 数据模型扩展 ✅ (已完成 2026-01-21)

#### 实际实现 vs 原计划

**原计划**: 扩展 IntegrationTask 模型（15个新字段）
**实际实现**: 创建全新的 ETLTask 模型（场景驱动设计）

**实际文件**: `backend/apps/dataetl/models.py` ✅

**原计划的字段设计** (仅供参考，已被更简化的设计取代):
```python
# 目标层级
target_layer = CharField(choices=[('stg','STG'),('ods','ODS'),('dwd','DWD'),('dws','DWS'),('ads','ADS')])

# 执行器类型
executor_type = CharField(choices=[('datax','DataX'),('spark_sql','Spark SQL')])

# 数据源配置
source_datasource = ForeignKey(DataSource, related_name='etl_source_tasks')
source_table = CharField()
source_filter = TextField()  # WHERE条件

# 【5000+租户优化】多库采集配置
is_multi_db_task = BooleanField(default=False, verbose_name='是否多库采集任务',
                                 help_text='同一数据源下的多个租户库合并采集')
source_databases = JSONField(default=list, verbose_name='源数据库列表',
                              help_text='如: ["tenant_db_001", "tenant_db_002", ...]')
tenant_id_field = CharField(max_length=128, blank=True, default='', verbose_name='租户ID字段',
                            help_text='用于标识租户的字段名，可为空则从数据库名提取')

# 目标配置
target_datasource = ForeignKey(DataSource, related_name='etl_target_tasks')
target_table = CharField()
target_partition = JSONField(default=dict, verbose_name='分区配置')

# 增量策略
INCREMENTAL_CHOICES = (
    ('full', '全量'),
    ('incremental_addtime', '按新增时间'),
    ('incremental_updatetime', '按更新时间'),
    ('incremental_id', '按自增ID'),
)
incremental_strategy = CharField(max_length=30, choices=INCREMENTAL_CHOICES, default='full')
incremental_field = CharField(max_length=128, blank=True, default='')

# 字段映射
field_mapping = JSONField(default=list, verbose_name='字段映射',
                          help_text='[{"source":"id","target":"user_id","type":"int"}]')

# 执行配置
batch_size = IntegerField(default=10000, verbose_name='批处理大小')
concurrency = IntegerField(default=1, verbose_name='并发度')

# 预处理/后处理SQL
pre_sql = TextField(blank=True, default='', verbose_name='执行前SQL')
post_sql = TextField(blank=True, default='', verbose_name='执行后SQL')
```

#### 1.2 实际实现的模型 ✅

实际创建了以下简化模型（见 [backend/apps/dataetl/models.py](backend/apps/dataetl/models.py)）:

1. **ETLTask** - ETL任务主表
   - 场景驱动设计（5种场景）
   - 智能默认值
   - 简化的配置流程

2. **ETLExecution** - 执行记录表
   - 完整的状态跟踪
   - 统计信息

3. **ETLTemplate** - 模板表
   - 可复用配置

**原计划模型** (已简化，未单独实现):
- *IntegrationTaskVersion* - 任务版本管理 (功能未实现)
- *TaskExecutionLog* - 任务执行详细日志 (已由 ETLExecution 取代)
- *DataLineage* - 数据血缘关系 (功能未实现)
- *MultiTenantAggregationTask* - 多租户聚合配置 (功能未实现)

#### 1.3 数据库迁移 ✅
已完成的迁移文件:
- `backend/apps/dataetl/migrations/0004_datalineage_integrationtaskversion_and_more.py`
- `backend/apps/dataetl/migrations/0005_auto_20260121_1542.py`
- `backend/apps/dataetl/migrations/0006_auto_20260121_1621.py`

---

### 阶段2: 执行器实现 ✅ (已完成框架)

#### 2.1 基础执行器接口 ✅
**实际文件**: [backend/apps/dataetl/executors/base.py](backend/apps/dataetl/executors/base.py) (已完成)

**原计划文件**: `backend/apps/dataintegration/executors/base.py`

```python
class BaseExecutor(ABC):
    @abstractmethod
    def validate(self) -> tuple[bool, str]: pass

    @abstractmethod
    def execute(self) -> Dict[str, Any]: pass

    @abstractmethod
    def cancel(self) -> bool: pass

    def _sync_lineage(self): pass  # 同步血缘
    def _trigger_quality_check(self): pass  # 触发质量检查
```

#### 2.2 DataX执行器 ✅
**实际文件**: [backend/apps/dataetl/executors/datax_executor.py](backend/apps/dataetl/executors/datax_executor.py) (框架已完成)

**原计划文件**: `backend/apps/dataintegration/executors/datax_executor.py`

**已完成**: 基础类结构和配置生成框架
**待完善**: subprocess调用、日志解析

#### 2.4 执行器工厂 ✅
**实际文件**: [backend/apps/dataetl/executors/factory.py](backend/apps/dataetl/executors/factory.py) (已完成)

**原计划文件**: `backend/apps/dataintegration/executors/factory.py`

```python
def get_executor(task, execution_log) -> BaseExecutor:
    if task.executor_type == 'datax':
        return DataXExecutor(task, execution_log)
    elif task.executor_type == 'spark_sql':
        return SparkSQLExecutor(task, execution_log)
    else:
        raise ValueError(f"Unsupported executor: {task.executor_type}")
```

#### 2.5 集成到TaskExecutor
**文件**: `backend/apps/datataskmonitor/taskmanager/executor.py` (已修改)

**说明**: 原计划在这里集成，目前实际集成在 dataetl/views.py 的 execute() action 中

**原计划**: 替换第31行占位符
**实际实现**: 在 ETLTaskViewSet.execute() 中调用执行器

---

### 阶段3: API接口开发 ✅ (已完成)

#### 3.1 Serializers扩展 ✅
**实际文件**: [backend/apps/dataetl/serializers.py](backend/apps/dataetl/serializers.py) (已完成)

**原计划文件**: `backend/apps/dataintegration/serializers.py`

**已实现的序列化器**:
- ETLTaskSerializer - 任务序列化
- ETLExecutionSerializer - 执行记录序列化
- ETLTemplateSerializer - 模板序列化

#### 3.2 ViewSets扩展 ✅
**实际文件**: [backend/apps/dataetl/views.py](backend/apps/dataetl/views.py) (已完成)

**原计划文件**: `backend/apps/dataintegration/views.py`

**已实现的ViewSet**:
- ETLTaskViewSet - 任务管理
- ETLExecutionViewSet - 执行记录管理
- ETLTemplateViewSet - 模板管理

**已实现的Actions**:
- ✅ execute() - 手动触发任务执行
- ✅ executions() - 查询任务执行历史
- ✅ scenarios() - 获取场景配置
- ✅ logs() - 查看执行日志
- ✅ progress() - 查看执行进度
- ⏳ lineage() - 查询数据血缘 (未实现)

---

### 阶段4: 前端开发 🔄 (进行中 70%)

#### 4.1 API封装 ✅
**实际文件**: [frontend/src/api/data/etl.js](frontend/src/api/data/etl.js) (已完成)

**原计划文件**: `frontend/src/api/dataintegration.js`

**已实现的API函数**:

```javascript
// 任务管理
export function listTasks(query) { ... }
export function getTask(id) { ... }
export function createTask(data) { ... }
export function updateTask(id, data) { ... }
export function deleteTask(id) { ... }

// 任务执行
export function executeTask(id) { ... }
export function stopTask(id) { ... }
export function getTaskExecutions(id, query) { ... }

// 执行记录
export function listExecutions(query) { ... }
export function getExecution(id) { ... }
export function getExecutionLogs(id) { ... }
export function getExecutionProgress(id) { ... }

// 场景和模板
export function getScenarios() { ... }
export function listTemplates(query) { ... }
export function applyTemplate(id, data) { ... }
```

#### 4.2 任务列表页面 ✅
**实际文件**: [frontend/src/views/data/etl/taskList.vue](frontend/src/views/data/etl/taskList.vue) (已完成)

**原计划文件**: `frontend/src/views/dataintegration/task/index.vue`

**功能**:
- ✅ 任务列表展示（名称、场景、状态、执行方式）
- ✅ 搜索过滤（任务名、场景、状态）
- ✅ 新增/编辑/删除任务
- ✅ 手动触发执行
- ✅ 查看执行历史

#### 4.3 任务配置表单 ✅
**实际文件**: [frontend/src/views/data/etl/index.vue](frontend/src/views/data/etl/index.vue) (已完成)

**原计划文件**: `frontend/src/views/dataintegration/task/form.vue`

**采用方案**: 简化向导而非复杂表单
- ✅ 场景选择器
- ✅ 数据源选择
- ✅ 表选择
- ✅ 简化配置向导 (3步引导式)

#### 4.4 执行日志页面 🔄
**实际文件**: [frontend/src/views/data/etl/taskDetail.vue](frontend/src/views/data/etl/taskDetail.vue) (部分完成)

**原计划文件**: `frontend/src/views/dataintegration/logs/index.vue`

**功能**:
- ✅ 执行历史列表
- 🔄 执行详情查看（待完善）
- 🔄 实时日志显示（待完善）

---

### 阶段5-6: 原详细计划说明

> **注意**: 以下章节为原计划详情，实际实施采用简化方案。请参考"已完成的工作"和"实施检查清单"了解实际进度。

#### ~~阶段2: 执行器实现（原详细计划）~~
**说明**: 已采用简化框架实现，详见上文"阶段2"

#### ~~阶段3: API接口开发（原详细计划）~~
**说明**: 已完成，详见上文"阶段3"

#### ~~阶段4: 前端开发（原详细计划）~~
**说明**: 已完成70%，详见上文"阶段4"

### 阶段5: 高级功能 ⏳ (待开始)

#### 5.1 版本管理 ⏳
- 保存任务配置快照
- 版本对比（JSON diff）
- 版本回滚

#### 5.2 血缘追踪 ⏳
- 自动提取表级血缘
- 自动提取字段级血缘
- 血缘关系查询（上游/下游）
- 影响分析

#### 5.3 质量检查集成 ⏳
- ETL执行后自动触发质量检查
- 质量规则绑定
- 质量报告生成

#### 5.4 多租户聚合 ⏳ (可选优化)
- STG任务自动标记租户
- ODS聚合任务配置
- 多租户去重SQL生成

---

### 阶段6: 部署与测试 ⏳ (待开始)

#### 6.1 DataX安装配置
```bash
# 下载安装
cd /opt
wget http://datax-opensource.oss-cn-hangzhou.aliyuncs.com/datax.tar.gz
tar -zxvf datax.tar.gz

# 配置环境变量
export DATAX_HOME=/opt/datax
export PATH=$PATH:$DATAX_HOME/bin

# 测试
python $DATAX_HOME/bin/datax.py -r streamreader -w streamwriter
```

#### 6.2 配置更新
**文件**: `backend/config/settings.py`

```python
# DataX配置
DATAX_HOME = os.environ.get('DATAX_HOME', '/opt/datax')
DATAX_LOG_DIR = '/var/log/datax'

# Spark配置
SPARK_HOME = os.environ.get('SPARK_HOME', '/opt/spark')
SPARK_MASTER = 'spark://localhost:7077'
```

#### 6.3 测试计划
1. **单元测试**: 执行器验证、配置生成
2. **集成测试**: 端到端ETL流程
3. **多租户测试**: STG→ODS聚合
4. **性能测试**: 大数据量场景
5. **故障测试**: 异常处理、重试机制

---

## 关键文件清单

### 后端文件（按优先级）

1. **models.py** - 数据模型扩展
   - 新增字段到IntegrationTask
   - 新增4个模型：Version, ExecutionLog, Lineage, MultiTenantAggregation

2. **executors/base.py** (新建) - 执行器基类
3. **executors/datax_executor.py** ✅ (已创建) - DataX执行器框架
4. **executors/sparksql_executor.py** ✅ (已创建) - Spark SQL执行器框架
5. **executors/factory.py** ✅ (已创建) - 执行器工厂

6. **taskmanager/executor.py** (已修改) - 集成真实执行器
   - 说明: 实际集成在 dataetl/views.py 的 execute() action 中

7. **serializers.py** ✅ (已创建) - API序列化器
8. **views.py** ✅ (已创建) - API视图
9. **urls.py** ✅ (已创建) - 路由配置

### 前端文件（按优先级）

**已更新路径**:
1. **api/data/etl.js** ✅ (已创建) - API封装
2. **views/data/etl/taskList.vue** ✅ (已创建) - 任务列表
3. **views/data/etl/index.vue** ✅ (已创建) - 创建入口（简化向导）
4. **views/data/etl/taskDetail.vue** 🔄 (部分完成) - 任务详情
5. **views/data/etl/components/** ✅ (已创建) - 核心组件

**原计划路径** (已更新):
- ~~api/dataintegration.js~~ → api/data/etl.js
- ~~views/dataintegration/task/index.vue~~ → views/data/etl/taskList.vue
- ~~views/dataintegration/task/form.vue~~ → views/data/etl/index.vue (简化版)
- ~~views/dataintegration/logs/index.vue~~ → views/data/etl/taskDetail.vue

### 配置文件

6. **config/settings.py** - 需添加DataX/Spark配置
7. **router/index.js** ✅ (已添加) - 前端路由配置

---

## 实施检查清单

### Phase 1: 数据模型 ✅ (已完成 2026-01-21)
- [x] 创建新模型设计
- [x] 创建ETLTask模型（场景驱动设计）
- [x] 创建ETLExecution模型（执行记录）
- [x] 创建ETLTemplate模型（模板管理）
- [x] 执行数据库迁移 (0004, 0005, 0006)
- [x] 模块重命名 dataintegration → dataetl
- [x] 旧代码备份到 _old_backup/

### Phase 2: 执行器框架 ✅ (已完成 2026-01-21)
- [x] 创建BaseExecutor抽象类
- [x] 创建DataXExecutor框架
  - [x] 基础类结构
  - [x] 配置生成方法框架
  - [ ] _完善_ DataX配置JSON生成逻辑
  - [ ] _完善_ subprocess调用和日志解析
- [x] 创建SparkSQLExecutor框架
  - [x] 基础类结构
  - [x] SQL生成方法框架
  - [ ] _完善_ Spark作业提交逻辑
  - [ ] _完善_ 作业状态监控
- [x] 创建执行器工厂

### Phase 3: API ✅ (已完成 2026-01-21)
- [x] 创建序列化器
- [x] 创建ETLTaskViewSet
  - [x] 列表、创建、更新、删除
  - [x] scenarios() action - 获取场景配置
  - [x] execute() action - 执行任务
  - [x] executions() action - 执行历史
- [x] 创建ETLExecutionViewSet
  - [x] 列表查询
  - [x] 日志查看
  - [x] 进度查询
- [x] 创建ETLTemplateViewSet
- [x] URL路由配置
- [x] 集成到主路由

### Phase 4: 前端 🔄 (进行中 70%)
- [x] 创建API封装 (etl.js)
- [x] 配置路由
- [x] 创建任务列表页面 (taskList.vue)
- [x] 创建简化创建入口 (index.vue)
- [x] 创建核心组件
  - [x] ScenarioSelector - 场景选择器
  - [x] SimplifiedWizard - 简化向导
  - [x] ExecutionMonitor - 执行监控
  - [x] DbSourceSelector - 数据源选择
  - [x] TableSelect - 表选择
  - [x] SqlEditor - SQL编辑器
  - [x] 其他辅助组件
- [ ] 完善任务详情页 (taskDetail.vue)
- [ ] 完善字段映射组件
- [ ] 实现实时日志显示
- [ ] 完善数据预览功能

### Phase 5: 高级功能 ⏳ (待开始)
- [ ] 完善DataX执行器实际执行逻辑
- [ ] 完善Spark SQL执行器实际执行逻辑
- [ ] 实现版本管理 (IntegrationTaskVersion)
- [ ] 实现血缘追踪 (DataLineage)
- [ ] 集成质量检查
- [ ] 实现多租户聚合 (可选)

### Phase 6: 部署与测试 ⏳ (待开始)
- [ ] 配置DataX环境变量
- [ ] 配置Spark环境变量
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 端到端测试
- [ ] 性能测试
- [ ] 用户验收测试

---

## 【关键】5000+租户场景专项测试计划

### 测试场景1：DataX多库并发采集
**目标**: 验证单个DataX任务采集500+租户库的稳定性

**测试用例**:
1. **小规模测试**: 10个租户库，每个库1万行数据
   - 验证数据完整性
   - 记录采集耗时

2. **中等规模测试**: 100个租户库，每个库10万行数据
   - 验证并发度设置（concurrency=10, 20, 50）
   - 监控内存占用
   - 验证断点续传

3. **大规模测试**: 500个租户库，每个库10万行数据
   - 验证最大并发度
   - 测试超时处理
   - 验证错误隔离（部分库失败不影响其他库）

**成功标准**:
- 数据完整性: 100%（行数、数据内容一致）
- 失败隔离: 单库失败不影响其他库
- 超时控制: 单任务超时后自动重试

### 测试场景2：跨数据源ODS聚合
**目标**: 验证多数据源STG数据聚合到ODS的正确性

**测试用例**:
1. **2个数据源聚合**: 每个数据源10个租户库
   - 验证ROW_NUMBER去重逻辑
   - 验证tenant_id字段正确性

2. **10个数据源聚合**: 每个数据源50个租户库
   - 验证UNION ALL性能
   - 验证最终ODS数据唯一性

**成功标准**:
- 去重正确: 相同user_id+tenant_id只保留最新记录
- 性能可接受: 5000万行数据聚合在2小时内完成

### 测试场景3：故障恢复
**目标**: 验证各种故障场景下的恢复能力

**测试用例**:
1. **单库连接失败**: 采集过程中断开某个租户库连接
2. **网络中断**: 采集过程中断开网络
3. **HDFS空间不足**: 写入STG时HDFS空间不足
4. **DataX进程被kill**: 模拟进程被意外终止

**成功标准**:
- 支持断点续传
- 失败任务自动重试
- 不影响其他库的采集

---

## 风险与应对

### 技术风险

**风险1**: DataX与Django集成复杂度
- **应对**: 先实现简单同步场景，逐步增加复杂度

**风险2**: Spark作业管理复杂
- **应对**: Phase 2先实现DataX，Phase 5再实现Spark SQL

**风险3**: 多租户SQL生成错误
- **应对**: 充分测试，提供SQL预览和手动编辑功能

### 进度风险

**风险4**: 8周时间紧张
- **应对**: MVP优先（DataX+基础功能），高级功能后续迭代

### 运维风险

**风险5**: DataX任务卡死
- **应对**: 设置超时机制，支持kill进程，完善监控

---

## 成功标准

### MVP功能 ✅ (已完成 60%)
1. ✅ 数据模型设计 (ETLTask, ETLExecution, ETLTemplate)
2. ✅ API接口开发 (任务CRUD、执行、监控)
3. ✅ 前端基础页面 (任务列表、创建入口)
4. 🔄 执行器框架 (基础框架完成，待完善实际执行)
5. ⏳ 手动/定时执行 (调度系统已存在，待集成)

### 核心功能 🔄 (进行中 40%)
6. 🔄 DataX数据同步 (框架完成)
7. 🔄 Spark SQL转换 (框架完成)
8. 🔄 执行日志查看 (前端部分完成)
9. ⏳ 实时执行监控 (部分完成)

### 高级功能 ⏳ (待实现)
10. ⏳ 多租户聚合
11. ⏳ 版本管理
12. ⏳ 血缘追踪
13. ⏳ 质量检查集成
14. ⏳ 任务模板复用

---

## 🚀 下一步行动计划

### 优先级 P0 (本周完成)
1. **完善执行器实际执行逻辑**
   - [ ] 完善 DataXExecutor 的 `_build_datax_config()` 方法
   - [ ] 实现 subprocess 调用 DataX 命令
   - [ ] 实现 DataX 日志解析和统计信息提取
   - [ ] 完善 SparkSQLExecutor 的 SQL 生成和作业提交

2. **前端组件完善**
   - [ ] 完善 taskDetail.vue 任务详情页
   - [ ] 实现字段映射可视化编辑器
   - [ ] 完善执行日志实时显示 (WebSocket/SSE)

3. **基础功能测试**
   - [ ] 创建测试数据源
   - [ ] 创建测试ETL任务 (各场景)
   - [ ] 端到端测试完整流程

### 优先级 P1 (2周内完成)
4. **集成任务调度**
   - [ ] 将ETL任务集成到现有 TaskScheduler
   - [ ] 支持定时执行
   - [ ] 支持手动触发

5. **错误处理和监控**
   - [ ] 完善异常处理机制
   - [ ] 集成告警系统
   - [ ] 添加执行超时控制

6. **文档完善**
   - [ ] 用户使用手册
   - [ ] API接口文档
   - [ ] 运维部署指南

### 优先级 P2 (后续迭代)
7. **高级功能**
   - [ ] 版本管理实现
   - [ ] 血缘追踪实现
   - [ ] 质量检查集成
   - [ ] 多租户优化 (可选)

---

## 📁 关键文件清单 (更新)

### 后端文件 (已完成)

**核心文件**:
1. ✅ [backend/apps/dataetl/models.py](backend/apps/dataetl/models.py) - 数据模型
2. ✅ [backend/apps/dataetl/serializers.py](backend/apps/dataetl/serializers.py) - API序列化器
3. ✅ [backend/apps/dataetl/views.py](backend/apps/dataetl/views.py) - API视图
4. ✅ [backend/apps/dataetl/urls.py](backend/apps/dataetl/urls.py) - URL路由

**执行器**:
5. ✅ [backend/apps/dataetl/executors/base.py](backend/apps/dataetl/executors/base.py) - 执行器基类
6. ✅ [backend/apps/dataetl/executors/datax_executor.py](backend/apps/dataetl/executors/datax_executor.py) - DataX执行器框架
7. ✅ [backend/apps/dataetl/executors/sparksql_executor.py](backend/apps/dataetl/executors/sparksql_executor.py) - Spark SQL执行器框架
8. ✅ [backend/apps/dataetl/executors/factory.py](backend/apps/dataetl/executors/factory.py) - 执行器工厂

**配置**:
9. ✅ [backend/config/settings.py](backend/config/settings.py) - 需添加DataX/Spark配置
10. ✅ [backend/config/urls.py](backend/config/urls.py) - 已集成ETL路由

### 前端文件 (70% 完成)

**API和路由**:
1. ✅ [frontend/src/api/data/etl.js](frontend/src/api/data/etl.js) - ETL API封装
2. ✅ [frontend/src/router/index.js](frontend/src/router/index.js) - 已配置路由

**页面**:
3. ✅ [frontend/src/views/data/etl/taskList.vue](frontend/src/views/data/etl/taskList.vue) - 任务列表
4. ✅ [frontend/src/views/data/etl/index.vue](frontend/src/views/data/etl/index.vue) - 创建入口
5. 🔄 [frontend/src/views/data/etl/taskDetail.vue](frontend/src/views/data/etl/taskDetail.vue) - 任务详情 (待完善)

**组件**:
6. ✅ [frontend/src/views/data/etl/components/SimplifiedWizard.vue](frontend/src/views/data/etl/components/SimplifiedWizard.vue) - 简化向导
7. ✅ [frontend/src/views/data/etl/components/ScenarioSelector.vue](frontend/src/views/data/etl/components/ScenarioSelector.vue) - 场景选择器
8. ✅ [frontend/src/views/data/etl/components/ExecutionMonitor.vue](frontend/src/views/data/etl/components/ExecutionMonitor.vue) - 执行监控
9. ✅ [frontend/src/views/data/etl/components/DbSourceSelector.vue](frontend/src/views/data/etl/components/DbSourceSelector.vue) - 数据源选择
10. ✅ [frontend/src/views/data/etl/components/TableSelect.vue](frontend/src/views/data/etl/components/TableSelect.vue) - 表选择
11. ✅ [frontend/src/views/data/etl/components/SqlEditor.vue](frontend/src/views/data/etl/components/SqlEditor.vue) - SQL编辑器
12. ✅ 其他辅助组件...

### 文档

1. ✅ [docs/etl-implementation-plan.md](docs/etl-implementation-plan.md) - 本文档 (实施计划)
2. ✅ [docs/etl-implementation-summary.md](docs/etl-implementation-summary.md) - 实施总结
3. ✅ [docs/etl-quickstart.md](docs/etl-quickstart.md) - 快速启动
4. ✅ [docs/etl-simplified-ui-design.md](docs/etl-simplified-ui-design.md) - 设计文档
5. ✅ [docs/etl-module-rename-summary.md](docs/etl-module-rename-summary.md) - 模块重命名总结

---

## 文档输出

本实施计划完成后，需输出以下文档到 `docs/` 目录：

1. **etl-implementation-plan.md** - 本文档
2. **etl-api-reference.md** - API接口文档
3. **etl-user-guide.md** - 用户使用手册
4. **etl-troubleshooting.md** - 故障排查指南
5. **etl-multi-tenant-guide.md** - 多租户配置指南

---

## 附录: 数据源配置示例

### DataX配置示例（MySQL→Hive）

```json
{
  "job": {
    "setting": {
      "speed": {"byte": 1048576, "record": 100000},
      "errorLimit": {"record": 0, "percentage": 0.01}
    },
    "content": [{
      "reader": {
        "name": "mysqlreader",
        "parameter": {
          "username": "root",
          "password": "password",
          "column": ["id", "name", "email"],
          "splitPk": "",
          "where": "update_time > '2026-01-20'",
          "connection": [{
            "jdbcUrl": ["jdbc:mysql://localhost:3306/db"],
            "table": ["user"]
          }]
        }
      },
      "writer": {
        "name": "hivewriter",
        "parameter": {
          "username": "hive",
          "password": "",
          "column": ["id", "name", "email"],
          "writeMode": "insert",
          "partition": "dt='20260121'",
          "connection": [{
            "jdbcUrl": "jdbc:hive2://localhost:10000/dw",
            "table": ["stg_user"]
          }]
        }
      }
    }]
  }
}
```

---

**文档版本**: v2.0 (更新版)
**创建时间**: 2026-01-21
**最后更新**: 2026-01-21
**当前状态**: Phase 1-3 已完成，Phase 4 进行中
**整体进度**: 约 60%
**负责模块**: ETL数据集成模块

### 版本历史
- **v1.0** (2026-01-21): 初始版本，完整实施计划
- **v2.0** (2026-01-21): 更新为实施进度跟踪，标记已完成项目

### 相关文档
- [ETL实施总结](etl-implementation-summary.md) - 已完成工作的详细总结
- [ETL快速启动](etl-quickstart.md) - 如何启动和测试系统
- [ETL简化UI设计](etl-simplified-ui-design.md) - 设计文档
- [模块重命名总结](etl-module-rename-summary.md) - dataintegration → dataetl
