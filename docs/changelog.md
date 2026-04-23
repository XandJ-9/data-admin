# [v1.4.57] - 2026-04-23
- [Feature] 已按 ADR-011 重建 `apps.datasource` 后端模块，恢复数据源 CRUD、连通性测试、数据库/表/字段探查与 `/datasource/collection/*` 采集入口。
- [Feature] `datasource` 现新增源表快照、源字段快照与采集任务模型，Phase 1 原始元数据采集结果不再依赖已删除的 `dataasset` 实现暂存。
- [Compat] `backend/config/settings.py` 与 `backend/config/urls.py` 已临时收敛为仅注册当前仍存在的模块与新的 `datasource`，保证当前阶段后端可启动并通过检查。

# [v1.4.56] - 2026-04-23
- [Ops] `scripts/module_rebuild_guard.py` 默认扫描范围已扩展到 `backend/`、`frontend/src/`、`docs/`、`scripts/`、`deploy/` 和根目录说明文件，旧实现排查不再只停留在局部目录。
- [Ops] 短英文关键词现按边界匹配，避免误命中普通变量名或函数名片段，扫描结果更适合作为清场依据。
- [Docs] `README.md` 与 `docs/developments/creating-modules.md` 已将 `--fail-on-hits` 收敛为新模块开工前的默认扫描方式，并补充“删除后重新扫描直到无残留”的要求。

# [v1.4.55] - 2026-04-23
- [Feature] 新增 `scripts/module_rebuild_guard.py`，支持按模块名与阶段扫描后端、前端、菜单、文档中的历史实现候选。
- [Ops] 该脚本已支持 `--fail-on-hits` 作为新模块开工前的自动化拦截，也支持通过 `--delete ... --yes` 对已确认旧路径执行清场。
- [Docs] `README.md` 与 `docs/developments/creating-modules.md` 已补充脚本命令示例，正式收敛为“先扫描、后删除、再重建”的模块开发入口。

# [v1.4.54] - 2026-04-23
- [Docs] `CLAUDE.md` 已新增“新模块开发前置流程”，要求所有新模块开发先以 `ADR-011` 判断阶段归属，再检查项目内是否已有同职责旧实现。
- [Docs] `docs/developments/creating-modules.md` 已新增“先查旧实现、先删后建”的创建规范，要求后端、前端、菜单、测试与文档同步纳入替换范围。
- [Docs] 平台后续开发现默认遵循“旧实现清场后再重建”的模块交付方式，避免同职责双实现长期并存。

# [v1.4.53] - 2026-04-23
- [Docs] 新增 `ADR-011-平台五阶段职责划分规范`，正式固化数据平台 5 个阶段的目标、职责边界、交付物与越界约束。
- [Docs] 该 ADR 已规定后续需求评审、设计评审与跨模块开发需先明确阶段归属、上下游输入输出与治理嵌入点。
- [Docs] `docs/adr/README.md` 已补充 ADR-011 入口，便于后续作为统一规范引用。

# [v1.4.52] - 2026-04-22
- [Docs] 新增 `ADR-010-后端平台分层与模块职责重构`，正式定义 `datasource / dataintegration / datadev / datatask / dataasset` 在数据平台中的层级角色与职责边界。
- [Docs] `backend/README.md` 已同步收敛为新的分层表达与真实目录结构，明确 `datatask` 为平台内核、`dataasset` 为资产治理层。

# [v1.4.51] - 2026-04-22
- [Refactor] `apps.datatask` 已改为注册式任务来源分发，`dataintegration` 与 `datadev` 现通过 `task_source.py` + `AppConfig.ready()` 注册自己的任务快照回写与执行处理器。
- [Refactor] 已将数据源连接上下文统一收敛到 `apps.datasource.executor_info`，数据源探查、数据服务查询与数据开发脚本执行共用同一套“解密密码 + 解析参数”构建逻辑。
- [Refactor] 已新增 `apps.dataasset.facades.metadata_collection` 作为公开门面，`apps.datasource` 现通过 facade 使用采集任务与元数据落库能力，不再直接依赖 `dataasset` 内部实现。

# [v1.4.50] - 2026-04-22
- [Feature] 新增 `.claude/agents/data-governance-engineer.agent.md`，提供独立的“资深数据治理工程师”Agent 角色。
- [Docs] 新 Agent 已覆盖元数据治理、数据标准、数据质量、数据安全、数据资产与治理流程落地等核心职责。
- [Docs] 已明确该 Agent 的输出原则为“治理嵌入主流程、规则可机器校验、优先最小治理闭环”。

# [v1.4.49] - 2026-04-22
- [Refactor] 已将源数据探查与采集后端实现从 `apps.dataasset` 迁移到 `apps.datasource`，`collectors.py` 现归属数据源管理模块维护。
- [Feature] 数据源管理新增正式采集接口族：`/datasource/collection/databases|tables|columns|collect|collect-table|collect-async|collect-status|collect-cancel`。
- [Breaking] 已移除 `/dataasset/collection/*` 旧接口，前端数据源详情页与源数据查看页已统一改走 `datasource` 模块接口。

# [v1.4.48] - 2026-04-22
- [Bugfix] 修复 MySQL 数据源“测试连接成功但探查数据表失败”问题：`apps.dataasset` 探查与采集链路现会先解密已存储密码，再构建执行器连接信息。
- [Compat] 数据资产侧连接参数已统一按 JSON 解析，查看数据库、查看数据表和异步采集元数据使用同一套连接上下文，避免接口行为不一致。

# [v1.4.47] - 2026-04-22
- [Feature] 数据资产标准模型已从“纯源端表/字段”扩展为同时支持业务元数据与数仓元数据，新增资产分类、数仓分层、业务域、主题域、负责人、生命周期、安全等级等字段。
- [Compat] `MetaTable / MetaColumn` 与 `DataAsset / DataAssetColumn` 已保持双写同步，兼容元数据接口继续可用，同时支持新维度筛选。
- [UX] 元数据浏览页已新增业务域、数仓分层、字段角色、安全等级、标准编码、指标单位等展示与筛选能力。

# [v1.4.46] - 2026-04-22
- [Feature] 数据源管理模块已新增首页，首页聚焦“连接与发现”定位，补充连接规模、连通性与元数据衔接总览。
- [UX] 数据源列表已补充模块定位提示、详情入口和带上下文的源数据查看入口，并支持从首页直达新增数据源。
- [Ops] 数据源模块菜单默认入口已调整为模块首页，便于与数据集成、建模与加工、数据服务等模块保持一致的信息架构。

# [v1.4.45] - 2026-04-22
- [Refactor] 数据开发模块已按“建模与加工”主线收敛：`DataDevScript` 语义升级为加工作业，新增作业用途与目标模型绑定，目录树降级为兼容能力。
- [Feature] 加工作业已新增显式“发布到任务运维”动作，调试执行不再自动纳入统一任务；发布后会生成 Task 快照并直接跳转任务详情。
- [UX] 建模与加工首页、加工作业列表/详情、模型设计页和任务运维来源标签已同步更新，主路径明确为“先建模，再加工，后运维”。

# [v1.4.44] - 2026-04-20
- [Fix] 已修复脚本详情页翻转进入编辑态后 SQL 编辑器无法正常编辑的问题。
- [UX] 翻转卡片现仅允许当前可见面接收交互，并在进入编辑态后主动刷新并聚焦编辑器。

