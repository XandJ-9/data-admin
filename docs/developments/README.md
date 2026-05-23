# 开发流程

本目录保留当前仍在使用的开发规范、流程说明和快速参考。开发时优先按本文档顺序阅读。

## 推荐阅读顺序

1. [快速参考](quick-reference.md)
2. [模块职责与执行边界指南](module-responsibility-execution-guide.md)
3. [后端开发约定](backend-conventions.md)
4. [前端开发约定](frontend-conventions.md)
5. [创建模块指南](creating-modules.md)
6. [开发优先级纠偏](development-priority-correction-2026-04-30.md)

## 开发原则

1. 先确认模块边界，再动模型、接口和页面。
2. 业务定义、平台任务镜像、执行实例三者不要混写。
3. 新增后端能力时同步考虑权限码、菜单种子、测试和前端入口。
4. 新增前端入口时确认后端真实路由存在，不保留未接通页面。
5. 遇到反复排查的问题，沉淀到 `docs/troubleshooting/`。
