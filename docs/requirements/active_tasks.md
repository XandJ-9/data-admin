# 任务追踪


### 2026-04-02: Windows 终端 PTY 读取稳定性修复（v1.3.1）

- 修复 Windows 终端 PTY 读取无响应问题：pywinpty `PtyProcess.read()` 不接受 timeout 参数，改为 `read(4096)` 直接传入 buffer size
- 增加进程退出时剩余输出的排空逻辑，确保所有输出都被捕获并转发到前端
- 前端添加缺失的 sortablejs 依赖（多标签页拖拽排序）
- 配置 pnpm `onlyBuiltDependencies` 允许 esbuild 和 vue-demi 执行构建脚本，解决依赖加载失败

### 2026-04-01: PTY 数据竞争修复 + 多标签终端 + 会话历史优化（v1.2.1 ~ v1.3.0）

- 修复 Unix PTY 读取数据竞争（`loop.add_reader(fd)` 替代 `asyncio.wait_for(to_thread)`），解决键盘输入不可见
- 终端支持多标签页（最多 8 个 Tab），每个 Tab 独立 PTY + WebSocket
- 会话历史页重写：双标签页（会话记录 + 命令历史），支持状态/日期/关键词/会话 ID 筛选
- 后端 Serializer 新增 commandCount/duration/updateTime，ViewSet 新增列表筛选和分页
- 移除命令输出缓冲机制（shell 输出格式不可控），output 字段仅记录 blocked 命令原因
- 会话历史页移除无意义的"关闭"按钮和"输出"查看功能

### 2026-04-01: Web Terminal 全面优化（v1.2.0）

- 前端 xterm 升级至 v6，加载 WebGL/WebLinks/Search/Unicode11 四个 addon
- WebSocket 管理器增加自动重连（指数退避 × 8 次）与双向心跳保活
- 后端 consumer 增加服务端心跳、空闲超时自动关闭、PTY 环境变量白名单隔离
- 安全模块扩展 Windows 黑名单命令 + 正则检测危险模式（fork bomb、reverse shell、sudo 等）
- 终端 UI 增加搜索栏（Ctrl+Shift+F）、尺寸显示、macOS 快捷键适配

### 2026-04-01: Terminal macOS 依赖兼容修复

- 修复 `pywinpty` 在 macOS 环境不可安装导致后端启动失败问题
- `backend/apps/terminal/consumers.py` 改为按平台加载 PTY 后端：Windows 使用 `pywinpty`，macOS/Linux 使用 `ptyprocess`
- `backend/pyproject.toml` 依赖改为平台条件安装，避免非 Windows 环境错误拉取 `pywinpty`

### 2026-04-01: 同步最新 Git 变更（fc066de）

- 后端 terminal consumer 升级为基于 `pywinpty` 的跨平台 PTY 实现，支持 Windows 终端场景
- 依赖清单新增 `pywinpty>=2.0.0`（`backend/pyproject.toml` 与 `backend/uv.lock`）
- ADR-005 已同步更新为“跨平台 PTY + WebSocket 直通”决策说明，消除文档与实现不一致

### 2026-04-01: 文档信息同步更新

- 按项目指引补充文档更新追踪：同步维护活跃任务与版本日志
- 统一变更记录口径，后续功能点落地时需同时更新 `docs/requirements/active_tasks.md` 与 `docs/changelog.md`

### 2026-03-31: 清理调试代码

- 删除 `vite.config.js` 中的 `console.log` 环境变量打印
- 修复 `request.js` 请求拦截器中 `Promise.reject` 未 return 的 bug，删除 debug 日志
- 删除 `datasource/detail.vue` 中 4 处生命周期 debug 日志
- 删除 `integration/taskList.vue` 中未实现函数的 debug 日志
- 删除 `terminalWs.js` 中 WebSocket 连接事件的 debug 日志

### 2026-03-31: 拆分 dataetl 后端超限模块

- `apps/dataetl/views.py`（711行）拆分为 `views/` 包，7个文件，每个均在 200 行内
- `apps/dataetl/serializers.py`（455行）拆分为 `serializers/` 包，8个文件
- 补齐缺失的 `ETLQualityResultViewSet`、`ETLExecutionProgressViewSet`
- 新增 `ETLQualityResultSerializer`、`ETLExecutionProgressSerializer`（原 serializers.py 未包含）
- 修复 `ETLQualityRuleViewSet.test_rule` 被截断的问题

### 2026-03-31: 判断缺失 ADR 文档

- 创建 ADR-003-包管理器选型.md
- 创建 ADR-004-数据库选型.md

- 删除 `views/data/integration/` 目录（taskList.vue、taskDetail.vue 及全部子组件）

### 2026-03-31: Terminal 模块问题修复（第1条）

- 已补齐后端依赖声明：`channels==4.3.2`、`daphne==4.2.1`
- 修复目标：避免 terminal 模块在新环境启动时报 `No module named 'channels'` / `No module named 'daphne'`

### 2026-03-31: Terminal 模块问题修复（第2条）

- 新增 WebSocket JWT 认证中间件：`backend/apps/terminal/auth.py`
- 后端 WebSocket 认证链调整为 Session + JWT 双支持，优先兼容 `?token=` 查询参数与 `Authorization: Bearer <token>`
- 前端 terminal WebSocket 连接自动附带 token 参数，修复“文档声明 JWT、实现仅 Session”的不一致问题

### 2026-03-31: Terminal 模块问题修复（第3条）

- 修复 terminal 会话详情/命令历史/关闭接口在越权或不存在场景返回 `HTTP 200 + code=404` 的语义问题
- 现在上述接口返回真实 `HTTP 404`，并保持 `{code: 404, message: ...}` 响应体结构

### 2026-03-31: Terminal 前端 Bug 修复

- 修复前端 `useMessage` 导入错误（element-plus 无此导出），替换为 `ElMessage`
- 新增 Vite WebSocket 代理规则 `/ws` → `localhost:8000`，修复 WS 连接 pending
- 后端 `INSTALLED_APPS` 添加 `daphne`，使 `runserver` 启用 ASGI 模式

### 2026-03-31: Terminal 后端 PTY 架构重构

- **重构**：后端 consumer 从 subprocess 逐命令执行改为 PTY 交互式 Shell
  - 使用 `pty.fork()` 创建真实伪终端，支持 Tab 补全、方向键历史、交互式程序
  - 使用 `loop.add_reader()` 事件驱动读取 PTY 输出，替代忙轮询
  - 新增 `input` 消息类型转发原始按键，保留 `command` 类型兼容
  - 新增 `resize` 消息类型同步终端窗口尺寸
  - 安全审计：按 Enter 时拦截黑名单命令，发送 ANSI 红色 BLOCKED 提示
- **重构**：前端终端组件改为 PTY 直通模式
  - 移除本地行缓冲和 prompt 渲染逻辑，所有按键直接转发后端
  - Shell 自行处理回显、补全、颜色输出
  - 添加 `sendInput()`、`sendResize()` WebSocket 方法
  - 窗口 resize 时自动同步终端尺寸
- **UI**：Tokyo Night 主题配色 + 16色 ANSI 调色板 + 自定义滚动条
