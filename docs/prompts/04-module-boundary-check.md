# 模块边界检查提示词

适用场景：需求涉及 datasource、dataintegration、datadev、datatask、executors、dbutils、任务发布、调度、执行记录、数据库访问或模块重构。

```text
请先做模块边界判断，再决定是否开发。

必须读取：
- CLAUDE.md
- docs/adr/ADR-002-平台分层与五阶段职责.md
- docs/adr/ADR-003-统一任务内核与执行实例边界.md
- docs/developments/module-responsibility-execution-guide.md
- docs/requirements/active_tasks.md

边界判断问题：
1. 这个需求属于 ADR-002 的哪个阶段？
   - datasource：Connection & Discovery
   - dataintegration：Data Integration
   - datadev：Data Development
   - datatask：Orchestration & DataOps
   - dataasset/dataservice：Assetization & Service
2. 当前项目是否已有同职责或近似职责旧实现？
3. 如果是旧模块重做，是否需要先删除或收敛旧入口，而不是并行新增第二套表达？
4. 是否会让 datatask 直接理解业务模块内部字段？
5. 是否会把 datatask.Task 当成业务真身，而不是平台镜像？
6. 是否会新增业务模块私有执行历史表？
7. 是否会绕开 TaskInstance 作为唯一执行记录中心？
8. 是否会让业务模块自己实现数据库连接、SQL 执行、Spark/Hive/DataX 执行？
9. 是否应该把实际执行能力沉淀到 apps.executors？
10. 是否应该把数据库访问能力沉淀到 apps.dbutils？
11. 是否需要通过 source handler 接入 TaskService？
12. 是否需要区分“业务页面调试草稿”和“任务中心发布快照”？
13. 是否涉及权限码、菜单 seed、前端按钮权限三处一致性？
14. 是否需要同步 ADR、模块架构、active_tasks.md、changelog.md 或开发规范？

判断输出格式：

阶段归属：
<说明需求属于哪个阶段，为什么>

已有实现：
<说明查到了哪些已有实现，复用或替换策略是什么>

边界结论：
<说明应该放在哪个模块，不应该放在哪些模块>

执行链路：
<说明是否走 TaskService、source handler、TaskInstance、executors、dbutils>

风险：
<列出可能造成职责漂移、重复实现或数据不一致的风险>

下一步：
<只给本轮最小必要实施计划>
```

高风险红线：

- 不要在 datasource、dataintegration、datadev 中新增正式私有执行记录中心。
- 不要让 datatask 反向 import 业务模块内部模型并写分支逻辑。
- 不要把完整业务配置迁移到 Task 里替代业务模型。
- 不要让业务模块手写外部数据库驱动连接。
- 不要让草稿变更自动污染任务中心已发布快照。
