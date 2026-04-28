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
2. `datasource` 已移除 snapshot 与 `DatabaseAssetSyncRun`；当前采集运行记录统一进入 `datatask.TaskInstance`，`datasource` 内只保留正式采集任务定义 `DataSourceCollectionTask`。
3. `dataintegration` 已改为直接填写 `sourceDatabaseName` / `sourceTableName`。
4. 删除数据源不会再被历史集成任务阻塞；若数据源被删，相关集成任务需重新绑定后才能继续执行，自动生成的源数据采集任务会一并回收。
5. `datadev` 当前只保留 `DataDevScript` / `DataDevModel` 作为业务任务定义，脚本调试执行、建模执行与历史执行记录统一进入 `datatask.TaskInstance`，不再保留 `DataDevScriptExecution` 私有执行表。
6. 登录链路当前包含验证码校验与失败次数限流。
7. `dataasset` 已建立 `facades/` 公开边界，元数据采集与规范资产同步默认通过 facade 进入，不再把 `services.py` 视为跨模块公共入口。
8. 任务运维执行记录页与任务详情页当前会直接展示 `datasource.collection` 的执行结果、失败原因与采集进度摘要；存在进行中实例时页面会自动轮询刷新状态。
9. `datasource.collection` 的僵尸实例纠偏当前由 `datasource` 通过 source handler 注册后台清理钩子给 `datatask.scheduler`，任务运维页与任务详情页的 GET 读取链路不再执行失联恢复或写数据库。
10. 任务运维执行记录列表当前采用“任务对象 / 实例与触发 / 状态 / 执行时间 / 执行情况”的组合列展示，减少原始字段平铺，便于运维快速扫读。
11. 执行记录列表中的“执行情况”列当前默认压缩为紧凑单行摘要，错误信息超长时省略显示并通过悬停 tooltip 查看完整内容，避免长文案把整行高度撑开。
12. 数据服务接口执行弹窗当前统一通过 `/dataservice/interface-info/{id}/export` 导出结果，不再使用不存在的 `/export-data` 路径。
13. `dataservice` 当前已补齐面向前端调用面的集成回归：`query`、`query-log`、`interface-info`、`interface-field`、`report-info` 及运行时导入导出相关入口均通过项目根路由实测覆盖。
14. 报表与接口关联关系当前在更新和删除前会清理历史已删除重复记录，避免同一报表重复编辑后再删除时触发软删除唯一约束冲突。
15. `dataservice` 的前端新增/更新接口当前会显式拦截重复 `interfaceCode` 与 `reportCode`，不再沿用通用基类的“按唯一键复用旧记录”行为，也不会把重复更新直接放到数据库唯一约束层报错。
16. `dataintegration` 当前已拆分为“模块首页 + 任务列表”两个正式菜单入口：模块首页只承载任务规模、焦点任务与导航入口，筛选、执行、详情抽屉与执行记录统一收敛到“任务列表”页面，不再把总览和工作台堆在同一页面；首页视觉样式也已收敛到和 `dataasset`、`dataservice` 一致的浅色模块首页风格。
17. 系统菜单管理页当前已修正“修改菜单”表单回填逻辑：菜单详情会先与默认表单合并并做字段归一化，菜单树加载失败也会被新增/修改入口正确兜底，避免显示状态、菜单状态等字段展示不全或产生未处理异常。

## 当前文档口径

1. `docs/README.md` 是统一文档入口。
2. `docs/changelog.md` 只保留近期有效变更摘要。
3. 历史信息统一进入 `docs/archive/`，不再继续堆在状态页与 README 中。
