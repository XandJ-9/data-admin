# 数据ETL模块

数据ETL模块（DataETL）是 Data Admin 平台的数据集成层，负责数据抽取（Extract）、转换（Transform）、加载（Load）的全流程管理。该模块实现了跨数据源的数据同步、数据清洗转换、数据仓库分层加载等核心功能，支持多种执行引擎和灵活的任务配置。

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

### 数据模型关系

```
ETLTask (ETL任务)
  ├─ N → 1 → DataSource (源数据源)
  ├─ N → 1 → DataSource (目标数据源)
  ├─ N → 1 → MetaTable (源表)
  ├─ 1 → N → ETLFieldMapping (字段映射)
  └─ 1 → N → ETLExecutionLog (执行日志)

ETLTaskVersion (任务版本)
  └─ N → 1 → ETLTask
```

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