# [v1.4.43] - 2026-04-20
- [UX] 脚本详情页已调整为概览优先，列表进入后先展示脚本基本信息、版本与运维摘要，再按需翻转进入 SQL 编辑页。
- [UX] “开始编辑 SQL”等操作已收敛到版本与运维卡片，翻转后的编辑页仅保留返回与执行等最小动作。

# [v1.4.42] - 2026-04-20
- [UX] 脚本详情辅助面已去掉顶部头部区，避免重复展示标题、状态与独立按钮栏。
- [UX] 详情相关操作已合并到“版本与运维”卡片头部，页面层级更浅，干扰更少。

# [v1.4.41] - 2026-04-20
- [UX] 脚本详情页已调整为编辑优先，进入脚本后默认直接展示编辑器，详情治理信息退居翻转后的辅助面板。
- [UX] 编辑页顶部动作继续收敛为“查看详情 + 执行脚本”，避免脚本开发模式被展示型信息打断。

# [v1.4.40] - 2026-04-20
- [UX] 脚本详情页的开发模式已改为页面内翻转效果，点击后直接在同页背面进入编辑视图，不再弹出多面板开发窗口。
- [UX] 开发模式已收敛为单编辑页，仅保留返回和执行按钮，移除保存/发布/全屏/状态栏等附加信息。
- [Compat] 执行前会自动保存当前草稿版本，确保脚本运行内容与当前编辑内容保持一致。

# [v1.4.39] - 2026-04-20
- [UX] 脚本开发列表页已移除顶部说明与摘要卡片，页面收敛为更轻的“筛选 + 列表”结构。
- [UX] 脚本列表已取消方格卡片样式，改回标准表格浏览，降低视觉干扰并提升信息密度。
- [Ops] 当前环境已同步最新菜单数据，脚本详情隐藏路由和新的数据开发菜单结构已可直接生效。

# [v1.4.38] - 2026-04-20
- [UX] 数据开发“脚本开发”子菜单已重构为“列表页 → 详情页”两段式结构，`/datadev/ide` 不再同屏堆叠脚本列表与详情信息。
- [UX] 脚本列表已改为简洁方格卡片布局，保留检索、分页、新建与删除能力，同时减少常驻 IDE 带来的视觉干扰。
- [Compat] 脚本详情页继续复用既有开发模式弹窗、版本历史与执行记录链路，数据目录、任务运维等入口现已统一跳转到脚本详情页。

# 版本更新日志

本文件用于记录 Data Admin 项目的所有版本变更、修复与新特性。

# [v1.4.37] - 2026-04-19
- [UX] 数据开发脚本页已移除左侧资源树，改为“脚本列表 + 详情页”结构，浏览与管理脚本时不再被常驻 IDE 挤压视野。
- [UX] 脚本详情页右上角已新增【脚本开发模式】入口，脚本编写、保存、发布与执行调试统一收敛到弹窗式开发窗口。
- [Compat] 开发模式窗口继续复用现有执行结果、版本历史、执行记录与执行日志链路，Spark SQL / Hive 调试反馈保持不变。

# [v1.4.36] - 2026-04-19
- [Bugfix] 修复数据开发脚本执行日志缺失问题：Spark SQL / Hive 的原始 stdout/stderr 现已随执行结果返回前端，并写入执行记录摘要。
- [UX] 脚本开发页的“执行日志”区已可展示 Spark SQL 原始执行输出，不再只显示“开始执行 / 执行完成”这类摘要提示。

# [v1.4.35] - 2026-04-19
- [Bugfix] 修复数据开发 Spark SQL / Hive 脚本运行时的前端 10 秒超时问题，执行接口已改为单独放宽请求等待时间。
- [UX] 当脚本执行等待超时时，前端会明确提示“任务可能仍在后端运行，请到执行记录查看”，避免误判为立即失败。

# [v1.4.34] - 2026-04-19
- [UX] 数据开发目录已新增真实子菜单【开发首页】，父级默认进入 `/datadev/home`，不再直接落到脚本 IDE。
- [UX] 原“开发工作台”菜单已更名为【脚本开发】，开发首页负责分流进入脚本开发、数据目录、数据建模等功能。
- [UX] 开发首页已支持通过快捷入口直接跳转到脚本开发，并通过 `quickCreate` 参数直达 SQL / Python 新建动作。
- [UX] 脚本开发页已移除与首页重复的分流卡片，空白态重新聚焦为脚本研发入口，不再承担首页职责。

# [v1.4.33] - 2026-04-19
- [UX] 数据开发模块已新增首页化入口，用户进入后可先选择“新建 SQL 脚本 / 新建 Python 草稿 / 进入数据建模 / 浏览现有脚本”，再进入具体 IDE。
- [UX] 数据开发工作台已从三列常驻布局收敛为“左侧资源树 + 中央主工作区”，版本历史与执行记录改为底部辅助区按需展开，整体更聚焦编辑主线。
- [UX] 顶部信息区已压缩为紧凑工具条，避免大面积摘要卡片继续挤占研发空间。

# [v1.4.32] - 2026-04-19
- [UX] 数据开发工作台已新增顶部摘要区，当前脚本、执行环境、执行状态与最近反馈改为主界面集中展示，减少信息分散带来的认知负担。
- [UX] 结果面板已新增页内反馈条与执行结果概览，执行成功、失败、预演三类结果都可直接看到状态、耗时和返回规模。
- [Bugfix] 数据开发脚本的创建、打开、编辑、保存、发布、回滚、执行等关键操作已改为优先展示后端原始错误信息，不再统一退化成泛化失败提示。

# [v1.4.31] - 2026-04-19
- [Bugfix] 修复数据开发脚本前后端执行语义不一致：前端已去掉数据源选择后，新建 SQL 脚本不再一律落入 `mvp` 预演路径。
- [Feature] `DataDevScript` 已新增执行引擎字段，SQL 脚本可声明 Spark SQL / Hive，后端执行分发改为“脚本执行引擎优先，数据源次之”。
- [UX] 数据开发 IDE 的新建/编辑脚本弹窗已补充执行引擎选择，底部状态栏改为展示真实数据源或脚本执行引擎。
- [Compat] 迁移已为历史脚本回填执行引擎：SQL 默认 `spark`，Python 默认 `mvp`。

# [v1.4.30] - 2026-04-19
- [Feature] 数据开发目录已新增【数据建模】模块，支持模型列表、模型详情、字段维护、DDL 预览与提交建表闭环。
- [Feature] `apps.datadev` 已新增 `DataDevModel / DataDevModelField` 及 `/datadev/models` 接口，草稿建模定义正式从脚本 IDE 中独立出来。
- [Compat] 模型提交建表继续复用统一 `Task / TaskInstance` 和 Spark/Hive 执行器，执行成功后自动回写模型状态与统一任务配置。
- [UX] 数据开发 IDE 已移除临时“建模执行”按钮，手工建表统一收敛到专属数据建模入口。

# [v1.4.29] - 2026-04-19
- [Feature] 数据开发 IDE 新增“建模执行”入口，手工建表场景已收敛到数据开发内，不再依赖管理员 Web Terminal。
- [Governance] 建模执行前新增最小治理卡点：执行引擎、数据层级、目标表名、表注释、负责人缺一不可。
- [Feature] `TaskService.execute_datadev_script` 已支持无数据源的建模执行模式：对 `CREATE TABLE` 语句可直接调用 Spark/Hive 执行器，并继续纳入统一 `Task / TaskInstance` 链路。

