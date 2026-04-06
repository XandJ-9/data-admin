# 版本更新日志

本文件用于记录 Data Admin 项目的所有版本变更、修复与新特性。

## [v1.4.5] - 2026-04-06
- [Feature] 数据开发执行引擎策略调整：脚本执行统一按 Spark SQL 引擎提交，不再依赖创建时选择数据源。
- [Refactor] 新建脚本弹窗简化：移除数据源选择项，执行器明确为“Spark SQL 执行引擎（固定）”。
- [Feature] 版本历史视图增强：新增“全部/正式/草稿”筛选，支持同时查看历史正式版本与草稿版本。
- [Docs] ADR-006 补充执行引擎策略：新增“执行引擎策略补充（2026-04-06）”并明确版本区可见性要求。

## [v1.4.4] - 2026-04-06
- [Feature] 数据开发 IDE 中央编辑区升级为多页签模式，支持并行打开多个脚本并快速切换。
- [Feature] 新增页签未保存保护：关闭存在变更的脚本页签时弹出确认，避免误关闭。
- [Refactor] 编辑器工具栏视觉重构：增加当前文档信息胶囊与语言标识，执行按钮文案调整为“运行当前文档”。
- [Refactor] 左侧资源区样式升级：按 ADR-006“资源导航树”语义优化层级展示与脚本分组可读性。
- [Refactor] 数据开发页面整体 UI 升级为统一 IDE 风格，并补充移动端断点下的可用布局。

## [v1.4.3] - 2026-04-06
- [Feature] 数据开发编辑器新增“发布”按钮：在“保存草稿版本”之外，支持发布正式可用版本。
- [Feature] 版本管理升级：草稿脚本允许入版本表，并通过版本字段标记为“草稿（非正式可用）/正式可用”。
- [Feature] 后端新增发布接口：`POST /datadev/scripts/{id}/versions/publish`，发布时自动创建正式版本并更新脚本状态为 `published`。
- [Feature] 版本历史视图增强：右侧版本列表新增“草稿/正式”标签，便于区分可用性。

## [v1.4.2] - 2026-04-06
- [Feature] 数据开发分层目录树支持点击联动筛选：点击 ODS/DWD/DWS/ADS 层级节点后，“我的脚本”仅显示当前分层脚本。
- [Feature] 分层筛选支持快速切换：点击同一层级节点可取消筛选并恢复全部脚本视图。
- [Feature] 新建 SQL 脚本对话框增强分层联动：从分层/数据源节点触发新建时，自动预填脚本 `layer` 字段。

## [v1.4.1] - 2026-04-05
- [Bugfix] 修复数据开发 IDE 执行状态误导：前端调用执行接口后不再直接显示“执行成功”，改为“已提交（待执行）”。
- [Refactor] 对齐后端当前能力边界：执行接口现阶段仅落库 `pending` 执行记录，待后续对接 `apps.executors` 实际执行链路。
- [Feature] 新增前端执行状态轻量轮询：提交后自动跟进状态变化并刷新执行记录，轮询超时时提示用户稍后查看。
- [Bugfix] 修复执行状态轮询并发污染：切换脚本或重复执行时主动清理旧轮询器，避免多定时器同时写入状态。
- [Bugfix] 修复 `cancelled` 状态显示不一致：状态栏与执行记录统一展示为“已取消”，不再误映射为“失败”。

## [v1.4.0] - 2026-04-05
- [Feature] 新增数据开发模块后端（`apps.datadev`）：
  - 实现三个核心模型：`DataDevScript`（脚本资产）、`DataDevScriptVersion`（版本快照）、`DataDevScriptExecution`（执行记录）
  - 实现完整 RESTful API：脚本 CRUD、版本创建/回滚、执行触发、执行记录查询
  - 路由注册：`data-api/datadev/scripts`、`data-api/datadev/executions`
  - 数据库迁移已生成并执行
