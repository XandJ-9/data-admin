# 当前状态（只保留现状）

本文件只记录当前主干的真实状态，不再保留过程型历史。

## 当前最高优先级

1. 当前开发最优先要解决的事情，已明确收敛为“业务任务定义真源 + `datatask/TaskInstance` 统一任务运维纳管”。
2. 未来 4 到 6 周的开发顺序纠偏方案，统一以 `docs/developments/development-priority-correction-2026-04-30.md` 为执行口径。
3. 在该阶段完成前，不把任务发布、独立快照、冻结版本、复杂审批流、全量资产治理体系作为主线验收标准。
4. 模块优先级当前固定为：`datasource / dataintegration / datadev / datatask` 第一优先级，`monitor / system` 第二优先级，`dataasset / dataservice` 第三优先级。

## 当前架构基线

1. 平台按 ADR-011 收敛为五阶段职责模型：
   - `datasource`：Connection & Discovery
   - `dataintegration`：Data Integration
   - `datadev`：Data Development
   - `datatask`：Orchestration & DataOps
   - `dataasset`：Assetization & Service
2. 平台任务边界按 ADR-012 执行：`datasource`、`dataintegration`、`datadev` 各自保留正式任务定义，`datatask.Task` 作为平台镜像，`datatask.TaskInstance` 作为唯一执行记录中心。
3. `datasource`、`dataintegration` 与 `datadev` 已通过各自 source handler 接入 `datatask`，统一任务中心只保留任务内核与来源分发协议；其中 `datasource` 当前已将原 `task_source.py` 收敛并更名为 `task_handler.py`。
4. `datatask` 当前通过 source handler / registry 分发来源模块执行能力；调度执行优先基于 `datatask.Task.task_config` 发布快照运行，不再默认回落到业务任务 live 配置作为执行事实来源。
5. 数据源连接上下文统一复用 `apps.datasource.executor_info`。
6. `dataservice` 已注册到 Django `INSTALLED_APPS` 并挂载到 `data-api/dataservice/`，数据服务前后端链路现以该入口作为唯一后端访问前缀。

## 当前产品口径

1. `datasource` 当前只保留：
   - 数据源 CRUD
   - 连通性测试
   - 数据库 / 表 / 字段发现
   - 单表采集到数据资产
   - 整库异步采集到数据资产