# [v1.4.28] - 2026-04-19
- [UX] 数据开发模块已按本地 MVP 角色收敛：脚本未绑定数据源时，运行入口不再直接失败，而是返回一次开发预演摘要。
- [Feature] `TaskService.execute_datadev_script` 已支持无数据源的 `mvp` 预演模式，照常创建 `TaskInstance / DataDevScriptExecution`，先承接脚本研发、版本管理与统一任务登记职责。
- [UX] 数据开发 IDE 的运行日志已补充“MVP预演完成”提示，避免误解为真实数据查询结果。


# [v1.4.27] - 2026-04-19
- [Feature] `apps.executors` 已接通当前任务模型：`DataXConfigBuilder / DataXExecutor` 现可直接消费 `DataIntegrationTask` 的数据源、源资产、目标表与 `taskConfig`，开始支持真实 DataX 执行链路。
- [Feature] `TaskService.execute_integration_task` 已取消对 `mock` 的硬编码限制，改为按 `executor_type` 动态校验并分发执行器，统一回写 `TaskInstance` 结果摘要。
- [Feature] 数据开发 SQL 执行已新增 Spark/Hive 执行器分发：Spark/Hive 数据源通过 executors 调用 `spark-sql / hive` CLI，传统库仍保留 `dbutils` 查询执行路径。
- [Compat] `dataintegration/task/validate` 已接入真实执行器校验，不再静态拦截 `datax`。


# [v1.4.26] - 2026-04-19
- [UX] `/datatask` 模块已统一对外更名为“任务运维”，继续承载统一 Task 中轴，但不再以“数据任务”命名暴露给用户。
- [UX] 任务运维首页、任务详情、执行记录页与数据集成详情页的面包屑 / 返回文案已同步收敛，明确该模块纳管数据集成任务和数据开发任务。
- [UX] 任务运维首页新增“进入数据开发”快捷入口，避免统一任务运维入口只偏向数据集成侧。


# [v1.4.25] - 2026-04-19
- [Feature] 新增统一任务调度执行底座 MVP：`apps.datatask.scheduler.TaskSchedulerService` 已支持 `cron` 扫描与依赖触发调度。
- [Feature] 新增管理命令 `uv run python manage.py run_task_scheduler`，可单次执行调度扫描或以固定间隔轮询运行。
- [Compat] `TaskService.execute_task` 已统一支持 `manual / schedule / dependency` 三种触发模式，调度器与人工执行共用同一分发链路。
- [Test] 已补充 `datatask` 调度服务回归测试，覆盖 cron 触发、同分钟去重、依赖触发与依赖指纹去重。

# [v1.4.24] - 2026-04-19
- [Bugfix] 修复 `/system/terminal` 目录路由直达 404：前端动态路由注册不再拍平带 `redirect` 的 `ParentView` 节点，父级目录可正常承载重定向。
- [Compat] 目录型菜单现支持“直接访问父路径 → 自动跳转到默认子页”的通用模式，`/system/terminal` 已恢复跳转到 `/system/terminal/index`。

# [v1.4.23] - 2026-04-19
- [Bugfix] 修复报表管理前后端未完全接通问题：当前开发库已补执行报表相关迁移，`dataservice_report_*` 表结构恢复可用。
- [Bugfix] 补齐“报表管理”菜单的 `dataservice:report:add/edit/remove/view` 权限点，前端按钮显隐与接口权限重新对齐。
- [Ops] 当前环境已同步最新菜单种子，报表管理页面现可完成列表、创建、修改、删除与详情查看闭环。

# [v1.4.22] - 2026-04-19
- [Feature] 数据服务“SQL查询”已新增“发布接口”能力，可将当前查询 SQL 直接发布到接口管理。
- [Feature] `apps.dataservice` 已新增 `/dataservice/interface-info/publish`，自动复用现有 `InterfaceInfo / InterfaceField` 模型创建接口定义。
- [UX] 发布弹窗会自动回填当前数据源、SQL、模板参数与查询结果列，只需补充接口名称、编码、描述即可完成发布。
- [Guard] 接口管理新增/修改与 SQL 发布接口已统一校验：启用合计时必须填写合计SQL；接口详情页同步新增合计SQL查看入口。
- [Feature] 接口管理列表已补齐接口生命周期操作，支持直接对接口执行上线 / 下线切换。
- [Guard] 接口删除现收敛为“下线后软删除”：已上线接口不可直接删除，删除时会同步归档接口字段。
- [Guard] 下线接口不可再试运行、查询或导出，避免接口资产状态与实际服务能力脱节。
- [UX] 接口管理列表新增负责人列，并补齐负责人 / 接口状态检索，提升接口资产筛选与认领效率。
- [UX] 接口新增 / 修改表单已支持负责人维护，留空时默认回填当前登录用户；接口详情页同步展示负责人。
- [UX] 接口管理已取消列表页中的正式查询与独立测试按钮，统一通过“详情”进入详情页中的“接口定义 / 接口测试”标签页。
- [UX] 接口测试详情页现已改为展示真实接口执行返回报文，除响应字段结构说明外同步展示原始响应 JSON，避免与实际调用结构不一致。
- [UX] 接口测试页的响应报文区域已补充状态摘要、原始报文 / data 载荷双视图与复制能力，提升联调可读性。
- [Feature] 接口 `/execute` 已对齐纯接口调用协议，新增 `reportName / interfaceName / isPaging / isTotal / property` 等业务语义字段，并按分页/非分页场景输出 `list/total/totalList` 或 `data/totaldata`。
- [UX] 接口管理列表、详情页和编辑表单已移除报表名称 / 报表编码展示，避免在报表管理未上线前形成错误归属语义。

# [v1.4.21] - 2026-04-19
- [UX] 数据源管理列表已移除主机、端口、用户名三列，首页信息收敛到“数据源识别 + 连通性 + 启停状态”，更贴近平台资源总览视角。
- [UX] 数据源管理列表的“连通性”列已改为 tooltip 详情展示，列表仅保留状态标签与详情提示，测试时间和异常原因改为悬浮查看。
- [Feature] `apps.datasource` 已持久化最近连通性状态、说明与测试时间；按资源 ID 执行连接测试后会自动回写成功/失败结果。
- [Guard] 数据源连接配置发生变更时，最近连通性状态会自动重置为“未测试”，避免旧测试结果继续误导后续集成与资产采集操作。


