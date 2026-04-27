# 当前状态（只保留现状）

本文件只记录当前主干的真实状态，不再保留过程型历史。

## 当前架构基线

1. 平台按 ADR-011 收敛为五阶段职责模型：
   - `datasource`：Connection & Discovery
   - `dataintegration`：Data Integration
   - `datadev`：Data Development
   - `datatask`：Orchestration & DataOps
   - `dataasset`：Assetization & Service
2. 平台任务边界按 ADR-012 执行：`datasource`、`dataintegration`、`datadev` 各自保留正式任务定义，`datatask.Task` 作为平台镜像，`datatask.TaskInstance` 作为唯一执行记录中心。
3. `datasource`、`dataintegration` 与 `datadev` 已通过各自 `task_source.py` / source handler 接入 `datatask`，统一任务中心只保留任务内核与来源分发协议。
4. 数据源连接上下文统一复用 `apps.datasource.executor_info`。

## 当前产品口径

1. `datasource` 当前只保留：
   - 数据源 CRUD
   - 连通性测试
   - 数据库 / 表 / 字段发现
   - 单表采集到数据资产
   - 整库异步采集到数据资产
2. `datasource` 已移除 snapshot 与 `DatabaseAssetSyncRun`；当前采集运行记录统一进入 `datatask.TaskInstance`，`datasource` 内只保留正式采集任务定义 `DataSourceCollectionTask`。
3. `dataintegration` 已改为直接填写 `sourceDatabaseName` / `sourceTableName`。
4. 删除数据源不会再被历史集成任务阻塞；若数据源被删，相关集成任务需重新绑定后才能继续执行，自动生成的源数据采集任务会一并回收。
5. `datadev` 当前只保留 `DataDevScript` / `DataDevModel` 作为业务任务定义，脚本调试执行、建模执行与历史执行记录统一进入 `datatask.TaskInstance`，不再保留 `DataDevScriptExecution` 私有执行表。
6. 登录链路当前包含验证码校验与失败次数限流。
7. `dataasset` 已建立 `facades/` 公开边界，元数据采集与规范资产同步默认通过 facade 进入，不再把 `services.py` 视为跨模块公共入口。
8. 任务运维执行记录页与任务详情页当前会直接展示 `datasource.collection` 的执行结果、失败原因与采集进度摘要；存在进行中实例时页面会自动轮询刷新状态。
9. 任务运维执行记录列表当前采用“任务对象 / 实例与触发 / 状态 / 执行时间 / 执行情况”的组合列展示，减少原始字段平铺，便于运维快速扫读。
10. 执行记录列表中的“执行情况”列当前默认压缩为紧凑单行摘要，错误信息超长时省略显示并通过悬停 tooltip 查看完整内容，避免长文案把整行高度撑开。

## 当前文档口径

1. `docs/README.md` 是统一文档入口。
2. `docs/changelog.md` 只保留近期有效变更摘要。
3. 历史信息统一进入 `docs/archive/`，不再继续堆在状态页与 README 中。