- [Architecture] 遵循 ADR-006 决策：模型独立，执行层预留复用 `apps.executors` 适配接口

## [v1.3.8] - 2026-04-05
- [Feature] 顶部导航点击父级菜单时，除联动侧边栏外新增自动路由跳转：优先使用路由 `redirect`，否则跳转首个子路由，避免仅展开不跳转。
- [Bugfix] 修复浏览器控制台 `Added non-passive event listener to a scroll-blocking 'wheel' event` 性能警告：在应用初始化阶段统一为 `wheel/touchstart/touchmove` 事件补充 `passive` 默认值，提升滚动响应性。

## [v1.3.7] - 2026-04-05
- [Docs] 新增 ADR-006，明确数据开发模块架构决策：定位为脚本研发中心（SQL/Python），首期聚焦脚本资产管理、版本管理与执行记录查询。
- [Refactor] 明确数据开发与 ETL 边界：脚本域模型独立，执行层复用 `apps.executors`，不重复建设执行器体系。
- [Docs] 同步更新 active_tasks，建立后续模块实施的文档基线。

## [v1.3.6] - 2026-04-05
- [Refactor] 将 ETL 执行器基础能力抽象为通用模块：新增 `apps.executors`（`BaseExecutor`、`ExecutorFactory`）。
- [Refactor] `apps.dataetl.executors.base` 改为兼容转发层，继续导出 `BaseETLExecutor` 与 `ExecutorFactory`，确保历史导入路径无缝可用。
- [Feature] 为后续非 ETL 业务复用执行器注册与实例化机制提供统一入口，降低模块耦合。

## [v1.3.5] - 2026-04-04
- [Refactor] 字典管理页面代码质量改进：
  - 添加统一的错误处理函数 `handleApiError`，区分开发/生产环境错误输出
  - 所有 API 调用添加 `.catch()` 错误处理和 `.finally()` 清理逻辑
  - 修复非严格相等比较（`!=` → `!==`）
  - 迁移至标准 ref 引用方式（`dictRef.value?.validate`），替代 `proxy.$refs`
  - 添加字典数据防御性检查（`sys_normal_disable = []`）
  - 使用 `defineOptions` 替代 `<script setup name="Dict">` 语法
  - 改进删除操作错误处理，区分用户取消和真实错误
  - 显式导入 Vue Composition API（`ref`, `reactive`, `toRefs`, `getCurrentInstance`）
  - 使用模板字符串替代字符串拼接

## [v1.3.4] - 2026-04-03
- [Bugfix] 切换生产构建压缩器为 terser，修复 esbuild 对 `@xterm/xterm` TypeScript 枚举 IIFE 二次压缩时丢失 `let` 变量声明，导致 ESM 严格模式下 `requestMode` 抛出 `ReferenceError: i is not defined` 的问题。详见 `docs/postmortem/esbuild-xterm-requestMode-bug.md`。

## [v1.3.3] - 2026-04-03
- [Bugfix] 修复 Nginx 反向代理下浏览器终端 vim 等全屏程序无法正常使用的问题：WebSocket location 添加 `proxy_buffering off` 禁用响应缓冲，确保 PTY 输出逐帧实时转发；同时添加 `proxy_send_timeout 3600s` 防止发送方向空闲断连。

## [v1.3.2] - 2026-04-03
- [Bugfix] 修复 ASGI 入口（config/asgi.py）模块导入顺序问题：将 JwtAuthMiddleware 导入移到 `get_asgi_application()` 之后，解决 Gunicorn + Uvicorn Worker 启动时 Django 未初始化报错。
- [Bugfix] 确认 Gunicorn + Uvicorn Worker 无法正确路由 Django Channels 的 WebSocket 请求（返回 404），生产环境必须使用 Daphne。
- [Feature] README.md 新增完整生产环境部署指南：系统要求、后端/前端部署步骤、Nginx 反向代理配置（含 WebSocket）、Systemd 服务管理、性能调优建议、常见问题排查。
- [Feature] quick-reference.md 新增生产环境部署速查：快速部署流程、应用服务器兼容性说明、部署检查清单、部署验证命令。
- [Refactor] 删除错误的 pnpm-workspace.yaml 配置文件，修复前端 pnpm 启动失败问题。
- [Refactor] 统一部署文档推荐 Daphne 作为唯一应用服务器，移除 Gunicorn/uWSGI 方案。

