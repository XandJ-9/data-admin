# frontend 应用架构

## 模块定位

`frontend` 是平台 Web 应用，基于 Vue 3、Element Plus、Vite、Pinia 和动态路由构建。

前端按后端模块组织页面入口，菜单数据由 `system` 模块提供，页面路径必须与菜单种子保持一致。

## 页面结构

当前数据平台主入口位于 `frontend/src/views/data`：

- `asset/`：数据资产。
- `datasource/`：数据源。
- `dev/`：数据开发。
- `integration/`：数据集成。
- `service/`：数据服务。
- `task/`：任务运维。

系统、监控和终端入口分别位于：

- `views/system/`
- `views/monitor/`
- `views/terminal/`

## 设计约束

1. 模块首页只展示概览、焦点数据和导航入口，不把筛选、详情、执行记录全部堆在首页。
2. 列表、详情、日志和执行记录等具体工作台下沉到模块子页面。
3. 前端 API 封装必须对应真实后端路由，发现断链入口应清理或修复。
4. 菜单 component 路径以系统菜单种子为准，前后端一起维护。
5. 构建脚本同时支持 `pnpm build` 与 `pnpm build:prod`，两者都执行生产构建。

## 已收敛规则

1. `/data-orchestration` 历史入口已停用，任务运维统一走 `views/data/task/`。
2. 未接入后端的历史 monitor job、tool gen、datastudio 等 API 和页面应保持清理状态。
3. 数据模块首页视觉风格以浅色、工作台式、信息扫描为主。
4. 生产构建涉及 xterm 时，需遵守 troubleshooting 中的压缩规避方案。

## 演进方向

1. 持续以模块工作流拆分页面，减少单页超载。
2. 将权限按钮、状态标签、任务实例摘要等模式沉淀为可复用组件。
3. 前端路由、菜单种子和后端权限码保持同步维护。