# [v1.4.20] - 2026-04-18
- [Docs] 已将“单轮单目标、故障优先、禁止扩 scope、文档与审查后置、分歧先停”等项目协作规则固化到根 `CLAUDE.md`，确保会话启动即自动加载。
- [UX] 已继续优化数据资产、数据服务、数据任务、数据集成四个模块首页的空间利用：主内容卡片在常规桌面宽度即可并排展开，减少右侧留白与单列堆叠。
- [UX] 数据资产与数据服务首页的核心能力、使用流程已改为更高密度排布，提升首屏可见信息量；并已移除数据资产首页“覆盖概览”区块与数据服务首页“最近查询动态”区块。
- [UX] 数据任务首页已从“逐任务卡片浏览”重构为“任务运行总览台”，首页只保留运行态势、异常暴露与快捷入口，不再承担单任务列表职责。
- [UX] 数据任务总览台进一步移除大块筛选区，改用轻量“观察周期”切换，避免首页重新退回列表页思路。
- [UX] 数据任务总览台新增概览指标、执行趋势柱状图、来源/调度分布饼图、异常看板与最近动态，帮助用户先判断整体运行健康度，再进入任务详情治理。
- [UX] 数据任务图表区已改为宽屏自适应布局：趋势图占主内容整行，来源/调度饼图在常规桌面宽度下即可并排展开，并跟随容器宽度自动重算尺寸。
- [Bugfix] 修复当前开发库 `datatask` 迁移记录与真实 SQLite 表结构漂移问题：新增 `0002_repair_legacy_schema`，兼容旧版 `datatask_task` 遗留表并补建统一任务依赖/实例表。
- [Bugfix] 恢复 `/data-api/datatask/task` 列表接口可用性，解决“数据任务”页面进入即因 `no such column: datatask_task.source_module` 返回 500 的问题。
- [Feature] `datatask` 已补齐统一任务更新接口：任务详情页现在可以直接维护状态、负责人、调度方式与备注，不再只是只读概览。
- [Feature] 统一任务中心新增 `/data-api/datatask/task/{id}/execute` 执行入口，可按来源模块分发到数据集成任务或数据开发脚本的真实执行链路。
- [Compat] `DataIntegrationTaskViewSet.execute_task` 与 `ScriptViewSet.execute_script` 已复用统一任务执行服务，避免来源页和任务中心出现双套执行逻辑漂移。
- [UX] 数据任务详情页升级为“概览 + 治理配置”布局，支持直接保存治理配置、触发执行，并按来源模块跳回数据集成详情或数据开发 IDE。
- [Bugfix] 修正 `/datatask` 菜单种子下误写为 `dataintegration:*` 的权限点，当前环境已通过 `initdata` 同步为 `datatask:*` 权限集。
- [Feature] 新增管理命令 `uv run python manage.py sync_menu_data`，支持将当前数据库 `sys_menu` 树同步回 `backend/apps/system/management/commands/menu_data.json`。
- [Docs] 已按当前开发库真实菜单结构刷新 `menu_data.json`，补齐 `menuId/query/isFrame/isCache/redirect/activeMenu/isAffix/isBreadcrumb/alwaysShow` 等菜单字段。
- [Refactor] `initdata` 已复用统一菜单转换逻辑，确保数据库导出的 `menu_data.json` 仍可直接用于新环境菜单初始化。
- [Feature] 新增“数据任务”前端模块：补齐 `frontend/src/views/data/task/index.vue`、`taskDetail.vue`、`instances.vue`，开始以统一任务中心视角承接任务管理。
- [UX] 数据任务中心保留统一任务入口定位，并继续提供“新建集成任务”直达入口与来源工作面跳转能力。
- [UX] 数据集成任务创建/编辑已从抽屉切换为独立详情页 `frontend/src/views/data/integration/detail.vue`，任务中心可直接跳转到该页面完成配置。
- [Compat] `DataIntegrationTaskViewSet` 的创建/更新接口现直接返回任务详情数据，便于前端保存后无缝切换到详情页继续编辑。
- [Feature] 初始化菜单补齐 `/datatask`、`DataTaskDetail`、`DataIntegrationTaskCreate`、`DataIntegrationTaskDetail` 路由，并将 `/datatask` 纳入普通角色默认可见业务菜单范围。
- [Bugfix] `dataintegration` 创建 / 更新 / 删除已补齐事务与依赖清理，避免配置模型、统一任务和任务依赖出现软删不同步。
- [Bugfix] `system/getInfo` 现按用户角色聚合菜单权限，普通角色的 `v-hasPermi` 按钮显隐恢复正常工作。
- [Bugfix] 数据集成详情页的数据源 / 源资产选项改为跨页拉取，避免后端分页上限 100 导致下拉项缺失。
- [Bugfix] 请求拦截器与新页面错误提示已对齐，业务失败不再重复弹出两次错误提示。
- [UX] “数据集成 > 同步任务”页面继续收敛信息层级：首页改为轻筛选 + 紧凑任务列表，配置/调度/运行记录迁入详情抽屉分 Tab 查看。
- [Bugfix] 修复初始化菜单时 `menu_id` 仅由 `orderNum` 推导导致的顶级菜单 ID 冲突问题；`initdata` 现支持从 `menu_data.json` 显式读取 `menuId`。
- [Bugfix] 为“数据集成”菜单分配独立菜单 ID，修复当前环境登录后 `getRouters` 缺失 `/data-integration`、浏览器无法进入新页面的问题。
- [UX] “数据集成 > 同步任务”页面重构为工作台式布局：筛选卡片、任务卡片流、配置概览、执行快照与抽屉式编辑集中在同一视图内。
- [UX] “任务编排 > 依赖编排”页面重构为任务卡片 + 上下游依赖泳道布局，弱化通用表格页形态，更贴近数据平台编排工作台。
- [Frontend] 两个工作台页面已统一改用组件化图标引用，降低对全局图标注册方式的运行时耦合。
- [Feature] `apps.datatask` 已补齐 `TaskDependency` 写接口，支持新增、修改、删除依赖关系，并为下游任务自动同步 `dependency/manual` 调度方式。
- [Feature] 新增“任务编排 > 依赖编排”页面 `frontend/src/views/data/orchestration/index.vue`，支持查看统一任务清单与配置上下游依赖关系。
- [Guard] `TaskDependency` 新增自依赖、重复依赖与环依赖校验，避免形成非法 DAG。
- [Feature] 初始化菜单新增“任务编排”模块及 `datatask:dependency:*` 权限点，并纳入普通角色默认可见业务菜单范围。
- [Frontend] 新增“数据集成 > 同步任务”页面 `frontend/src/views/data/integration/index.vue`，支持任务查询、创建、编辑、删除、手动执行和执行记录查看。
- [Frontend] 数据集成页面已对接当前后端任务接口，并补充配置校验、源资产联动选择与执行详情展示。
- [Feature] 初始化菜单新增“数据集成”模块及 `dataintegration:task:*` 权限点，普通角色默认可见范围同步纳入 `/data-integration`。
- [Compat] 前端 `api/data/integration.js` 已对齐当前阶段执行器边界：`mock` 为可用执行器，`datax` 标记为待接入。
- [Feature] 新增数据集成模块 `apps.dataintegration`，落地 `DataIntegrationTask` 配置模型，承载源/目标数据源、源资产、目标表、加载/写入模式与执行器配置。
- [Feature] 新增数据集成接口：`/data-api/dataintegration/task`、`/task/{id}/execute`、`/task/{id}/executions`、`/executionlog`，开始承接遗留前端 `integration.js` 的核心路径。
- [Feature] 数据集成任务已接入统一任务中心：创建/更新配置时同步 `DATA_SYNC` 任务定义，执行时创建 `TaskInstance`。
- [Compat] 数据集成首期已用 `mock` 执行器打通执行闭环；`datax` 目前保留配置入口，执行时返回显式提示，等待后续适配器接入。
- [ADR] 新增 ADR-009，明确数据集成模块采用“配置模型 + 统一任务映射”策略。
- [Test] 新增 `apps.dataintegration` 测试，覆盖任务创建、mock 执行和执行日志详情接口。
- [Feature] 新增统一任务中心模块 `apps.datatask`，落地 `Task`、`TaskDependency`、`TaskInstance` 三类核心模型，作为平台目标态的统一任务内核。
- [Feature] 新增统一任务查询接口：`GET /data-api/datatask/task`、`GET /data-api/datatask/task-dependency`、`GET /data-api/datatask/task-instance`。
- [Feature] `datadev` 脚本执行链已接入统一任务中心：执行时自动生成/刷新 `SQL_COMPUTE` 任务并创建 `TaskInstance`。
- [Compat] `DataDevScriptExecution` 新增 `task_instance` 关联字段，保留原有脚本执行记录模型，同时与统一任务实例建立映射。
- [ADR] 新增 ADR-008，明确统一任务内核与实例模型作为后续数据集成、数据开发、编排运维的统一中轴。
- [Test] 新增 `apps.datatask` 测试与 `datadev -> datatask` 集成测试，覆盖任务复用、实例完结和脚本执行接入链路。
- [Feature] 数据资产模块新增规范读接口：`GET /data-api/dataasset/asset-namespace`、`GET /data-api/dataasset/asset`、`GET /data-api/dataasset/asset-column`。
- [Refactor] `meta-table` / `meta-column` 的 GET 查询已切换为从 `AssetNamespace`、`DataAsset`、`DataAssetColumn` 读取，采集写端与血缘写端保持现状不变。
- [Compat] 兼容旧元数据页面响应结构：继续返回 `tableName / databaseName / dataSourceName` 等历史字段，并优先透出 `legacy_meta_*` 标识保证现有页面可继续工作。
- [Test] 新增数据资产读端回归测试，覆盖规范接口详情查询与旧元数据查询兼容行为。
- [Frontend] 前端 `api/data/asset.js` 补充规范资产查询封装，支持后续页面渐进切换到规范接口。
- [Bugfix] 修复 `0004_backfill_standard_asset_models` 在旧库升级时把未落库命名空间对象送入 `bulk_update` 导致迁移失败的问题，数据资产规范模型迁移现已可在真实库完成升级。
- [QA] 完成数据资产模块浏览器级联调，确认资产概览、元数据列表/筛选/详情与血缘表选择器在本地真实环境下可正常工作。