## [v1.3.1] - 2026-04-02
- [Bugfix] 修复 Windows 终端 PTY 读取无响应问题：pywinpty PtyProcess.read() 不接受 timeout 参数，改为 read(4096)，修复 TypeError 被静默捕获问题。
- [Bugfix] 增加进程退出时剩余输出的排空逻辑，确保数据完整性。
- [Bugfix] 前端添加缺失的 sortablejs 依赖。
- [Bugfix] 配置 pnpm 允许 esbuild 和 vue-demi 执行构建脚本，解决依赖加载失败问题。

## [v1.3.0] - 2026-04-01
- [Feature] 终端多标签页：支持新建终端 Tab（最多 8 个），每个 Tab 独立 PTY 会话、独立 WebSocket 连接。
- [Feature] 终端会话历史页面重写：双标签页布局（会话记录 + 命令历史），会话列表支持状态/日期范围筛选，命令历史支持关键词/会话 ID 过滤。
- [Feature] 会话列表新增命令数（commandCount）和时长（duration）列。
- [Refactor] 后端 TerminalSessionSerializer 新增 commandCount（annotate 聚合）、duration（时长计算）、updateTime 字段。
- [Refactor] 后端 TerminalSessionViewSet.list() 支持 status/host/beginTime/endTime 查询参数。
- [Refactor] 后端 TerminalCommandViewSet.recent() 支持分页 + keyword + sessionId 过滤。
- [Refactor] 移除命令输出缓冲机制：output 字段仅用于记录 blocked 命令的拦截原因，不再尝试捕获 PTY 输出（shell 输出格式不可控、异步间隙丢数据、ANSI 清理不可靠）。
- [Refactor] 会话历史页面移除"关闭"操作按钮（审计视角不需要操作入口）和"输出"查看功能。

## [v1.2.1] - 2026-04-01
- [Bugfix] 修复 Unix PTY 读取数据竞争：将 `asyncio.wait_for(to_thread)` 替换为 `loop.add_reader(fd)` + `os.read(fd)`，消除键盘输入不可见问题。
- [Bugfix] 修复 pywinpty/ptyprocess 读写 API 不一致（str vs bytes）导致的编码错误，添加平台适配层。

## [v1.2.0] - 2026-04-01
- [Feature] 前端 xterm 升级至 v6（@xterm/xterm），启用 WebGL 渲染、Web Links 可点击链接、Search 搜索、Unicode11 宽字符支持。
- [Feature] 前端终端新增搜索栏（Ctrl+Shift+F），支持上下查找、ESC 关闭。
- [Feature] WebSocket 管理器增加自动重连（指数退避，最多 8 次）+ 双向心跳保活。
- [Feature] 后端 consumer 增加服务端心跳、空闲超时（30 分钟自动关闭）、PTY 环境隔离（白名单环境变量）。
- [Feature] 状态栏显示终端尺寸（cols×rows），连接状态中文化。
- [Feature] 支持 macOS Option→Meta 映射、右键选词、Ctrl+Shift+C/V 复制粘贴快捷键透传。
- [Refactor] 安全模块扩展：新增 Windows 危险命令黑名单、正则检测 fork bomb/reverse shell/sudo/curl|sh 等模式、管道分段解析优化。
- [Refactor] 使用 ResizeObserver 替代 window.resize，终端尺寸同步更精准。