2. `datasource` 模块首页当前已收敛为轻量入口页：只保留连接概览与当前关注的数据源，不再在首页同时堆叠流程说明、快捷入口区、能力清单与多块重复列表。
3. `datasource` 已移除 snapshot 与 `DatabaseAssetSyncRun`；当前采集运行记录统一进入 `datatask.TaskInstance`，`datasource` 内只保留正式采集任务定义 `DataSourceCollectionTask`，且采集任务定义当前不再承载 `schedule_type`、`cron_expression`、`task_config` 等调度或平台快照字段。
4. `datasource` 当前已完成采集链路职责收敛：`collectors.py` 只保留数据发现与元数据采集动作，任务纳管、执行分发、整库采集运行时与僵尸实例恢复统一收敛到 `task_handler.py`。
5. `datasource` 详情页返回列表当前统一直接跳转 `/datasource/list`，不再依赖列表路由名回跳，避免菜单/动态路由状态失配时按钮报错。
6. `dataintegration` 已改为直接填写 `sourceDatabaseName` / `sourceTableName`。
7. 删除数据源不会再被历史集成任务阻塞；若数据源被删，相关集成任务需重新绑定后才能继续执行，自动生成的源数据采集任务会一并回收。
8. `datadev` 当前只保留 `DataDevScript` / `DataDevModel` 作为业务任务定义，脚本调试执行、建模执行与历史执行记录统一进入 `datatask.TaskInstance`，不再保留 `DataDevScriptExecution` 私有执行表。
9. 登录链路当前包含验证码校验与失败次数限流。
10. `dataasset` 已建立 `facades/` 公开边界，元数据采集与规范资产同步默认通过 facade 进入，不再把 `services.py` 视为跨模块公共入口。
11. 任务运维执行记录页与任务详情页当前会直接展示 `datasource.collection` 的执行结果、失败原因与采集进度摘要；存在进行中实例时页面会自动轮询刷新状态。
12. `datasource.collection` 的僵尸实例纠偏当前由 `datasource` 通过 source handler 注册后台清理钩子给 `datatask.scheduler`，任务运维页与任务详情页的 GET 读取链路不再执行失联恢复或写数据库。
13. 任务运维执行记录列表当前采用“任务对象 / 实例与触发 / 状态 / 执行时间 / 执行情况”的组合列展示，减少原始字段平铺，便于运维快速扫读。
14. 执行记录列表中的“执行情况”列当前默认压缩为紧凑单行摘要，错误信息超长时省略显示并通过悬停 tooltip 查看完整内容，避免长文案把整行高度撑开。
15. 数据服务接口执行弹窗当前统一通过 `/dataservice/interface-info/{id}/export` 导出结果，不再使用不存在的 `/export-data` 路径。
16. `dataservice` 当前已补齐面向前端调用面的集成回归：`query`、`query-log`、`interface-info`、`interface-field`、`report-info` 及运行时导入导出相关入口均通过项目根路由实测覆盖。
17. 报表与接口关联关系当前在更新和删除前会清理历史已删除重复记录，避免同一报表重复编辑后再删除时触发软删除唯一约束冲突。
18. `dataservice` 的前端新增/更新接口当前会显式拦截重复 `interfaceCode` 与 `reportCode`，不再沿用通用基类的“按唯一键复用旧记录”行为，也不会把重复更新直接放到数据库唯一约束层报错。
19. `dataintegration` 当前已拆分为“模块首页 + 任务列表”两个正式菜单入口：模块首页只承载任务规模、焦点任务与导航入口，筛选、执行、详情抽屉与执行记录统一收敛到“任务列表”页面，不再把总览和工作台堆在同一页面；首页视觉样式也已收敛到和 `dataasset`、`dataservice` 一致的浅色模块首页风格。
20. 系统菜单管理页当前已修正“修改菜单”表单回填逻辑：菜单详情会先与默认表单合并并做字段归一化，菜单树加载失败也会被新增/修改入口正确兜底，避免显示状态、菜单状态等字段展示不全或产生未处理异常。
21. `dataintegration` 当前改为“保存业务配置”和“发布到任务中心”分离：创建/编辑任务不再自动进入 `datatask` 调度，只有在数据集成详情页手动点击发布后，当前配置快照才会同步到 `datatask.Task` 并参与 cron 调度；未发布时手动执行仍会产生统一 `TaskInstance` 记录，但不会自动开启调度。
22. `datatask` 当前已将任务治理更新入口收敛到 `TaskService.update_task_governance`：`TaskViewSet.update` 不再直接拼装状态、调度与来源快照同步字段，统一由 service 承接，相关 `apps.datatask` 回归测试当前通过。
23. `datatask` 当前已建立发布快照统一边界：`TaskService.get_published_snapshot` / `build_task_config_payload` 作为唯一快照读写入口，`datasource`、`dataintegration`、`datadev` 执行链路统一优先读取发布快照，旧 `task_config` 结构保持兼容回退。
24. `datatask` 当前已收敛 `SourceHandler` 契约：来源执行返回统一采用 `{ok,msg,data}` envelope，并由 `TaskService.execute_task` 统一归一化；当来源模块返回结构异常时，任务中心会稳定降级为失败响应而不是抛出运行时错误。
25. `docs/architecture/datatask-architecture-review-2026-04-29.md` 与 `ADR-010` 当前已完成时效性对齐：专项评审稿新增“已落实/待落实”收敛进度，`ADR-010` 中 `datasource` 接入状态补充了 2026-04-30 的阶段说明，避免历史决策描述与主干实现口径冲突。
26. `initdata` 当前菜单种子继续保留 `/datadev` 与 `/datatask` 作为正式业务根菜单，同时显式停用历史 `/data-orchestration` 入口，菜单回归测试已按该现状对齐。
27. 前端当前已清理未接入后端的遗留断链入口：移除 `/register` 静态路由，以及 monitor 的 `job / jobLog / logininfor` 与 `tool/gen` 相关页面和 API 封装，避免保留不可用前台代码。
28. `dataasset` 当前已开始按“`asset*` 为主、`meta-*` 兼容保留”的方向收口：资产首页、元数据浏览页和血缘页的表选项都改为优先消费 `asset / asset-column`，同时 `asset*` 已补齐 legacy 时间过滤和表/字段写入能力。
29. 前端当前已进一步清理未挂载后端的历史 API 封装：移除 `task-monitor`、`datataskmonitor` 与 `datastudio` 相关请求文件，避免重新引入不可用调用面。
30. 前端构建脚本当前同时支持 `pnpm build` 与 `pnpm build:prod`，两者均执行生产构建，减少常规构建命令与项目脚本不一致导致的误用。
31. `datatask` 当前在 source handler 执行抛异常时会稳定返回 `{ok:false,msg,data:null}` 失败 envelope 并记录服务端日志，不再让来源模块异常直接冒泡成任务中心 500。
32. 通用 `BaseViewSet.perform_create` 当前默认禁止按主键或唯一字段静默复用旧记录；如确需兼容旧式 create-upsert，必须由子类显式开启 `create_reuse_existing`。
33. `datadev` 模块首页当前已收敛到与 `dataasset`、`dataservice`、`dataintegration` 一致的浅色模块首页风格：只保留开发规模、核心入口、推荐流程和近期加工作业，不再使用独立渐变营销式首页。

## 当前文档口径

1. `docs/README.md` 是统一文档入口。
2. `docs/changelog.md` 只保留近期有效变更摘要。
3. 历史信息统一进入 `docs/archive/`，不再继续堆在状态页与 README 中。
4. `docs/architecture/datatask-architecture-review-2026-04-29.md` 已记录本轮 `datatask` 专项评审结论，当前明确后续收敛方向为“`Task` 仅承载发布纳管关系与调度索引，完整业务定义继续留在来源模块；如需冻结发布版本，再由独立快照层承接”。
5. `docs/architecture/platform-target-architecture-2026-04-30.md` 已新增平台目标架构图与模块职责图；当前阶段口径已进一步收敛为“先完成业务任务定义真源 + `datatask/TaskInstance` 统一纳管”，暂不把任务发布、独立快照和版本冻结作为当前主线交付。
6. `docs/developments/development-priority-correction-2026-04-30.md` 已新增开发顺序纠偏方案，并已提升为当前文档入口中的优先阅读项，用于约束未来 4 到 6 周的开发顺序、非目标范围和模块优先级。
7. 项目根 README、前后端 README 与前端开发规范当前已完成实现口径校准：`datasource` 明确保留采集到资产能力，前端免登录白名单明确仅保留 `/login`。
8. `docs/adr/README.md` 当前已按新编写规则重新分为“当前基线 / 背景决策 / 历史阶段口径 / 已删除旧 ADR”；ADR-006、ADR-008、ADR-009、ADR-010 已标注部分被 ADR-012 与当前主干实现覆盖，完全对应已下线 `apps.dataetl` 的 ADR-002 已删除。
