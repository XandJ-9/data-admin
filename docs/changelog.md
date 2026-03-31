# 版本更新日志

本文件用于记录 Data Admin 项目的所有版本变更、修复与新特性。

## [v1.0.0] - 2026-03-31
- 项目目录结构重构，文档规范化
- ...（后续版本内容请在此补充）

## [v1.0.1] - 2026-03-31
- [Feature] 新增 Stop 阶段自动汇总 Hook，执行 .github/hooks/scripts/update-changelog-summary.ps1 自动更新变更摘要。
- [Bugfix] 修复 Windows 环境下 Stop 阶段未触发更新摘要的问题，补充 hooks.windows.command 配置。
- [Refactor] 统一 Hook 配置结构，集中到 .github/hooks/changelog-auto-summary.json，便于后续维护与扩展。
