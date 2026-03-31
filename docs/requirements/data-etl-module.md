# 数据ETL模块

数据ETL模块（DataETL）是 Data Admin 平台的数据集成层，负责数据抽取（Extract）、转换（Transform）、加载（Load）的全流程管理。该模块遵循 **"定义任务 → 执行任务 → 调度编排任务"** 的三层架构设计，实现了跨数据源的数据同步、数据清洗转换、数据仓库分层加载等核心功能，支持多种执行引擎和灵活的任务配置。

---

## 功能特性

### 1. ETL任务管理

**任务类型**
- STG采集：外部数据源 → STG缓冲层（快速采集，保持原样）
- DWD转换：STG/ODS → DWD明细层（清洗、去重、标准化）
- ODS加载：STG → ODS原始层（数据汇总和归档）
- 全量ETL：跨层级全流程处理

**核心能力**
- 多执行器支持：Mock（测试）、DataX（离线同步）、Spark SQL（大数据）、Python（自定义）
- 执行策略：全量/增量抽取
- SQL配置：自定义采集、转换、加载SQL
- 版本管理：配置快照、版本对比、一键回滚

### 2. 字段映射管理

- 源字段→目标字段映射配置
- 转换规则：类型转换、默认值、表达式
- 清洗规则：空值处理、格式转换
- 主键标识、排序控制
- 批量导入、类型推断、智能匹配

### 3. 执行监控

- 实时状态跟踪（等待/执行中/成功/失败/已取消）
- 进度统计（总行数、成功/失败行数）
- 性能指标（执行时长、吞吐量）
- 完整执行历史和日志记录

---

## 架构设计

### 三层架构理念

本模块遵循 **"定义任务 → 执行任务 → 调度编排任务"** 的经典三层架构设计：

| 层级 | 职责 | 解决问题 | 实现方式 |
|:---|:---|:---|:---|
| **元数据层（定义层）** | 任务定义、元数据管理 | "做什么" | ETLTask、ETLFieldMapping、版本管理 |
| **计算层（执行层）** | 数据抽取、转换、加载 | "怎么做" | 多执行器（Mock/DataX/Spark/Python） |
| **控制层（调度层）** | DAG编排、依赖触发 | "什么时候做" | Task模块集成、Cron调度（v1.3.x） |

### 数据模型关系

### 核心数据表

| 表名 | 模型 | 说明 |
|------|------|------|
| `dataetl_task` | ETLTask | ETL任务配置 |
| `dataetl_task_version` | ETLTaskVersion | 任务版本历史 |
| `dataetl_field_mapping` | ETLFieldMapping | 字段映射配置 |
| `dataetl_execution_log` | ETLExecutionLog | 执行日志 |
| `dataetl_watermark` | ETLWatermark | 增量水印（v1.1.x） |

### ETLTask 关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_name` | String(128) | 任务名称 |
| `task_code` | String(64) | 任务编码（唯一） |
| `etl_type` | String(20) | 类型：extract/transform/load/full |
| `executor_type` | String(20) | 执行器：mock/datax/spark/python |
| `execute_strategy` | String(20) | 策略：full/increment |
| `source_datasource_id` | Integer | 源数据源ID |
| `target_datasource_id` | Integer | 目标数据源ID |
| `source_table_id` | Integer | 源表ID |
| `target_table` | String(256) | 目标表名 |
| `sql_config` | Text | SQL配置（JSON） |
| `executor_params` | JSONField | 执行器参数 |
| `is_stg_task` | Boolean | STG多租户任务 |
| `tenant_id_field` | String(64) | 租户ID字段名 |

### 执行器接口

```python
class BaseETLExecutor(ABC):
    @abstractmethod
    def validate(self) -> Tuple[bool, str]:
        """验证任务配置"""

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """执行ETL任务"""

    @abstractmethod
    def cancel(self) -> bool:
        """取消执行"""
```

---

## 开发路线

### 版本规划

