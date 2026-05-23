# 架构设计

本目录只放当前有效的架构说明。历史评审稿和早期设想仍保留在本目录中，但不再作为默认入口。

## 当前入口

1. [平台整体架构](platform.md)
2. [模块架构目录](modules/README.md)
3. [数据源模块](modules/datasource.md)
4. [数据集成模块](modules/dataintegration.md)
5. [数据开发模块](modules/datadev.md)
6. [统一任务模块](modules/datatask.md)
7. [数据资产模块](modules/dataasset.md)
8. [数据服务模块](modules/dataservice.md)
9. [系统管理模块](modules/system.md)
10. [监控模块](modules/monitor.md)
11. [Web Terminal 模块](modules/terminal.md)
12. [执行器模块](modules/executors.md)
13. [数据库适配模块](modules/dbutils.md)
14. [公共后端能力模块](modules/common.md)
15. [工具模块](modules/utils.md)
16. [前端应用架构](modules/frontend.md)

## 当前架构口径

1. 平台按“连接发现、数据集成、数据开发、任务运维、资产服务”五阶段组织主链路。
2. 业务模块负责业务定义和单次调试入口，`datatask` 负责统一任务镜像、依赖、调度索引和执行实例。
3. 执行能力向 `executors` / `dbutils` 收敛，避免在业务模块中重复实现数据库驱动或运行器。
4. 资产语义由 `dataasset` 统一沉淀，跨模块写入通过 facade 完成。

## 历史参考

以下文件保留用于追溯，不建议作为新开发的直接依据：

- `backend-architecture-review-2026-04-28.md`
- `datatask-architecture-review-2026-04-29.md`
- `platform-target-architecture-2026-04-30.md`
- `data-platform.md`
- `data-admin-architecture.html`