# [v1.4.19] - 2026-04-17
- [Refactor] 数据资产模块启动标准模型重构 Phase 1：新增 `AssetNamespace`、`DataAsset`、`DataAssetColumn` 三类规范资产模型。
- [Refactor] 扩展 `MetaCollectionTask`，补齐采集范围与运行模式字段，为后续分层采集奠定模型基础。
- [Refactor] 现有元数据采集链路已同步双写到规范资产模型，保留 `MetaTable` / `MetaColumn` 兼容现有接口。
- [Bugfix] 补齐 Presto/Trino 的 `catalog.schema` 命名空间解析，并同步修正采集任务 `scope_catalog_name / scope_schema_name / scope_level` 的回填与运行时写入。
- [Bugfix] 规范字段同步改为按列名原位更新并过滤软删除历史列，避免重采时 `DataAssetColumn` 主键抖动。
- [Bugfix] 同步采集改为单表事务提交，避免外层长事务放大锁持有范围；异步采集启动前增加数据库级活动任务检查。
- [Bugfix] 字段采集结果为空时显式中止同步，避免采集器异常降级为空列表时误删历史字段。
- [Bugfix] 同步/异步采集统一接入活动任务占槽，补齐任务取消轮询、启动异常失败回写与数据库级单活动任务约束。
- [Refactor] 数据资产标准模型回填迁移拆分为独立 `0004` 数据迁移，并新增 `0005` 活动任务约束迁移，降低发布失败时的恢复成本。
- [Bugfix] `0004` 数据回填迁移改为可重跑写入，`0005` 在增加活动任务唯一约束前先清理历史重复活动任务。
- [ADR] 新增 ADR-007，明确本阶段只做源数据模型标准化，血缘标准化延后。
- [Docs] 修正数据资产模块文档状态：按当前代码主干确认 `dataasset` 模块仍保留，而非已完全移除。
- [Docs] 新增 `docs/requirements/data-asset-module.md`，补齐数据资产模块的当前范围、入口、接口与实现边界说明。
- [Docs] 更新 `docs/requirements/README.md`，将数据资产模块从“已归档”恢复为当前模块文档。
- [Docs] 同步修正主 README 的数据资产能力矩阵、初始化命令、API 文档地址，并清理 requirements 索引中的失效链接。
- [Docs] 继续修正主 README 的生产构建说明与监控模块状态描述，使部署步骤和能力矩阵与仓库实现一致。
- [Docs] 补充前端开发默认绑定 `80` 端口的限制说明，避免本地启动时因端口权限报错。
- [Docs] 收敛主 README 中未生效的生产环境变量模板，并将前端生产访问入口统一到 `/data-admin/` 子路径。
- [Docs] 修正主 README 中的 Python 最低版本、`uv run` 部署命令与本地开发访问路径，使说明可按当前主干直接执行。
- [Review] 启动数据资产模块设计评审，重点识别架构边界、元数据建模与采集任务架构问题；血缘标准化已明确延后。

# [v1.4.18] - 2026-04-17
- [Feature] 为“数据服务”模块补齐首页导航，新增子菜单 `服务概览`（`/data-service/index`）并指向组件 `data/service/index`。
- [Ops] 同步补齐当前环境数据库菜单与角色授权，保证管理端刷新后可直接访问“数据服务 > 服务概览”。
- [Bugfix] 修复全局面包屑组件固定前置“首页”问题，改为按当前路由层级自然展示。
- [UX] 重设计“数据服务 > 服务概览”首页，补充核心能力说明、快捷入口、使用流程与最近动态，帮助用户快速理解模块用途。
- [UX] 调整服务概览页视觉风格到项目统一的后台卡片体系，弱化独立专题页风格，保持与现有页面一致性。
- [UX] 细化服务概览页的字体层级、按钮样式、标签强度与区块间距，进一步贴合现有后台页面的视觉节奏。

# [v1.4.17] - 2026-04-16
- [Cleanup] 移除 `apps.dataetl` 后端模块及其路由注册，收敛 Django 运行时能力边界。
- [Cleanup] 删除前端 ETL 首页、任务页、执行日志页与对应 API 封装，避免遗留空菜单和失效请求。
- [Refactor] 首页仪表盘移除 ETL 统计与图表，仅保留数据源与资产概览。
- [Refactor] `apps.executors` 中 DataX 水位线逻辑改为无持久化模式，解除对 `ETLWatermark` 的跨模块依赖。
- [Docs] 同步更新初始化菜单、README、快速参考和 ADR 状态，标记 dataetl 已下线。

# [v1.4.16] - 2026-04-16
- [Cleanup] 删除本地历史分支 `feature/etl` 与 `fix/menus`，收敛当前开发分支集。
- [Security] 修复 `apps.dbutils.presto` 中 `SHOW CREATE TABLE` 的 schema/table 直接拼接问题，统一改为安全标识符引用。
- [Security] 修复 `apps.dbutils.sqlite` 中 `PRAGMA table_info` 的表名直接拼接问题，避免 SQLite 元数据查询被注入。
- [Security] 收敛 `apps.monitor.middleware` 操作日志响应体落库范围：响应内容改为脱敏后的摘要，避免 token、密码等敏感信息写入日志。
- [Security] 修复数据源连接测试接口异常明文透传问题，前端统一返回安全提示，详细错误保留在服务端日志中。
- [Security] 收敛 `apps.dbutils.presto` 执行器异常消息，避免其他调用路径直接暴露底层连接细节。
- [Test] 新增 `apps.monitor.tests`、`apps.datasource.tests`，并补充 `apps.dbutils.tests` 覆盖安全修复边界。
- [Bugfix] 修复服务监控采集失败吞错问题：后端返回 `warnings` 并写入日志，CPU/内存采集失败时不再伪装为正常数值。
- [UX] 服务监控页新增采集告警提示，不可用指标统一显示为 `--`。