| 版本 | 主题 | 优先级 | 状态 | 核心功能 |
|------|------|--------|------|----------|
| v1.0.x | 基础框架 | P0 | ✅ 已完成 | 任务管理、Mock执行器、字段映射、版本管理 |
| v1.1.x | DataX集成 | P0 | 🚧 开发中 | DataX执行器、多租户STG、增量抽取、ODS汇总 |
| v1.2.x | Spark SQL | P1 | 📋 计划中 | Spark执行器、DWD/DWS/ADS转换、数据血缘 |
| v1.3.x | 任务调度 | P1 | 📋 计划中 | Cron调度、任务依赖、事件触发 |
| v1.4.x | 质量监控 | P1 | 📋 计划中 | 质量检查、监控大盘、性能分析 |
| v2.0.x | 高级特性 | P2 | 📋 计划中 | Python执行器、CDC、自适应并发、智能恢复 |

### v1.1.x DataX执行器集成（当前阶段）

**目标**：实现基于DataX的离线数据同步，支持多租户STG采集和增量抽取

**核心任务**（4-6周）
- DataX环境配置和依赖安装
- DataX JSON配置生成器（支持MySQL、Oracle、PostgreSQL Reader）
- DataX执行引擎实现（进程管理、日志解析、错误处理）
- 多租户STG任务支持（分区策略、并发执行）
- 增量抽取策略（时间戳/ID增量、水印管理）
- ODS汇总任务（去重、质量初检）

**验收标准**
- 完整流程（STG→ODS）验证通过
- 性能达标：100万行数据 < 5分钟
- 多租户并发执行稳定

### v1.2.x Spark SQL执行器（下一阶段）

**目标**：实现基于Spark SQL的大数据计算能力

**核心任务**（6-8周）
- Spark环境集成（PySpark、Session管理、Hive MetaStore）
- Spark SQL执行器（SQL执行、参数化查询、UDF支持）
- DWD/DWS/ADS层转换任务
- 数据血缘自动生成（SQL解析、表级/字段级血缘）
- 转换规则可视化编辑

### v1.3.x 任务调度与依赖

**目标**：与Task模块深度集成，实现任务调度和依赖管理

**核心任务**
- Task模块集成（调度配置、结果同步、日志推送）
- Cron表达式调度（表达式解析、下次执行时间计算）
- 任务依赖关系管理（拓扑排序、依赖触发、失败处理）
- 事件触发机制
- 黑名单日期配置

### v1.4.x 质量与监控增强

**目标**：与Quality模块集成，实现自动质量检查和任务监控

**核心任务**
- Quality模块集成（规则绑定、自动触发、失败阻断）
- 质量规则绑定UI
- 自动质量检查（ETL执行后触发、质量报告生成）
- 任务监控大盘（实时状态、成功率趋势、异常热点）
- 性能分析与优化

### v2.0.x 高级特性

**核心任务**
- Python脚本执行器（脚本编辑器、版本管理、执行沙箱）
- 实时数据同步（CDC数据源配置、变更数据捕获）
- 自适应并发控制（动态并发度、资源监控、负载均衡）
- 智能故障恢复（故障识别、自动重试、断点续传）
- 元数据自动推荐（类型推断、规则推荐、AI辅助）

### 实施策略建议

基于当前从零搭建的现状，建议采取 **"先核心，后扩展"** 的策略：

1. **第一阶段：数据通路打通**（v1.0.x - v1.1.x）
   - ✅ 任务定义框架（ETLTask、字段映射、版本管理）
   - ✅ Mock执行器（测试验证）
   - 🚧 DataX执行器（离线同步）
   - 🚧 多租户STG采集
   - 🚧 增量抽取能力

2. **第二阶段：数据加工与分层**（v1.2.x）
   - 📋 Spark SQL执行器（大数据计算）
   - 📋 DWD/DWS/ADS转换任务
   - 📋 数据血缘自动生成

3. **第三阶段：自动化与编排**（v1.3.x - v1.4.x）
   - 📋 Task模块集成（调度配置）
   - 📋 Cron调度、任务依赖
   - 📋 Quality模块集成（质量检查）

4. **第四阶段：优化与增强**（v2.0.x）
   - 📋 Python执行器、CDC
   - 📋 自适应并发、智能恢复

---

## 最佳实践与设计原则

### 1. 架构分层原则

遵循典型的湖仓一体分层架构，保持ETL逻辑清晰：

