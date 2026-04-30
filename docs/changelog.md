# 版本变更日志（近期）

说明：本文件仅保留近期有效变更摘要，更早历史见 `docs/archive/`。

## [v1.4.86] - 2026-04-30

- [Refactor] `apps.datasource.task_source` 已正式更名为 `apps.datasource.task_handler`，`AppConfig.ready()`、视图与测试引用已同步切换，不再保留 datasource 侧兼容别名。
- [Refactor] `datasource` 当前已完成采集职责收敛：`collectors.py` 仅保留数据发现与元数据采集动作，任务纳管、执行分发、整库采集运行时与僵尸实例恢复统一下沉到 `task_handler.py`。
- [Test] `uv run manage.py test apps.datasource` 当前 22 条测试通过，覆盖采集定义同步、单表采集、整库采集、快照优先执行与删除回收链路。

## [v1.4.85] - 2026-04-30

- [Refactor] `datasource.DataSourceCollectionTask` 已去除 `schedule_type`、`cron_expression`、`task_config` 字段，明确当前阶段该模型只表达采集任务业务定义，不再混入调度语义与平台快照语义。
- [Refactor] `apps.datasource.task_source` 已同步收窄：采集任务同步到 `datatask` 时只携带采集定义快照，不再把 datasource 侧调度字段与平台治理字段双向回写。
- [Refactor] `datasource` 新增字段删除前的数据保留迁移：历史采集任务上的调度配置与扩展配置会先转存到 `datatask.Task`，避免本轮模型收敛直接丢失既有数据。
- [Test] `apps.datasource` 相关回归已同步调整为围绕“定义真源 + 实例纳管”校验，不再断言 datasource 侧保留调度字段。

## [v1.4.84] - 2026-04-30

- [Docs] 已新增 `docs/developments/development-priority-correction-2026-04-30.md`，正式给出未来 4 到 6 周的开发顺序纠偏方案，逐阶段明确“只做什么 / 不做什么 / 完成标志 / 风险”。
- [Docs] 当前开发最高优先级已明确写入 `docs/requirements/active_tasks.md`：先完成业务任务定义真源与 `datatask/TaskInstance` 统一任务运维纳管，不再把任务发布、独立快照、冻结版本等能力作为当前主线验收标准。
- [Docs] `docs/README.md` 已把开发顺序纠偏方案提升到“当前先看”，用于约束近期开发顺序，避免主线再次漂移。

## [v1.4.83] - 2026-04-30

- [Docs] 已新增平台目标架构文档，基于当前项目目录、ADR-010/011/012 与主干现状整理出完整的平台目标架构图、模块职责图、目标职责矩阵与主链路示意。
- [Docs] `docs/architecture/README.md` 已同步补充该文档索引与用途说明，便于后续方案评审时快速定位。
- [Docs] `docs/requirements/active_tasks.md` 已同步登记该架构蓝图文档，明确其作为当前平台目标沟通稿的用途。
- [Docs] 平台目标架构文档已按当前阶段重新收敛口径：先确保业务任务定义真源与统一任务运维纳管，暂不把任务发布、独立快照与版本冻结作为当前主线交付。

## [v1.4.82] - 2026-04-30

- [Docs] `datatask` 专项评审稿已补充截至 2026-04-30 的“已落实/待落实”收敛进度，明确当前代码已完成的治理入口收敛、发布快照边界与 handler 协议增强，以及仍待推进的主表字段最小化与独立快照承载。
- [Docs] `ADR-010` 中关于 `datasource` 暂不接入任务中心的阶段性条目已追加时效性说明，明确该描述属于制定当时前提，当前主干以 `DataSourceCollectionTask + source handler + TaskInstance` 口径运行。

## [v1.4.81] - 2026-04-30

- [Refactor] `datatask` 已强化 source handler 协议：新增 `ExecuteTaskResult` 统一执行返回类型，并在任务中心执行入口统一归一化来源返回结构，收敛跨模块执行契约。
- [Refactor] `datasource`、`dataintegration`、`datadev` 平台执行函数已补齐统一返回类型标注，降低来源模块接入时的隐式约定成本。
- [Test] 已新增“来源返回结构异常时任务中心归一化失败响应”的回归用例，并完成 `apps.datatask`、`apps.datasource`、`apps.dataintegration`、`apps.datadev` 共 94 条测试通过。

## [v1.4.80] - 2026-04-29

- [Refactor] `datatask` 已新增发布快照统一入口：`TaskService.get_published_snapshot` 与 `TaskService.build_task_config_payload`，并在 `upsert_source_task`、依赖调度切换与治理更新链路中统一使用，形成“治理字段 + 发布快照”边界。
- [Refactor] `datasource`、`dataintegration`、`datadev` 的执行读取链路已统一优先消费发布快照，不再直接散读 `Task.task_config` 顶层字段；同时保持旧结构回退兼容。
- [Test] 已新增快照兼容回归，并完成 `apps.datatask`、`apps.datasource`、`apps.dataintegration`、`apps.datadev` 共 93 条测试通过。

## [v1.4.79] - 2026-04-29

