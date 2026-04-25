# 版本变更日志（近期）

说明：本文件仅保留近期版本摘要，完整历史见归档文件。

## [v1.4.64] - 2026-04-25

- [Fix] `dataintegration` 对 `datasource` 的源/目标数据源引用已从 `PROTECT` 调整为可空解绑，删除无效数据源时不再被历史集成任务阻塞。
- [Fix] 当集成任务引用的数据源已被删除时，任务详情与列表继续保留，但执行与配置校验会明确提示“请重新绑定数据源后再执行”。
- [Test] 已补充数据源删除与集成任务解绑的回归测试，覆盖删除接口放行与缺绑定执行保护。

## [v1.4.63] - 2026-04-25

- [Refactor] `apps.datasource` 已移除 `SourceTableSnapshot`、`SourceColumnSnapshot` 与 `SourceMetadataCollectionTask`，当前阶段仅保留连接管理、连通性测试与库表字段探查能力。
- [Refactor] `dataintegration` 任务配置已改为直接填写 `sourceDatabaseName` / `sourceTableName`，不再依赖 `/dataintegration/task/source-tables` 与 snapshot 选择流程。
- [UX] 数据源首页、详情页、源数据查看页及资产元数据页已同步移除采集入口，避免继续暴露已下线的 snapshot/采集能力。

## [v1.4.62] - 2026-04-25

- [Refactor] `apps.datadev` 新增注册式 `task_source.py`，通过 `AppConfig.ready()` 接入统一任务中心。
- [Refactor] `datatask` 不再持有 datadev 的脚本/模型执行与回写分支，保留通用任务运行时与来源分发协议。
- [Refactor] datadev 脚本执行中的普通数据源上下文统一复用 `apps.datasource.executor_info`。

## [v1.4.61] - 2026-04-25

- [Refactor] `apps.dataintegration` 新增注册式 `task_source.py` 并接入统一任务中心。
- [Refactor] 数据集成任务生命周期与统一 `Task` 事务内同步，任务运维改动可回写集成任务。
- [Refactor] 删除 `DataIntegrationExecutionLog`，执行事实统一收敛到 `datatask.TaskInstance`。

## [v1.4.60] - 2026-04-25

- [Docs] 开发流程“主干稳定、短分支交付、单分支单目标”写入 `CLAUDE.md`。
- [Docs] `docs/developments/creating-modules.md` 与 `docs/developments/quick-reference.md` 补充分支命名、提交与交付规范。

## [v1.4.59] - 2026-04-25

- [UX] 数据源模块首页恢复“快捷查看源数据”入口。
- [Docs] `menu_data.json` 恢复独立“源数据查看”子菜单。

## [v1.4.58] - 2026-04-24

- [UX] 数据源查看入口曾收敛到详情页，后续已在 v1.4.59 调整为“双路径”。

## 历史归档

- 完整版本历史：`docs/archive/changelog-history-2026-04-25.md`
- 历史日志用于追溯，不作为当前决策依据。