| 分层 | 全称 | 职责 | ETL操作 |
|:---|:---|:---|:---|
| **STG** | Staging Buffer | 外部数据源快速采集缓冲 | 保持原样、不做转换 |
| **ODS** | Original Data Storage | 原始数据层 | 数据汇总、归档、去重 |
| **DWD** | Data Warehouse Detail | 明细数据层 | 清洗、去重、脱敏、标准化 |
| **DWS** | Data Warehouse Service | 汇总数据层 | 宽表建模、主题汇总 |
| **ADS** | Application Data Service | 应用数据层 | 报表、大屏、AI模型接口 |

### 2. 任务抽象与分类

**同步任务（E & L - 数据集成）**
- 定义方式：配置驱动（JSON/YAML）+ UI表单
- 核心要素：源端信息、目标端信息、字段映射、并发度
- 适用场景：异构数据源之间的数据搬运
- 执行引擎：DataX（离线）、Flink CDC（实时）

**转换任务（T - 数据清洗与加工）**
- 定义方式：SQL（首选）或 Python脚本
- 核心要素：依赖的上游表、计算逻辑、目标表、写入模式
- 适用场景：数据过滤、聚合、关联、复杂计算
- 执行引擎：Spark SQL、Hive、ClickHouse、Doris

### 3. 配置化优于脚本化

- **原则**：尽量使用平台定义的配置来完成任务，减少硬编码
- **优势**：数据结构变更时，只需修改元数据配置，无需重新编译发布
- **实现**：
  - 字段映射配置化（`ETLFieldMapping`）
  - SQL配置化（`sql_config` JSON字段）
  - 执行器参数配置化（`executor_params` JSON字段）

### 4. 幂等性设计

**核心原则**：同一个任务重复运行多次，结果必须一致

**实现方式**：
- **写入模式**：采用"先删除后插入"或"Insert Overwrite"模式
- **分区策略**：配合分区字段（如 `dt=20260316`）隔离数据
- **版本管理**：通过 `ETLTaskVersion` 记录配置快照，支持回滚
- **故障恢复**：任务失败重试时，不会产生重复记录

### 5. 元数据管理

所有定义的任务集中统一管理：

- **ETL Meta DB**：基于MySQL/PostgreSQL的元数据库
- **存储内容**：
  - `task_id`, `task_name`, `task_code`
  - `task_type`（STG采集/DWD转换/ODS加载/全量ETL）
  - `source_config`, `target_config`
  - `transform_logic`（SQL或脚本）
  - `owner`, `create_time`, `update_time`
- **版本控制**：Git集成，CI/CD流水线（代码提交 → 自动测试 → 自动部署）

### 6. 数据质量保障

**质量检查策略**：
- **空值检查**：关键维度（如`user_id`）是否存在NULL
- **一致性检查**：数值校验，例如"今日订单金额"不应超过"历史平均水平"的10倍
- **唯一性检查**：主键是否存在重复
- **报警逻辑**：一旦质检失败，立即挂起后续流程，防止脏数据污染下游

**质量规则类型**：
| 规则类型 | 说明 | 示例 |
|:---|:---|:---|
| 完整性 | 检查必填字段、空值比例 | user_id NOT NULL |
| 唯一性 | 检查主键重复 | 主键去重率 = 100% |
| 一致性 | 检查数据逻辑关系 | 订单金额 = 单价 × 数量 |
| 及时性 | 检查数据延迟 | 数据延迟 < 30分钟 |
| 准确性 | 检查数据格式、范围 | 手机号格式、年龄范围 |

**集成方案**（v1.4.x）：
- Quality模块集成（规则绑定、自动触发、失败阻断）
- 质量规则绑定UI
- 自动质量检查（ETL执行后触发、质量报告生成）

### 7. 全链路监控与可观测性

**日志聚合**：
- 所有任务的执行日志统一采集至 ELK 或 Grafana Loki
- 实现秒级检索和问题定位

**关键指标**：
- **性能指标**：执行耗时、吞吐量、资源使用率
- **质量指标**：成功率、数据质量评分、异常数据比例
- **及时性指标**：数据延迟时间、SLA达成率
- **业务指标**：数据行数、数据量大小、增量比例

**任务监控大盘**（v1.4.x）：
- 实时状态展示（等待/执行中/成功/失败/已取消）
- 成功率趋势分析
- 异常热点定位
- 性能瓶颈分析

