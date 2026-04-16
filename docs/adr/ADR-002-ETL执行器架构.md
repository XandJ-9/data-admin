# ADR-002: ETL 执行器插件化架构

**Status**: Superseded  
**Date**: 2026-03-31
**Superseded Date**: 2026-04-16

> 说明：`apps.dataetl` 模块已在 2026-04-16 从主干移除，本 ADR 仅作为历史归档保留。

## Context

ETL 模块需要支持多种执行引擎（模拟执行、DataX、Spark SQL、Python脚本），且未来可能扩展更多类型。需要一种可扩展的执行器架构。

## Decision

采用插件式 Executor 架构：
- 定义抽象基类 `BaseExecutor`，约定 `execute()` / `validate()` 等接口
- 每种执行器单独实现为一个模块（`datax_executor.py`、`mock_executor.py` 等）
- `ExecutionService` 通过 `executor_type` 字段动态 dispatch 对应执行器
- 配置生成逻辑单独抽取为 `datax_config_builder.py`，避免执行器文件过大

目录结构：
```
apps/dataetl/executors/
├── base.py                 # 抽象接口
├── mock_executor.py        # 模拟执行器
├── datax_executor.py       # DataX 执行器
└── datax_config_builder.py # DataX 配置生成
```

## Consequences

**优点**:
- 新增执行器只需实现接口，不修改现有代码（OCP 原则）
- 便于单元测试各执行器

**缺点/风险**:
- `datax_executor.py`（377行）和 `datax_config_builder.py`（353行）已超200行限制，需进一步拆分
- 执行器间无统一错误码，错误信息格式不一致
