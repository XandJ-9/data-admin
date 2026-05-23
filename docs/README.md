# Data Admin 文档中心

本文档中心按当前架构与后续开发协作方式重新组织。日常开发优先阅读本页列出的当前有效文档；历史评审稿和状态流水只作为追溯材料，不再作为默认设计入口。

## 1. 架构设计

架构设计用于说明平台整体分层、模块职责和模块间协作边界。每个实际模块单独维护一份设计说明。

- [架构设计总览](architecture/README.md)
- [平台整体架构](architecture/platform.md)
- [模块架构目录](architecture/modules/README.md)
- [架构决策记录](adr/README.md)
- [数据源模块](architecture/modules/datasource.md)
- [数据集成模块](architecture/modules/dataintegration.md)
- [数据开发模块](architecture/modules/datadev.md)
- [统一任务模块](architecture/modules/datatask.md)
- [数据资产模块](architecture/modules/dataasset.md)
- [数据服务模块](architecture/modules/dataservice.md)
- [系统管理模块](architecture/modules/system.md)
- [监控模块](architecture/modules/monitor.md)
- [Web Terminal 模块](architecture/modules/terminal.md)
- [执行器模块](architecture/modules/executors.md)
- [数据库适配模块](architecture/modules/dbutils.md)
- [公共后端能力模块](architecture/modules/common.md)
- [工具模块](architecture/modules/utils.md)
- [前端应用架构](architecture/modules/frontend.md)

## 2. 开发流程

开发流程沿用 `docs/developments` 下的现有规范，作为编码、建模块、联调和验收的主要依据。

- [开发流程目录](developments/README.md)
- [模块职责与执行边界指南](developments/module-responsibility-execution-guide.md)
- [后端开发约定](developments/backend-conventions.md)
- [前端开发约定](developments/frontend-conventions.md)
- [创建模块指南](developments/creating-modules.md)
- [快速参考](developments/quick-reference.md)
- [开发优先级纠偏](developments/development-priority-correction-2026-04-30.md)

## 3. 问题解决

问题解决用于沉淀开发过程中反复出现、曾经需要多轮尝试才能稳定解决的问题。

- [问题解决总览](troubleshooting/README.md)
- [反复问题处理手册](troubleshooting/repeated-issues.md)
- [xterm 生产构建压缩问题](troubleshooting/esbuild-xterm-requestMode-bug.md)

## 4. 历史参考

以下目录保留追溯价值，但不再作为当前设计入口。

- `docs/architecture/*review*.md`：历史评审稿。
- `docs/architecture/data-platform.md`：早期目标设想。
- `docs/requirements/active_tasks.md`：阶段状态记录。
- `docs/archive/`：历史归档。
- `docs/prompts/`：AI 协作提示词模板。
- `docs/changelog.md`：变更记录。

## 维护规则

1. 架构变化先更新对应模块架构文档，再更新入口页。
2. 新增全局基础技术方案或重大决策时，写入 `docs/adr/` 形成 ADR；模块局部实现细节留在模块架构文档。
3. 反复出现的问题写入 `docs/troubleshooting/repeated-issues.md`，不要只停留在聊天记录或临时状态页。
4. 历史材料如果与当前代码冲突，应在当前文档中给出最新口径，历史文件只保留追溯用途。
