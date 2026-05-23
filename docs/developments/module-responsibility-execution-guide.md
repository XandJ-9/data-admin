# 业务模块职责与统一执行层开发手册

## 1. 文档定位

本文是当前阶段后续开发的模块职责执行手册，用于把 `datasource`、`dataintegration`、`datadev`、`datatask`、`executors`、`dbutils` 的边界固定下来。

本文与现有文档关系如下：

1. `ADR-002` 定义平台分层与五阶段职责边界。
2. `ADR-003` 定义业务任务真源、平台任务镜像与执行实例边界。
3. `development-priority-correction-2026-04-30.md` 定义未来阶段的开发顺序。
4. 本文在上述三份文档基础上，进一步明确三个业务模块的功能形态与统一执行层约束。

后续涉及数据源、数据集成、数据开发、任务执行、数据库查询、执行器扩展的需求评审、代码实现和代码评审，必须优先按本文检查。

## 2. 核心原则

### 2.1 三个业务模块只定义“要做什么”

`datasource`、`dataintegration`、`datadev` 是业务定义真源。它们负责表达各自业务对象、调试入口、发布入口和执行计划，但不应该自己实现数据库驱动连接、SQL 执行、DataX 执行、Spark/Hive 执行等底层动作。

### 2.2 `datatask` 只管理“什么时候跑、谁在跑、跑成什么样”

`datatask.Task` 是平台任务镜像和调度索引，不是业务任务真身。

`datatask.TaskInstance` 是全平台唯一执行记录中心。所有手动执行、调试执行、定时执行、依赖触发执行，都必须进入 `TaskInstance`，不能在业务模块重新建立私有执行历史表。

### 2.3 `executors/dbutils` 负责“怎么实际执行”

所有涉及任务执行、数据库连接、数据库查询、库表字段探查、DataX/Spark/Hive/MVP 预演等动作，都必须通过 `apps.executors` 或 `apps.dbutils` 承接。

业务模块不能因为短期方便直接引入 `pymysql`、`psycopg2`、`sqlite3`、`trino`、`sqlalchemy` 等驱动并自行连接外部数据源。

### 2.4 source handler 是唯一跨模块执行分发协议

业务模块接入统一任务中心时，必须通过 `apps.datatask.source_registry.SourceHandler` 注册来源能力。

`TaskService.execute_task` 只按 `source_module + source_record_id` 找到来源记录，再调用来源 handler。`datatask` 不反向理解业务模块内部模型和执行细节。

## 3. 当前现状对照

| 模块 | 当前符合点 | 需要继续收敛的点 |
| --- | --- | --- |
| `datasource` | 已保留 `DataSource` 与 `DataSourceCollectionTask`；发现链路通过 `dbutils`；采集实例统一进入 `TaskInstance` | 采集任务目前更多由采集入口隐式创建与同步，后续应补齐显式采集任务列表、编辑、发布入口 |
| `dataintegration` | 已将保存业务配置和发布到任务中心分离；执行通过 `ExecutorFactory`；执行实例统一进入 `TaskInstance` | 继续避免把发布、调度、快照字段重新塞回业务任务定义 |
| `datadev` | 已保留 `DataDevScript` / `DataDevModel` 作为真源；只有脚本发布为任务中心来源，模型定义、保存和建表动作不再同步平台任务镜像；SQL 查询走 `dbutils`，Spark/Hive 走 `executors` | MVP 预演、建模执行等运行逻辑后续应尽量沉淀为正式 executor，模型建表建议进一步复用脚本执行链路 |
| `datatask` | 已具备 `TaskService`、发布快照边界、source handler 分发与执行 envelope 归一化 | 继续保持任务镜像定位，不扩张为业务定义中心 |
| `executors/dbutils` | 已承接数据库查询、库表探查、DataX、Spark SQL、Mock/MVP 类执行器 | 需要把“唯一执行层”写入后续代码评审标准，新增执行能力默认先落这里 |

## 4. 模块职责规范

### 4.1 `datasource`

`datasource` 负责连接与发现阶段的业务定义。

应该负责：

1. 数据源定义：`DataSource`。
2. 数据源连接测试入口。
3. 数据库、表、字段发现入口。
4. 源数据采集任务定义：`DataSourceCollectionTask`。
5. 单表采集、整库采集的业务入口。
6. 将采集任务发布或同步为 `datatask.Task`。
7. 通过 source handler 向 `datatask` 暴露采集任务加载、执行、实例归一化和陈旧实例清理能力。

不应该负责：

1. 自行创建外部数据库连接。
2. 自行实现数据库驱动适配。
3. 自行维护采集执行历史表。
4. 把 cron、依赖、调度索引、平台快照字段重新放回 `DataSourceCollectionTask`。
5. 绕开 `dataasset.facades` 直接写资产内部细节。

执行要求：

