# 版本变更日志（近期）

说明：本文件仅保留近期有效变更摘要，更早历史见 `docs/archive/`。

## [v1.4.73] - 2026-04-27

- [Fix] `dataservice` 已补充 Django 应用注册与 `data-api/dataservice/` 根路由挂载，前端数据服务页面不再因模块未接入主路由而整体打不通。
- [Fix] 数据服务接口执行弹窗的导出链路已改为调用后端现有 `/dataservice/interface-info/{id}/export` 接口，并按响应头保存真实文件名，不再请求不存在的 `/export-data` 路径。
- [Fix] 报表接口关联关系在更新与删除前会清理历史已删除重复记录，避免前端多次编辑报表后再删除时触发软删除唯一约束冲突。
- [Fix] `dataservice` 的前端新增/更新接口已补充重复编码校验，`interface-info` 与 `report-info` 在重复 `interfaceCode` / `reportCode` 的创建和修改场景下会明确返回校验错误，不再静默覆盖旧记录或把唯一约束冲突直接抛成 500。
- [Test] 已新增覆盖前端数据服务调用面的集成回归，`uv run manage.py test apps.dataservice` 当前 27 个测试通过，覆盖查询、日志、接口、字段、导入导出与报表相关入口，并补齐报表关联软删除与重复编码防回归用例。

## [v1.4.72] - 2026-04-26

- [UX] 任务运维执行记录列表已重排为更适合运维扫读的组合列，按“任务对象 / 实例与触发 / 状态 / 执行时间 / 执行情况”集中呈现，不再把来源、实例号、触发方式、执行器和耗时拆成过多原始列。
- [UX] 执行记录列表已补充触发方式标签、任务来源标签、执行器名称映射与更友好的耗时格式，数据源采集、集成任务和加工作业实例的展示口径更统一。
- [UX] 执行记录列表的“执行情况”列已改为紧凑摘要展示，超长结果与错误信息默认单行省略并支持悬停查看完整内容，避免单条记录把表格行高明显撑大。

## [v1.4.71] - 2026-04-26

- [Fix] 任务运维执行记录接口已补充 `taskType`、`sourceModule` 与 `sourceRecordId` 字段，前端可直接区分 `datasource.collection` 等来源实例。
- [UX] 任务运维执行记录页与任务详情页已展示执行结果摘要、失败原因和采集进度，数据源采集任务的成功/失败情况不再只能靠数据源详情页观察。
- [UX] 当执行记录中存在 `pending` / `running` 实例时，任务运维页会自动轮询刷新，异步整库采集可在页面内直接看到状态从执行中收敛到成功或失败。

## [v1.4.70] - 2026-04-26

- [Docs] 已新增 `ADR-012-统一任务定义与执行实例边界规范`，正式固化 `datasource` / `dataintegration` / `datadev` 与 `datatask` 的任务定义、平台镜像和执行实例边界。
- [Docs] 文档入口已将 `ADR-012` 提升为协同开发优先阅读项，后续涉及任务模型和运行链路的设计统一以 `ADR-010`、`ADR-011`、`ADR-012` 三份 ADR 为基线。

## [v1.4.69] - 2026-04-26

- [Refactor] `datadev` 已删除私有执行记录模型 `DataDevScriptExecution`，脚本调试执行与建模执行的运行历史统一进入 `datatask.TaskInstance`。
- [Refactor] `datadev` 脚本执行链路现统一先同步 `datadev.script -> datatask.Task`，再创建 `TaskInstance` 执行，不再允许脱离统一任务中心单独落一套执行实例。
- [Refactor] `datadev` 历史执行数据已通过迁移回填到 `TaskInstance` 后再删旧表，保留原执行状态、执行人、时间和结果摘要。

## [v1.4.68] - 2026-04-26

- [Refactor] `datasource` 已新增正式采集任务定义 `DataSourceCollectionTask`，单表采集与整库异步采集统一通过 `datasource.collection -> datatask.Task / TaskInstance` 执行，不再使用 `DatabaseAssetSyncRun`。
- [Refactor] 数据源采集历史已拆为“建新表 / 回填旧实例 / 删除旧表”三段迁移，历史整库采集记录会迁移到统一任务实例。
- [Fix] 删除数据源时会同步回收关联的 `datasource.collection` 任务并终止在跑采集实例，避免留下僵尸任务或后台继续写资产。
- [UX] 任务运维页已补充 `ASSET_COLLECTION` / `datasource.collection` 展示映射，任务详情可回跳到对应数据源详情。

## [v1.4.67] - 2026-04-25

- [Feat] `datasource` 发现链已恢复“单表采集到数据资产”能力：从数据源详情页选择源表后，可直接同步到 `dataasset` 的元数据模型与规范资产模型。
- [Refactor] 该采集入口继续遵循 `datasource` 负责连接与发现、`dataasset` facade 负责落库与资产同步的边界，不再回退到 snapshot / 采集任务模型。
- [Test] 已补充 `apps.datasource` 到 `apps.dataasset` 的单表采集回归，并完成后端检查、相关后端测试与前端生产构建。

## [v1.4.66] - 2026-04-25

- [Refactor] `apps.dataasset` 已新增 `facades/metadata_assets.py` 作为正式公开边界，统一承接元数据采集、命名空间 upsert 与规范资产同步。
- [Refactor] `dataasset` 视图与测试已切换到 facade 调用，不再直接依赖 `services.py` 作为外部入口。
- [Test] 已补齐 facade 提取后的 `apps.dataasset` 回归，确认元数据写入、规范资产同步与事务回滚行为保持稳定。

## [v1.4.65] - 2026-04-25

- [Docs] 已重写根 README、前后端 README、文档入口页与快速参考，删除历史漂移描述，只保留当前主干真实状态。
- [Docs] `docs/requirements/active_tasks.md` 已收敛为“当前状态页”，不再保留过程型里程碑堆叠。
- [Docs] 已移除长期失真的需求旧稿，后续状态与规范统一以 `docs/README.md`、ADR 与当前状态页为准。

## [v1.4.64] - 2026-04-25

- [Fix] `dataintegration` 对 `datasource` 的源/目标数据源引用已从 `PROTECT` 调整为可空解绑，删除无效数据源时不再被历史集成任务阻塞。
- [Fix] 当集成任务引用的数据源已被删除时，任务详情与列表继续保留，但执行与配置校验会明确提示“请重新绑定数据源后再执行”。
- [Test] 已补充数据源删除与集成任务解绑的回归测试，覆盖删除接口放行与缺绑定执行保护。

## [v1.4.63] - 2026-04-25

- [Refactor] `apps.datasource` 已移除 `SourceTableSnapshot`、`SourceColumnSnapshot` 与 `SourceMetadataCollectionTask`，当前阶段仅保留连接管理、连通性测试与库表字段探查能力。
- [Refactor] `dataintegration` 任务配置已改为直接填写 `sourceDatabaseName` / `sourceTableName`，不再依赖 `/dataintegration/task/source-tables` 与 snapshot 选择流程。
- [UX] 数据源首页、详情页、源数据查看页及资产元数据页已同步移除采集入口，避免继续暴露已下线的 snapshot/采集能力。