- [Refactor] `datatask` 已把任务治理更新逻辑从 `TaskViewSet.update` 下沉到 `TaskService.update_task_governance`，状态、调度字段与来源快照回写统一通过 service 入口处理，避免 View 层继续承载领域规则编排。
- [Test] 已新增 `TaskService.update_task_governance` 回归用例，覆盖“有变更触发来源快照同步”“无变更跳过同步”“仅更新 cronExpression”三个治理分支；`uv run manage.py test apps.datatask` 当前 27 条测试通过。

## [v1.4.78] - 2026-04-29

- [Docs] 已新增 `datatask` 模块专项评审稿，明确当前结论：`Task` 不应继续承担完整业务任务定义，但也不能收缩成只有业务任务 ID 的空壳引用；更合理的目标是只保留已发布任务的纳管关系与调度索引。
- [Docs] 已同步记录调度设计约束：调度服务应基于 `datatask` 自身索引先粗筛“已发布、启用、当前到点”的任务，再按命中结果读取发布快照或来源模块定义执行，避免调度周期退化为跨模块逐条回源扫描。

## [v1.4.77] - 2026-04-29

- [Refactor] `dataintegration` 当前已改为显式发布后才进入 `datatask` 调度：创建和编辑任务不再自动同步任务中心镜像，必须在数据集成详情页手动点击发布，当前配置快照才会进入 `datatask.Task` 并参与 cron 调度。
- [Refactor] `dataintegration` 的手动执行当前仍会统一写入 `datatask.TaskInstance`，但未发布任务只会创建运行态手动载体，不会因为一次手动执行就自动开启任务中心调度。
- [Fix] 任务中心当前已拦截未发布 `dataintegration.task` 直接切换为 cron 调度的操作，避免绕过数据集成模块的显式发布入口。
- [Test] 已新增发布门禁回归，覆盖“创建不自动发布、发布后才同步、未发布执行不进 cron、任务中心禁止未发布开 cron”等场景，`apps.dataintegration` 与 `apps.datatask` 相关测试当前通过。

## [v1.4.76] - 2026-04-28

- [Refactor] `datatask` 调度执行当前优先基于 `Task.task_config` 发布快照驱动 `dataintegration` 与 `datasource.collection`，不再默认读取业务任务 live 配置作为执行事实来源。
- [Refactor] `datasource.collection` 的失联实例恢复已从任务详情与执行记录 GET 读取链路移出，统一改由 `TaskSchedulerService` 通过 source handler 后台清理钩子收敛处理。
- [Fix] `dataintegration` 当快照中显式绑定的数据源已失效时，当前会直接返回重新绑定提示，不再静默回退到 live 数据源导致快照参数与真实连接错配。
- [Test] 已新增 27 条聚焦回归中的快照执行、后台 stale cleanup 与 GET 只读行为验证，`apps.datatask`、`apps.datasource`、`apps.dataintegration` 相关测试当前通过。

## [v1.4.75] - 2026-04-28

- [Refactor] `datatask` 已移除对 `datasource.collectors` 的直接反向依赖；任务运维实例列表与任务详情中的实例读取，当前统一通过 `source handler / registry` 调用来源模块注册的实例归一化能力。
- [Refactor] `datasource.collection` 当前已通过 `task_source.py` 向 `datatask` 注册执行记录纠偏 / 失联恢复能力，数据源采集实例的僵尸状态不再由平台内核写死特判分支处理。
- [Docs] 已新增后端现状架构评审稿，基于当前主要类与运行链输出代码级实际架构图，并同步补充 ADR-012 对“实例归一化也必须通过 source handler 暴露”的边界说明。
- [Test] 已新增 registry 化实例归一化回归，并完成 `apps.datatask`、`apps.datasource` 后端测试通过，确认新的来源注册链路未破坏现有任务运维与数据源采集行为。

## [v1.4.74] - 2026-04-27

- [Fix] 系统菜单管理页已修正“修改菜单”时的表单回填逻辑，菜单详情会先与默认值合并并做字段归一化，显示状态、菜单状态及布尔开关类字段不再因缺省值或异步链路问题出现展示不全。
- [Fix] 菜单管理页的新增/修改入口已补齐菜单树加载失败的异常兜底，避免 treeselect 请求失败时产生未处理 Promise rejection 或重复报错。
- [UX] `dataintegration` 前端界面已按模块首页风格重构为“模块首页 + 任务列表”双入口，首页只保留规模感知、焦点任务与导航，不再把总览与任务工作台堆在同一页。
- [UX] 数据集成菜单种子已新增 `DataIntegrationHome` 首页入口，并把 `DataIntegrationTask` 调整为独立任务列表页；新建页和详情页当前会高亮回到 `/data-integration/task`，避免编辑链路丢失菜单上下文。
- [UX] 数据集成首页的配色、圆角和卡片层级已进一步收敛到 `dataasset` / `dataservice` 的统一模块首页风格，不再出现偏冷色、偏厚重的单独视觉语言。
- [Test] 已新增 `initdata` 菜单回归，确认数据集成会种出“模块首页 + 任务列表”两个入口，且详情/新建页继续绑定任务列表高亮；前端生产构建已通过。

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