1. 连接测试必须通过 `apps.dbutils.factory.get_executor`。
2. 库表字段发现必须通过 `apps.dbutils` 的统一函数。
3. 采集落资产必须通过 `apps.dataasset.facades`。
4. 采集执行实例必须通过 `TaskService.create_task_instance` 与 `TaskService.finalize_instance`。

后续优先补齐：

1. `DataSourceCollectionTask` 的正式列表、详情、编辑、启停与发布入口。
2. 单表采集和整库采集统一从采集任务定义发起，而不是只在详情页动作中隐式生成。
3. 整库采集当前线程式运行后续应迁入统一 executor 或后台 worker。

### 4.2 `dataintegration`

`dataintegration` 负责数据集成阶段的业务定义。

应该负责：

1. 同步任务定义：`DataIntegrationTask`。
2. 源数据源、源库、源表、目标数据源、目标 schema、目标表定义。
3. 同步策略、写入模式、执行器类型和字段映射配置。
4. 业务配置保存。
5. 单次调试执行。
6. 显式发布到任务中心。
7. 通过 source handler 向 `datatask` 暴露同步任务加载、执行和治理字段回写能力。

不应该负责：

1. 自行执行 DataX、Spark、Flink、SeaTunnel 等引擎逻辑。
2. 自行连接源库或目标库执行同步。
3. 自行维护同步执行历史表。
4. 创建或维护任务依赖、调度实例和统一运维状态。
5. 把 `datatask.Task` 当成完整业务配置真身。

执行要求：

1. 同步执行必须通过 `apps.executors.base.ExecutorFactory`。
2. 数据源运行时连接信息只能通过统一连接上下文构造，不允许手写连接参数拼接。
3. 手动执行未发布任务时，可以创建运行态平台任务，但不得自动开启调度。
4. 只有显式发布后，当前业务配置快照才能进入 `datatask.Task` 并参与 cron 或依赖调度。

后续优先补齐：

1. 发布前校验统一走 executor 的 `validate()`。
2. 同步任务的 source/target 连接失效提示继续保持在业务模块，但执行状态仍归一到 `TaskInstance`。

### 4.3 `datadev`

`datadev` 负责数据开发阶段的业务定义。

应该负责：

1. 脚本定义：`DataDevScript`。
2. 脚本版本、草稿、发布版本和回滚。
3. 模型定义：`DataDevModel` 与 `DataDevModelField`。
4. SQL/Python 作业调试入口。
5. 模型建表或建模执行入口。
6. 发布脚本任务到任务中心。
7. 开发态治理卡点，例如负责人、表注释、字段注释、目标层级。
8. 通过 source handler 向 `datatask` 暴露脚本任务加载、执行和治理字段回写能力。

不应该负责：

1. 自行维护私有执行历史表。
2. 自行连接外部数据库执行 SQL。
3. 自行实现 Spark/Hive/DataX/MVP 执行器。
4. 把版本中心、审批流、冻结版本中心提前做成当前阶段主线。
5. 把字段级血缘、全量质量规则一次性压入当前开发主线。

执行要求：

1. 绑定数据源的 SQL 查询必须通过 `apps.dbutils.factory.get_executor(...).execute_query(...)`。
2. Spark/Hive/建模执行必须通过 `apps.executors.base.ExecutorFactory`。
3. MVP 预演类能力后续应沉淀到 `apps.executors`，业务模块只传入执行计划。
4. 脚本调试执行和平台执行都必须创建 `TaskInstance`。
5. 模型定义、保存和直接建表不具备任务属性；需要调度编排时应先生成或绑定加工作业，再发布脚本任务。
6. 发布任务时，`datadev` 只发布当前脚本定义快照，不把完整业务真身迁移到 `datatask`。

后续优先补齐：

1. 把当前业务模块内的 MVP 预演执行逻辑沉淀为正式 executor。
2. 把建模 SQL 生成保留在业务层，建表动作继续只走 executor，并逐步复用脚本执行链路。
3. 继续保持脚本版本与平台运行快照的边界清晰。

### 4.4 `datatask`

`datatask` 负责统一任务运维阶段。

应该负责：

1. `Task` 平台镜像。
2. `TaskDependency` 任务依赖。
3. `TaskInstance` 唯一执行实例中心。
4. 统一任务执行入口：`TaskService.execute_task`。
5. 统一执行实例创建、运行中标记、完成归档。
6. source handler 注册表与执行返回 envelope 归一化。
7. 调度类型、cron 表达式、依赖触发、实例列表和任务详情。

不应该负责：

1. 直接理解 `datasource`、`dataintegration`、`datadev` 的业务字段。
2. 直接持有完整业务任务定义。
3. 直接调用业务模块内部实现而绕过 source handler。
4. 直接执行数据库查询或引擎任务。
5. 为每类业务任务增加私有字段分支。

执行要求：

1. 新来源模块接入必须注册 `SourceHandler`。
2. 来源模块执行返回必须是 `{ok,msg,data}` envelope。
3. handler 抛异常时必须稳定降级为失败响应并记录日志。
4. 调度执行只调用 `TaskService.execute_task`，不直接调业务模块函数。

