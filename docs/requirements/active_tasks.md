# 当前任务状态（现状优先）

本文件只记录当前主线与近期待确认事项，避免历史信息干扰决策。

## 当前主线（2026-04-25）

1. 平台边界已按 ADR-011 收敛为五阶段职责模型：
   - `datasource` 负责 Connection & Discovery
   - `dataintegration` 负责 Data Integration
   - `datadev` 负责 Data Development
   - `datatask` 负责 Orchestration & DataOps
   - `dataasset` 负责 Assetization & Service
2. `dataintegration` 与 `datadev` 已通过注册式 `task_source.py` 接入统一任务中心，`datatask` 仅保留任务内核与分发协议。
3. 数据源执行上下文已统一复用 `apps.datasource.executor_info`，避免跨模块重复解密与拼接连接信息。
4. `datasource` 当前已临时移除源表快照、源字段快照与元数据采集任务能力，Phase 1 暂收敛为“连接管理 + 库表字段发现”。
5. `dataintegration` 新建/编辑任务已改为直接填写 `sourceDatabaseName` 与 `sourceTableName`，不再依赖 `datasource` 的 snapshot 选择链路。
6. `dataintegration` 对 `datasource` 的引用已改为可解绑：删除无效数据源时不再被集成任务阻塞，但相关任务会进入“缺少数据源绑定”的状态，需重新选择后再执行。

## 近期待确认

1. 文档体系收敛已完成首轮：建立 `docs/README.md` 统一入口，活跃文档改为“当前视图 + 历史归档”。
2. 后续若继续模块重构，必须先以 ADR-011 判阶段归属，再执行“先扫描旧实现、先删后建”。
3. 需要补一次文档一致性巡检（README、模块说明、菜单说明）确保不再出现失效链接或历史语义残留。

## 最近完成里程碑（精简）

1. `datadev` 后端边界收敛：业务执行与回写逻辑迁回 `datadev` 来源处理器。
2. `dataintegration` 后端边界收敛：统一任务生命周期同步与执行事实收敛到 `TaskInstance`。
3. 开发流程与分支规范已固化到 `CLAUDE.md` 与开发文档。
4. 数据源模块“源数据查看”入口已回归为“快捷查看 + 详情深入”双路径。

## 历史归档

- 完整历史记录：`docs/archive/active_tasks-history-2026-04-25.md`
- 历史仅用于追溯，不作为当前决策入口。