**数据血缘追踪**（v1.2.x）：
- 基于SQL解析自动生成表级和字段级血缘
- 支持正向血缘（影响分析）和反向血缘（溯源分析）
- 采用 OpenLineage 标准

### 8. 计算引擎选型

根据场景选择不同的执行引擎（多引擎插件化架构）：

| 场景 | 引擎 | 特点 | 适用任务 |
|:---|:---|:---|:---|
| 离线批量集成 | DataX, SeaTunnel | 成熟稳定、插件丰富 | STG采集、ODS加载 |
| 实时增量集成 | Flink CDC, Debezium | 低延迟、Exactly Once | 实时数仓、CDC |
| 离线复杂转换 | Spark, Hive | 大规模、高吞吐 | DWD/DWS转换 |
| 现代ELT架构 | ClickHouse, Doris | 存算一体、高性能 | 实时报表、交互分析 |

**资源调度与隔离**：
- 所有计算任务运行在 K8s 或 YARN 集群上
- 通过分配 Queue 或 Namespace 实现资源隔离
- 防止大任务挤占小任务资源

### 9. 依赖管理

**调度方式**：
- **时间依赖**：Cron表达式调度（每天凌晨 2:00 触发）
- **任务依赖**：基于DAG的依赖关系管理（上游任务完成后触发）
- **事件触发**：数据到达触发、文件到达触发

**依赖管理功能**（v1.3.x）：
- 拓扑排序和循环依赖检测
- 依赖触发机制
- 失败处理策略（失败暂停、失败跳过、失败重试）
- 黑名单日期配置

### 10. DevOps集成

**CI/CD流水线**：
- 将ETL任务逻辑视为代码，使用 Git 进行版本控制
- 自动化流程：代码提交 → 自动化测试（验证SQL语法与逻辑） → 自动部署到生产调度系统

**测试策略**：
- 单元测试：执行器接口测试、SQL语法验证
- 集成测试：端到端流程测试（STG→ODS→DWD）
- 性能测试：基准测试、压力测试
- 回归测试：版本发布前的自动化测试

---

## 附录：工具推荐

| 模块 | 功能重点 | 核心工具推荐 | 当前实现 |
|:---|:---|:---|:---|
| **定义层** | 任务配置、元数据管理 | Git, YAML, 自研元数据DB | ETLTask + Version |
| **执行层** | 数据抽取、计算引擎 | DataX, SeaTunnel, Spark, Flink | Mock/DataX(v1.1.x)/Spark(v1.2.x) |
| **调度层** | DAG编排、依赖触发 | DolphinScheduler, Airflow | Task模块集成(v1.3.x) |
| **监控层** | 告警、血缘、日志 | Prometheus, Grafana, OpenLineage | 执行日志 + 血缘(v1.2.x) |
| **质检层** | 数据校验、质量拦截 | Great Expectations, 自研质检SQL | Quality模块集成(v1.4.x) |

---

## 参考架构

### 典型ETL任务示例

**STG采集任务**（配置驱动）：
```json
{
  "taskId": "sync_mysql_to_stg_001",
  "type": "DATA_SYNC",
  "source": {
    "type": "MySQL",
    "table": "user_info",
    "increment_col": "update_time"
  },
  "target": {
    "type": "MySQL",
    "table": "stg_user_info",
    "partition": "dt=${biz_date}"
  },
  "mapping": [
    {"src": "id", "tgt": "user_id"},
    {"src": "name", "tgt": "user_name"}
  ],
  "executor": "datax",
  "concurrent": 2
}
```

**DWD转换任务**（SQL驱动）：
```sql
-- DWD用户明细层转换
INSERT OVERWRITE TABLE dwd_user_info
PARTITION (dt = '${biz_date}')
SELECT
    user_id,
    user_name,
    phone,
    -- 清洗规则
    TRIM(user_name) AS user_name_clean,
    REGEXP_REPLACE(phone, '\\D', '') AS phone_clean,
    -- 脱敏规则
    CONCAT(LEFT(phone, 3), '****', RIGHT(phone, 4)) AS phone_masked,
    -- 标准化
    UPPER(gender) AS gender,
    '${biz_date}' AS data_date
FROM
    ods_user_info
WHERE
    dt = '${biz_date}'
    AND user_id IS NOT NULL  -- 质量过滤
```