# [v1.4.15] - 2026-04-08
- [Bugfix] 修复 dbutils SQL 类型误判：执行前复用 `_check_sql` 规范化结果，避免注释/空白前缀导致 SHOW/DESCRIBE/EXPLAIN 被错误分页。
- [Bugfix] 修复 SQL 错误定位偏移：SQL 校验使用标准化文本，但执行阶段保留原始 SQL（含注释），便于按原始行号定位报错。
- [Refactor] 将 SQL 校验方法重命名为 `_check_and_normalized_sql`，统一方法语义并同步调用与测试引用。
- [Bugfix] 优化分页前分号处理：按“最后一个非注释行”判断并移除末尾分号，避免尾部注释导致分号识别错误。
- [Security] 增强 SQL 只读校验：支持块注释与行内注释剥离，限制单语句执行，拦截 `WITH` 语句中的写操作与 DDL 关键词。
- [Bugfix] 修复分页边界误判：查询分页改为 `page_size+1` 探测下一页，避免总数整除时错误返回 next。
- [Test] 新增 `apps.dbutils.tests` 覆盖 SQL 校验与分页核心边界场景。

# [v1.4.14] - 2026-04-06
- [Feature] 脚本执行从模拟数据切换为真实数据源执行：通过 dbutils 连接脚本关联的数据源，执行真实 SQL 并返回结果。
- [Feature] 执行前置校验：检查数据源关联、当前版本、脚本内容是否为空。
- [Feature] 执行失败记录：异常时保存 status=failed 的执行记录并返回错误信息。

# [v1.4.13] - 2026-04-06
- [Bugfix] 修复脚本执行结果无法回填前端问题：后端模拟 Spark SQL 执行并返回列名、行数据与耗时，前端解析结果填充数据预览面板。
- [Bugfix] 修复状态栏光标行列信息始终为空：CodeEditor 监听 `changeCursor` 事件并上报光标位置。
- [Bugfix] 修复版本预览后脏状态判断异常：查看历史版本不再覆盖 `savedContent`，保留原始内容用于变更检测。
- [Bugfix] 修复保存/发布后本地 `versionNumber` 自增不一致：移除本地自增，改由 `openScript` 从后端同步正确版本号。
- [Feature] 资源导航树脚本节点新增删除按钮，支持确认弹窗后删除脚本并自动关闭对应页签。
- [Feature] 新建脚本对话框支持选择脚本类型（SQL / Python），对齐 ADR-006 首期语言范围。
- [Feature] 资源导航树脚本节点新增编辑按钮，支持修改脚本名称、所属目录与描述信息。
- [Refactor] 脚本列表加载从循环分页遍历优化为单次大页请求，减少网络开销。

# [v1.4.12] - 2026-04-06
- [UX] 资源导航树交互体验优化：
  - 父节点无论有无子项始终显示展开/折叠肩头。
  - 子项数量标签紧贴主文本。
  - 点击节点任意区域只选中节点，不再导致所有节点自动展开。
  - 展开/折叠操作仅由肩头控制，行为与主流后台一致。

## [v1.4.11] - 2026-04-06
- [Refactor] 数据开发 IDE 侧边栏代码优化：移除冗余 `activeDirectoryFilter` 本地状态，toggle 逻辑直接引用 `props.activeDirectoryId`，消除双源真值问题。
- [Feature] 资源导航树刷新按钮升级：点击刷新按钮不仅重渲染树组件，还通知父组件重新请求目录与脚本数据。
- [Feature] 资源导航树目录节点新增子项计数标签：显示每个目录下的子目录与脚本总数。
- [Feature] "未分配目录"节点新增快捷创建脚本按钮，与普通目录保持一致。
- [Refactor] 树节点 `isLeaf` 属性正确映射：空目录也显示展开/折叠箭头，不再因无子节点而隐藏。
- [Refactor] 初始展开策略从 `default-expand-all` 改为 `default-expanded-keys`，仅默认展开第一层目录，子层级需点击展开。
- [Bugfix] 修复目录节点 `comment` 字段未映射问题：目录 `remark` 和脚本 `description` 正确传入树节点数据。
- [Cleanup] 移除未使用的 `.ds-icon` CSS 类。

## [v1.4.10] - 2026-04-06
- [Refactor] 数据开发 IDE 资源导航树调整为目录-脚本树结构，目录节点下直接展示所属脚本。
- [Feature] 新增“默认目录”节点，统一承载无所属目录脚本。
- [Feature] 资源树支持脚本节点点击即打开，保留目录节点筛选能力。

## [v1.4.9] - 2026-04-06
- [Feature] 数据开发数据目录管理页恢复“新增目录”入口，支持直接创建目录。
- [Refactor] 目录弹窗统一为新增/修改双模式：自动根据 `directoryId` 路由到新增或更新接口。

## [v1.4.8] - 2026-04-06
- [Feature] 新增数据开发数据目录前端管理页 `data/dev/catalog/index`，支持目录树查询、新增、修改、删除。
- [Feature] 数据开发 IDE 目录化联动升级：侧边栏按目录筛选脚本，目录/数据源节点新建脚本自动携带 `directoryId`。
- [Refactor] 脚本新建参数从 `layer` 切换为 `directoryId`，与后端 `DataDevScript.directory` 模型保持一致。
- [Feature] 新增前端目录 API 封装：`listDirectories/getDirectoryTree/addDirectory/updateDirectory/delDirectory`。
- [Feature] 后端目录接口增强：目录树节点返回 `scriptCount`，目录删除新增子目录/脚本占用校验。
- [Bugfix] 后端目录更新新增父子循环防护，禁止将目录挂载到自身子目录下。
- [Feature] 数据开发模块新增 `DataDevDirectory` 数据目录模型，用于管理开发脚本目录项。
- [Feature] 初始化命令 `initdata` 新增数据目录种子逻辑，默认创建 ODS 贴源层、DWD 明细层、DWS 汇总层、ADS 应用层四个目录项。
- [Refactor] 数据目录从菜单结构中解耦，改为独立业务模型承载，便于后续持续扩展目录内容。
- [Test] 新增 `apps.datadev` 测试，验证初始化命令可正确创建默认数据目录。

## [v1.4.7] - 2026-04-06
- [Feature] 数据开发版本历史交互增强：点击版本条目可直接在编辑区查看对应版本内容。
- [Feature] 版本查看状态可视化：新增版本条目选中态高亮，便于识别当前浏览版本。
- [Bugfix] 增加未保存保护：编辑区存在未保存修改时，切换查看历史版本前弹窗确认，避免误覆盖。

## [v1.4.6] - 2026-04-06
- [Feature] 数据开发脚本版本管理逻辑收敛：同一脚本保存草稿时优先更新已有草稿版本，避免生成多个草稿版本记录。
- [Feature] 保持正式版本可多次发布：发布动作仍按版本号递增创建正式版本快照，支持长期可追溯。
- [Refactor] 版本当前态维护优化：保存草稿与发布正式版本前统一清理旧 `is_current` 标记，确保当前版本唯一。
- [Test] 新增 `apps.datadev` 单元测试，覆盖草稿单例与多次发布正式版本核心场景。

