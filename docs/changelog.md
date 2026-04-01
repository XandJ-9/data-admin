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

## [v1.1.1] - 2026-04-01
- [Refactor] 文档治理流程对齐：将“功能变更需同步维护 active_tasks 与 changelog”固化为常规交付要求。
- [Bugfix] 修复文档追踪链路不完整的问题，补齐活跃任务文档中的当日更新记录。

## [v1.1.2] - 2026-04-01
- [Feature] Terminal 后端升级为基于 pywinpty 的跨平台 PTY 进程模型，支持 Windows 与 Unix/macOS 统一终端交互能力。
- [Bugfix] 修复 Terminal 在 Windows 环境无法使用 Unix 专属 PTY 实现的问题。
- [Refactor] 同步调整 ADR-005 架构决策文档，更新为“跨平台 PTY + WebSocket 直通”并对齐当前实现。

## [v1.1.3] - 2026-04-01
- [Bugfix] 修复 macOS 无法安装/加载 `pywinpty` 导致 Terminal 模块启动失败的问题：后端改为按平台选择 PTY 实现（Windows 使用 `pywinpty`，macOS/Linux 使用 `ptyprocess`）。
- [Refactor] 调整 `backend/pyproject.toml` 依赖为平台条件安装，避免非 Windows 环境拉取 `pywinpty` 失败。

## [v1.2.0] - 2026-04-01
- [Feature] 前端 xterm 升级至 v6（@xterm/xterm），启用 WebGL 渲染、Web Links 可点击链接、Search 搜索、Unicode11 宽字符支持。
- [Feature] 前端终端新增搜索栏（Ctrl+Shift+F），支持上下查找、ESC 关闭。
- [Feature] WebSocket 管理器增加自动重连（指数退避，最多 8 次）+ 双向心跳保活。
- [Feature] 后端 consumer 增加服务端心跳、空闲超时（30 分钟自动关闭）、PTY 环境隔离（白名单环境变量）。
- [Feature] 状态栏显示终端尺寸（cols×rows），连接状态中文化。
- [Feature] 支持 macOS Option→Meta 映射、右键选词、Ctrl+Shift+C/V 复制粘贴快捷键透传。
- [Refactor] 安全模块扩展：新增 Windows 危险命令黑名单、正则检测 fork bomb/reverse shell/sudo/curl|sh 等模式、管道分段解析优化。
- [Refactor] 使用 ResizeObserver 替代 window.resize，终端尺寸同步更精准。

## [v1.2.1] - 2026-04-01
- [Bugfix] 修复 Unix PTY 读取数据竞争：将 `asyncio.wait_for(to_thread)` 替换为 `loop.add_reader(fd)` + `os.read(fd)`，消除键盘输入不可见问题。
- [Bugfix] 修复 pywinpty/ptyprocess 读写 API 不一致（str vs bytes）导致的编码错误，添加平台适配层。

## [v1.3.0] - 2026-04-01
- [Feature] 终端多标签页：支持新建终端 Tab（最多 8 个），每个 Tab 独立 PTY 会话、独立 WebSocket 连接。
- [Feature] 终端会话历史页面重写：双标签页布局（会话记录 + 命令历史），会话列表支持状态/日期范围筛选，命令历史支持关键词/会话 ID 过滤。
- [Feature] 会话列表新增命令数（commandCount）和时长（duration）列。
- [Refactor] 后端 TerminalSessionSerializer 新增 commandCount（annotate 聚合）、duration（时长计算）、updateTime 字段。
- [Refactor] 后端 TerminalSessionViewSet.list() 支持 status/host/beginTime/endTime 查询参数。
- [Refactor] 后端 TerminalCommandViewSet.recent() 支持分页 + keyword + sessionId 过滤。
- [Refactor] 移除命令输出缓冲机制：output 字段仅用于记录 blocked 命令的拦截原因，不再尝试捕获 PTY 输出（shell 输出格式不可控、异步间隙丢数据、ANSI 清理不可靠）。
- [Refactor] 会话历史页面移除"关闭"操作按钮（审计视角不需要操作入口）和"输出"查看功能。
