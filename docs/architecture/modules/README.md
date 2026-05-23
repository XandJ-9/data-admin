# 模块架构目录

每个实际模块维护一份独立设计说明，用于回答四类问题：

1. 这个模块负责什么。
2. 这个模块不负责什么。
3. 它与其他模块如何协作。
4. 后续开发必须遵守哪些约束。

## 模块文档

- [datasource：数据源与元数据发现](datasource.md)
- [dataintegration：数据集成](dataintegration.md)
- [datadev：数据开发](datadev.md)
- [datatask：统一任务内核](datatask.md)
- [dataasset：数据资产](dataasset.md)
- [dataservice：数据服务](dataservice.md)
- [system：系统管理与权限](system.md)
- [monitor：监控与审计](monitor.md)
- [terminal：Web Terminal](terminal.md)
- [executors：执行器](executors.md)
- [dbutils：数据库适配](dbutils.md)
- [common：公共后端能力](common.md)
- [utils：工具模块](utils.md)
- [frontend：前端应用](frontend.md)

## 编写规则

1. 模块文档写设计边界，不写接口流水账。
2. 新增模型、运行链路或跨模块依赖时，必须同步更新对应模块文档。
3. 如果模块文档与历史 ADR 冲突，以模块文档和当前代码为准，再视情况补充新的决策说明。