## [v1.4.5] - 2026-04-06
- [Feature] 数据开发执行引擎策略调整：脚本执行统一按 Spark SQL 引擎提交，不再依赖创建时选择数据源。
- [Refactor] 新建脚本弹窗简化：移除数据源选择项，执行器明确为“Spark SQL 执行引擎（固定）”。
- [Feature] 版本历史视图增强：新增“全部/正式/草稿”筛选，支持同时查看历史正式版本与草稿版本。
- [Docs] ADR-006 补充执行引擎策略：新增“执行引擎策略补充（2026-04-06）”并明确版本区可见性要求。

## [v1.4.4] - 2026-04-06
- [Feature] 数据开发 IDE 中央编辑区升级为多页签模式，支持并行打开多个脚本并快速切换。
- [Feature] 新增页签未保存保护：关闭存在变更的脚本页签时弹出确认，避免误关闭。
- [Refactor] 编辑器工具栏视觉重构：增加当前文档信息胶囊与语言标识，执行按钮文案调整为“运行当前文档”。
- [Refactor] 左侧资源区样式升级：按 ADR-006“资源导航树”语义优化层级展示与脚本分组可读性。
- [Refactor] 数据开发页面整体 UI 升级为统一 IDE 风格，并补充移动端断点下的可用布局。

## [v1.4.3] - 2026-04-06
- [Feature] 数据开发编辑器新增“发布”按钮：在“保存草稿版本”之外，支持发布正式可用版本。
- [Feature] 版本管理升级：草稿脚本允许入版本表，并通过版本字段标记为“草稿（非正式可用）/正式可用”。
- [Feature] 后端新增发布接口：`POST /datadev/scripts/{id}/versions/publish`，发布时自动创建正式版本并更新脚本状态为 `published`。
- [Feature] 版本历史视图增强：右侧版本列表新增“草稿/正式”标签，便于区分可用性。

## [v1.4.2] - 2026-04-06
- [Feature] 数据开发分层目录树支持点击联动筛选：点击 ODS/DWD/DWS/ADS 层级节点后，“我的脚本”仅显示当前分层脚本。
- [Feature] 分层筛选支持快速切换：点击同一层级节点可取消筛选并恢复全部脚本视图。
- [Feature] 新建 SQL 脚本对话框增强分层联动：从分层/数据源节点触发新建时，自动预填脚本 `layer` 字段。

## [v1.4.1] - 2026-04-05
- [Bugfix] 修复数据开发 IDE 执行状态误导：前端调用执行接口后不再直接显示“执行成功”，改为“已提交（待执行）”。
- [Refactor] 对齐后端当前能力边界：执行接口现阶段仅落库 `pending` 执行记录，待后续对接 `apps.executors` 实际执行链路。
- [Feature] 新增前端执行状态轻量轮询：提交后自动跟进状态变化并刷新执行记录，轮询超时时提示用户稍后查看。
- [Bugfix] 修复执行状态轮询并发污染：切换脚本或重复执行时主动清理旧轮询器，避免多定时器同时写入状态。
- [Bugfix] 修复 `cancelled` 状态显示不一致：状态栏与执行记录统一展示为“已取消”，不再误映射为“失败”。

## [v1.4.0] - 2026-04-05
- [Feature] 新增数据开发模块后端（`apps.datadev`）：
  - 实现三个核心模型：`DataDevScript`（脚本资产）、`DataDevScriptVersion`（版本快照）、`DataDevScriptExecution`（执行记录）
  - 实现完整 RESTful API：脚本 CRUD、版本创建/回滚、执行触发、执行记录查询
  - 路由注册：`data-api/datadev/scripts`、`data-api/datadev/executions`
  - 数据库迁移已生成并执行
- [Architecture] 遵循 ADR-006 决策：模型独立，执行层预留复用 `apps.executors` 适配接口

## [v1.3.8] - 2026-04-05
- [Feature] 顶部导航点击父级菜单时，除联动侧边栏外新增自动路由跳转：优先使用路由 `redirect`，否则跳转首个子路由，避免仅展开不跳转。
- [Bugfix] 修复浏览器控制台 `Added non-passive event listener to a scroll-blocking 'wheel' event` 性能警告：在应用初始化阶段统一为 `wheel/touchstart/touchmove` 事件补充 `passive` 默认值，提升滚动响应性。

## [v1.3.7] - 2026-04-05
- [Docs] 新增 ADR-006，明确数据开发模块架构决策：定位为脚本研发中心（SQL/Python），首期聚焦脚本资产管理、版本管理与执行记录查询。
- [Refactor] 明确数据开发与 ETL 边界：脚本域模型独立，执行层复用 `apps.executors`，不重复建设执行器体系。
- [Docs] 同步更新 active_tasks，建立后续模块实施的文档基线。

## [v1.3.6] - 2026-04-05
- [Refactor] 将 ETL 执行器基础能力抽象为通用模块：新增 `apps.executors`（`BaseExecutor`、`ExecutorFactory`）。
- [Refactor] `apps.dataetl.executors.base` 改为兼容转发层，继续导出 `BaseETLExecutor` 与 `ExecutorFactory`，确保历史导入路径无缝可用。
- [Feature] 为后续非 ETL 业务复用执行器注册与实例化机制提供统一入口，降低模块耦合。

## [v1.3.5] - 2026-04-04
- [Refactor] 字典管理页面代码质量改进：
  - 添加统一的错误处理函数 `handleApiError`，区分开发/生产环境错误输出
  - 所有 API 调用添加 `.catch()` 错误处理和 `.finally()` 清理逻辑
  - 修复非严格相等比较（`!=` → `!==`）
  - 迁移至标准 ref 引用方式（`dictRef.value?.validate`），替代 `proxy.$refs`
  - 添加字典数据防御性检查（`sys_normal_disable = []`）
  - 使用 `defineOptions` 替代 `<script setup name="Dict">` 语法
  - 改进删除操作错误处理，区分用户取消和真实错误
  - 显式导入 Vue Composition API（`ref`, `reactive`, `toRefs`, `getCurrentInstance`）
  - 使用模板字符串替代字符串拼接

## [v1.3.4] - 2026-04-03
- [Bugfix] 切换生产构建压缩器为 terser，修复 esbuild 对 `@xterm/xterm` TypeScript 枚举 IIFE 二次压缩时丢失 `let` 变量声明，导致 ESM 严格模式下 `requestMode` 抛出 `ReferenceError: i is not defined` 的问题。详见 `docs/postmortem/esbuild-xterm-requestMode-bug.md`。

## [v1.3.3] - 2026-04-03
- [Bugfix] 修复 Nginx 反向代理下浏览器终端 vim 等全屏程序无法正常使用的问题：WebSocket location 添加 `proxy_buffering off` 禁用响应缓冲，确保 PTY 输出逐帧实时转发；同时添加 `proxy_send_timeout 3600s` 防止发送方向空闲断连。

## [v1.3.2] - 2026-04-03
- [Bugfix] 修复 ASGI 入口（config/asgi.py）模块导入顺序问题：将 JwtAuthMiddleware 导入移到 `get_asgi_application()` 之后，解决 Gunicorn + Uvicorn Worker 启动时 Django 未初始化报错。
- [Bugfix] 确认 Gunicorn + Uvicorn Worker 无法正确路由 Django Channels 的 WebSocket 请求（返回 404），生产环境必须使用 Daphne。
- [Feature] README.md 新增完整生产环境部署指南：系统要求、后端/前端部署步骤、Nginx 反向代理配置（含 WebSocket）、Systemd 服务管理、性能调优建议、常见问题排查。
- [Feature] quick-reference.md 新增生产环境部署速查：快速部署流程、应用服务器兼容性说明、部署检查清单、部署验证命令。
- [Refactor] 删除错误的 pnpm-workspace.yaml 配置文件，修复前端 pnpm 启动失败问题。
- [Refactor] 统一部署文档推荐 Daphne 作为唯一应用服务器，移除 Gunicorn/uWSGI 方案。