## [v1.1.3] - 2026-04-01
- [Bugfix] 修复 macOS 无法安装/加载 `pywinpty` 导致 Terminal 模块启动失败的问题：后端改为按平台选择 PTY 实现（Windows 使用 `pywinpty`，macOS/Linux 使用 `ptyprocess`）。
- [Refactor] 调整 `backend/pyproject.toml` 依赖为平台条件安装，避免非 Windows 环境拉取 `pywinpty` 失败。

## [v1.1.2] - 2026-04-01
- [Feature] Terminal 后端升级为基于 pywinpty 的跨平台 PTY 进程模型，支持 Windows 与 Unix/macOS 统一终端交互能力。
- [Bugfix] 修复 Terminal 在 Windows 环境无法使用 Unix 专属 PTY 实现的问题。
- [Refactor] 同步调整 ADR-005 架构决策文档，更新为"跨平台 PTY + WebSocket 直通"并对齐当前实现。

## [v1.1.1] - 2026-04-01
- [Refactor] 文档治理流程对齐：将"功能变更需同步维护 active_tasks 与 changelog"固化为常规交付要求。
- [Bugfix] 修复文档追踪链路不完整的问题，补齐活跃任务文档中的当日更新记录。

## [v1.1.0] - 2026-03-31
- [Refactor] 后端 Terminal consumer 从 subprocess 逐命令执行重构为 PTY 交互式 Shell（`pty.fork()` + `loop.add_reader()`）。
- [Feature] 支持 Tab 补全、方向键历史、Ctrl+C 中断、交互式程序（vim/top 等）。
- [Feature] 前端终端组件改为 PTY 直通模式，所有按键直接转发后端，Shell 自行回显。
- [Feature] 新增 `resize` 消息类型，窗口尺寸变化时自动同步到后端 PTY。
- [Feature] 终端 UI 采用 Tokyo Night 主题配色，完整 16 色 ANSI 调色板支持。
- [Feature] 安全审计保留：Enter 时拦截黑名单命令并显示红色 BLOCKED 提示。

## [v1.0.5] - 2026-03-31
- [Bugfix] 修复前端 `useMessage` 导入错误（element-plus 无此导出），替换为 `ElMessage`。
- [Bugfix] 新增 Vite WebSocket 代理规则 `/ws`，修复 WS 连接 pending 问题。
- [Bugfix] 后端 INSTALLED_APPS 添加 `daphne`，使 `runserver` 启用 ASGI 支持 WebSocket。
- [Bugfix] 修复后端命令输出 `\n` 未转换为 `\r\n` 导致 xterm.js 阶梯状渲染的问题。

## [v1.0.4] - 2026-03-31
- [Bugfix] 修复 Terminal 会话详情/命令历史/关闭接口在越权场景返回 HTTP 状态码不正确的问题，统一改为真实 404（不再返回 200 + code=404）。

## [v1.0.3] - 2026-03-31
- [Bugfix] 修复 Terminal WebSocket 认证与文档不一致问题：新增 JWT 认证中间件，支持 `?token=` 与 `Authorization Bearer`；同时前端 terminalWs 自动携带 token 建立连接。

## [v1.0.2] - 2026-03-31
- [Bugfix] 修复 Terminal 模块依赖声明缺失问题，在 backend/pyproject.toml 增加 channels==4.3.2 与 daphne==4.2.1，确保后端在新环境可加载 WebSocket 终端能力。

## [v1.0.1] - 2026-03-31
- [Feature] 新增 Stop 阶段自动汇总 Hook，执行 .github/hooks/scripts/update-changelog-summary.ps1 自动更新变更摘要。
- [Bugfix] 修复 Windows 环境下 Stop 阶段未触发更新摘要的问题，补充 hooks.windows.command 配置。
- [Refactor] 统一 Hook 配置结构，集中到 .github/hooks/changelog-auto-summary.json，便于后续维护与扩展。

## [v1.0.0] - 2026-03-31
- 项目目录结构重构，文档规范化