### 4.5 `executors`

`executors` 负责任务级执行。

应该负责：

1. DataX、Spark SQL、Hive、MVP/Mock 等任务执行器。
2. 执行器注册与工厂创建。
3. 任务执行前校验：`validate()`。
4. 统一执行结果返回结构。
5. 执行器生命周期与资源释放。

不应该负责：

1. 保存业务任务定义。
2. 保存 `TaskInstance`。
3. 判断任务是否发布、是否调度、是否归属某业务模块。
4. 写业务模块模型字段。

新增执行能力时，默认先问：这是数据库级查询能力，还是任务级执行能力。任务级执行能力必须落到 `apps.executors`。

### 4.6 `dbutils`

`dbutils` 负责数据库级访问能力。

应该负责：

1. 外部数据库连接创建与关闭。
2. 查询类 SQL 执行。
3. 分页 SQL 适配。
4. 库列表、表列表、字段列表、表结构和表信息探查。
5. SQL 安全基础校验。

不应该负责：

1. 保存业务任务定义。
2. 创建或完成 `TaskInstance`。
3. 处理调度、依赖、发布、治理字段。
4. 直接写 `dataasset`、`datadev`、`dataintegration` 业务模型。

新增数据库能力时，默认先落到 `apps.dbutils`，再由业务模块通过 facade 或 helper 调用。

## 5. 标准调用链

### 5.1 调试执行

```text
业务模块页面/API
  -> 读取业务定义
  -> 构造 runtime_config / 执行计划
  -> ensure 或同步 datatask.Task 镜像
  -> TaskService.execute_task 或模块执行入口
  -> source handler
  -> executors/dbutils
  -> TaskService.finalize_instance
  -> 返回 TaskInstance 摘要
```

调试执行可以不启用调度，但必须进入 `TaskInstance`。

### 5.2 发布到任务中心

```text
业务模块发布入口
  -> 校验业务定义完整性
  -> 构造业务配置快照
  -> TaskService.upsert_source_task
  -> datatask.Task 保存来源锚点、治理字段和发布快照
```

发布动作只同步平台镜像，不迁移业务真身。

### 5.3 调度执行

```text
datatask.scheduler
  -> 命中到期 Task
  -> TaskService.execute_task
  -> get_source_handler(source_module)
  -> handler.load_source_record(source_record_id)
  -> handler.execute_task(...)
  -> executors/dbutils
  -> TaskInstance 完成
```

调度执行不得直接 import 业务模块执行函数。

## 6. 禁止事项

后续代码评审中，以下情况默认需要退回：

1. 在 `datasource`、`dataintegration`、`datadev` 中直接引入外部数据库驱动并连接数据库。
2. 在业务模块中新增私有执行记录表。
3. 在 `datatask.Task` 中新增大量业务字段，试图替代业务模块真源。
4. 绕过 `TaskService.create_task_instance` / `finalize_instance` 记录执行结果。
5. 绕过 `SourceHandler` 让 `datatask` 直接调用业务模块内部函数。
6. 新增执行引擎时不注册到 `apps.executors`。
7. 新增数据库探查或查询能力时不落到 `apps.dbutils`。
8. 让 `dataasset` 或 `dataservice` 反向成为前三个业务模块的流程入口。
9. 为了页面展示方便新增第二套状态字段、第二套实例表或第二套执行日志。

## 7. 开发前检查清单

涉及 `datasource`、`dataintegration`、`datadev`、`datatask`、`executors`、`dbutils` 的需求，开工前必须回答：

1. 本次改动的业务真源在哪个模块？
2. 是否需要创建、修改或发布 `datatask.Task` 镜像？
3. 是否会产生执行记录？如果会，是否进入 `TaskInstance`？
4. 是否涉及外部数据库连接或查询？如果会，是否走 `dbutils`？
5. 是否涉及任务级执行？如果会，是否走 `executors`？
6. 是否需要新增 source handler 或扩展已有 handler？
7. 是否存在业务模块直接承担执行器职责的代码？
8. 是否需要同步菜单、前端入口、测试、文档和 changelog？

## 8. 验收口径

一个改动可以进入主干前，至少满足：

1. 业务定义仍留在对应业务模块。
2. 平台任务只作为镜像和调度索引。
3. 执行历史只进入 `TaskInstance`。
4. 任务执行只通过 source handler 分发。
5. 数据库查询和库表探查只通过 `dbutils`。
6. 任务级执行只通过 `executors`。
7. 前端页面看到的执行结果与任务运维看到的执行实例来自同一批数据。
8. 文档入口、当前状态和 changelog 已同步更新。

## 9. 一句话结论

后续开发必须坚持：**业务模块定义“要做什么”，`datatask` 管“什么时候跑、谁在跑、跑成什么样”，`executors/dbutils` 负责“怎么实际连接和执行”。**
