# 版本更新日志

本文件用于记录 Data Admin 项目的所有版本变更、修复与新特性。

## [v1.0.0] - 2026-03-31
- 项目目录结构重构，文档规范化
- ...（后续版本内容请在此补充）

## [v1.0.1] - 2026-03-31
- [Feature] 新增 Stop 阶段自动汇总 Hook，执行 .github/hooks/scripts/update-changelog-summary.ps1 自动更新变更摘要。
- [Bugfix] 修复 Windows 环境下 Stop 阶段未触发更新摘要的问题，补充 hooks.windows.command 配置。
- [Refactor] 统一 Hook 配置结构，集中到 .github/hooks/changelog-auto-summary.json，便于后续维护与扩展。

## [v1.0.2] - 2026-03-31
- [Bugfix] 修复 Terminal 模块依赖声明缺失问题，在 backend/pyproject.toml 增加 channels==4.3.2 与 daphne==4.2.1，确保后端在新环境可加载 WebSocket 终端能力。

## [v1.0.3] - 2026-03-31
- [Bugfix] 修复 Terminal WebSocket 认证与文档不一致问题：新增 JWT 认证中间件，支持 `?token=` 与 `Authorization Bearer`；同时前端 terminalWs 自动携带 token 建立连接。

## [v1.0.4] - 2026-03-31
- [Bugfix] 修复 Terminal 会话详情/命令历史/关闭接口在越权场景返回 HTTP 状态码不正确的问题，统一改为真实 404（不再返回 200 + code=404）。

## [v1.0.5] - 2026-03-31
- [Bugfix] 修复前端 `useMessage` 导入错误（element-plus 无此导出），替换为 `ElMessage`。
- [Bugfix] 新增 Vite WebSocket 代理规则 `/ws`，修复 WS 连接 pending 问题。
- [Bugfix] 后端 INSTALLED_APPS 添加 `daphne`，使 `runserver` 启用 ASGI 支持 WebSocket。
- [Bugfix] 修复后端命令输出 `\n` 未转换为 `\r\n` 导致 xterm.js 阶梯状渲染的问题。

## [v1.1.0] - 2026-03-31
- [Refactor] 后端 Terminal consumer 从 subprocess 逐命令执行重构为 PTY 交互式 Shell（`pty.fork()` + `loop.add_reader()`）。
- [Feature] 支持 Tab 补全、方向键历史、Ctrl+C 中断、交互式程序（vim/top 等）。
- [Feature] 前端终端组件改为 PTY 直通模式，所有按键直接转发后端，Shell 自行回显。
- [Feature] 新增 `resize` 消息类型，窗口尺寸变化时自动同步到后端 PTY。
- [Feature] 终端 UI 采用 Tokyo Night 主题配色，完整 16 色 ANSI 调色板支持。
- [Feature] 安全审计保留：Enter 时拦截黑名单命令并显示红色 BLOCKED 提示。