## [v1.3.1] - 2026-04-02
- [Bugfix] 修复 Windows 终端 PTY 读取无响应问题：pywinpty PtyProcess.read() 不接受 timeout 参数，改为 read(4096)，修复 TypeError 被静默捕获问题。
- [Bugfix] 增加进程退出时剩余输出的排空逻辑，确保数据完整性。
- [Bugfix] 前端添加缺失的 sortablejs 依赖。
- [Bugfix] 配置 pnpm 允许 esbuild 和 vue-demi 执行构建脚本，解决依赖加载失败问题。

## [v1.3.0] - 2026-04-01
- [Feature] 终端多标签页：支持新建终端 Tab（最多 8 个），每个 Tab 独立 PTY 会话、独立 WebSocket 连接。
- [Feature] 终端会话历史页面重写：双标签页布局（会话记录 + 命令历史），会话列表支持状态/日期范围筛选，命令历史支持关键词/会话 ID 过滤。
- [Feature] 会话列表新增命令数（commandCount）和时长（duration）列。
- [Refactor] 后端 TerminalSessionSerializer 新增 commandCount（annotate 聚合）、duration（时长计算）、updateTime 字段。
- [Refactor] 后端 TerminalSessionViewSet.list() 支持 status/host/beginTime/endTime 查询参数。
- [Refactor] 后端 TerminalCommandViewSet.recent() 支持分页 + keyword + sessionId 过滤。
- [Refactor] 移除命令输出缓冲机制：output 字段仅用于记录 blocked 命令的拦截原因，不再尝试捕获 PTY 输出（shell 输出格式不可控、异步间隙丢数据、ANSI 清理不可靠）。
- [Refactor] 会话历史页面移除"关闭"操作按钮（审计视角不需要操作入口）和"输出"查看功能。

## [v1.2.1] - 2026-04-01
- [Bugfix] 修复 Unix PTY 读取数据竞争：将 `asyncio.wait_for(to_thread)` 替换为 `loop.add_reader(fd)` + `os.read(fd)`，消除键盘输入不可见问题。
- [Bugfix] 修复 pywinpty/ptyprocess 读写 API 不一致（str vs bytes）导致的编码错误，添加平台适配层。

## [v1.2.0] - 2026-04-01
- [Feature] 前端 xterm 升级至 v6（@xterm/xterm），启用 WebGL 渲染、Web Links 可点击链接、Search 搜索、Unicode11 宽字符支持。
- [Feature] 前端终端新增搜索栏（Ctrl+Shift+F），支持上下查找、ESC 关闭。
- [Feature] WebSocket 管理器增加自动重连（指数退避，最多 8 次）+ 双向心跳保活。
- [Feature] 后端 consumer 增加服务端心跳、空闲超时（30 分钟自动关闭）、PTY 环境隔离（白名单环境变量）。
- [Feature] 状态栏显示终端尺寸（cols×rows），连接状态中文化。
- [Feature] 支持 macOS Option→Meta 映射、右键选词、Ctrl+Shift+C/V 复制粘贴快捷键透传。
- [Refactor] 安全模块扩展：新增 Windows 危险命令黑名单、正则检测 fork bomb/reverse shell/sudo/curl|sh 等模式、管道分段解析优化。
- [Refactor] 使用 ResizeObserver 替代 window.resize，终端尺寸同步更精准。

## [v1.1.3] - 2026-04-01
- [Bugfix] 修复 macOS 无法安装/加载 `pywinpty` 导致 Terminal 模块启动失败的问题：后端改为按平台选择 PTY 实现（Windows 使用 `pywinpty`，macOS/Linux 使用 `ptyprocess`）。
- [Refactor] 调整 `backend/pyproject.toml` 依赖为平台条件安装，避免非 Windows 环境拉取 `pywinpty` 失败。

## [v1.1.2] - 2026-04-01
- [Feature] Terminal 后端升级为基于 pywinpty 的跨平台 PTY 进程模型，支持 Windows 与 Unix/macOS 统一终端交互能力。
- [Bugfix] 修复 Terminal 在 Windows 环境无法使用 Unix 专属 PTY 实现的问题。
- [Refactor] 同步调整 ADR-005 架构决策文档，更新为"跨平台 PTY + WebSocket 直通"并对齐当前实现。

## [v1.1.1] - 2026-04-01
- [Refactor] 文档治理流程对齐：将"功能变更需同步维护 active_tasks 与 changelog"固化为常规交付要求。
- [Bugfix] 修复文档追踪链路不完整的问题，补齐活跃任务文档中的当日更新记录。

## [v1.1.0] - 2026-03-31
- [Refactor] 后端 Terminal consumer 从 subprocess 逐命令执行重构为 PTY 交互式 Shell（`pty.fork()` + `loop.add_reader()`）。
- [Feature] 支持 Tab 补全、方向键历史、Ctrl+C 中断、交互式程序（vim/top 等）。
- [Feature] 前端终端组件改为 PTY 直通模式，所有按键直接转发后端，Shell 自行回显。
- [Feature] 新增 `resize` 消息类型，窗口尺寸变化时自动同步到后端 PTY。
- [Feature] 终端 UI 采用 Tokyo Night 主题配色，完整 16 色 ANSI 调色板支持。
- [Feature] 安全审计保留：Enter 时拦截黑名单命令并显示红色 BLOCKED 提示。

## [v1.0.5] - 2026-03-31
- [Bugfix] 修复前端 `useMessage` 导入错误（element-plus 无此导出），替换为 `ElMessage`。
- [Bugfix] 新增 Vite WebSocket 代理规则 `/ws`，修复 WS 连接 pending 问题。
- [Bugfix] 后端 INSTALLED_APPS 添加 `daphne`，使 `runserver` 启用 ASGI 支持 WebSocket。
- [Bugfix] 修复后端命令输出 `\n` 未转换为 `\r\n` 导致 xterm.js 阶梯状渲染的问题。

## [v1.0.4] - 2026-03-31
- [Bugfix] 修复 Terminal 会话详情/命令历史/关闭接口在越权场景返回 HTTP 状态码不正确的问题，统一改为真实 404（不再返回 200 + code=404）。

## [v1.0.3] - 2026-03-31
- [Bugfix] 修复 Terminal WebSocket 认证与文档不一致问题：新增 JWT 认证中间件，支持 `?token=` 与 `Authorization Bearer`；同时前端 terminalWs 自动携带 token 建立连接。

## [v1.0.2] - 2026-03-31
- [Bugfix] 修复 Terminal 模块依赖声明缺失问题，在 backend/pyproject.toml 增加 channels==4.3.2 与 daphne==4.2.1，确保后端在新环境可加载 WebSocket 终端能力。

## [v1.0.1] - 2026-03-31
- [Feature] 新增 Stop 阶段自动汇总 Hook，执行 .github/hooks/scripts/update-changelog-summary.ps1 自动更新变更摘要。
- [Bugfix] 修复 Windows 环境下 Stop 阶段未触发更新摘要的问题，补充 hooks.windows.command 配置。
- [Refactor] 统一 Hook 配置结构，集中到 .github/hooks/changelog-auto-summary.json，便于后续维护与扩展。

## [v1.0.0] - 2026-03-31
- 项目目录结构重构，文档规范化
