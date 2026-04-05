# 任务追踪

### 2026-04-06: 数据开发分层目录树点击筛选与新建分层联动

- ✅ 完成分层目录树点击联动：点击 ODS/DWD/DWS/ADS 目录节点后，左侧“我的脚本”仅展示当前分层下作业脚本
- ✅ 支持同层节点二次点击取消筛选，恢复展示全部脚本
- ✅ 完成新建脚本分层联动：从分层/数据源节点触发“新建脚本”时，自动带入 `layer`
- 🔲 待完善后端接口按 `layer` 查询过滤，降低前端本地过滤负担

### 2026-04-05: 数据开发执行状态反馈一致性修正

- ✅ 修复数据开发 IDE 执行反馈文案：前端由“提交即成功”调整为“已提交（待执行）”
- ✅ 与后端现状对齐：`/datadev/scripts/{id}/execute` 当前仅创建 `pending` 记录，尚未实际执行
- ✅ 降低误判风险：避免用户将“执行请求入队”误解为“执行成功”
- ✅ 增加前端轻量轮询：执行提交后自动刷新执行状态（提交/执行中/完成），超时后提示稍后查看执行记录
- ✅ 修复轮询状态污染风险：切换脚本/重复执行前清理旧轮询器，避免并发轮询导致状态串扰
- ✅ 统一状态语义：`cancelled` 不再映射为 `failed`，状态栏与执行记录展示一致

### 2026-04-05: 数据开发模块后端实现（v1.4.0）

- ✅ 创建 `apps.datadev` Django App，含 models/serializers/views/urls/admin
- ✅ 实现三个核心模型：`DataDevScript`、`DataDevScriptVersion`、`DataDevScriptExecution`
- ✅ 完成 RESTful API：脚本 CRUD、版本创建与回滚、执行触发、执行记录查询
- ✅ 注册路由 `data-api/datadev/`，生成并执行数据库迁移
- 🔲 前端页面：脚本管理列表、脚本编辑器（SQL/Python）、版本历史、执行记录
- 🔲 对接执行器适配层：通过 `apps.executors` 实际执行 SQL/Python 脚本

### 2026-04-05: 顶部菜单跳转与滚动性能告警修复

- 修复顶部菜单父级点击行为：在保留侧边栏联动的基础上，同步执行路由跳转，优先走 `redirect`，无 `redirect` 时跳转首个子路由
- 修复浏览器控制台 `wheel` 非被动事件监听告警：在前端入口初始化阶段为 `wheel/touchstart/touchmove` 监听补充 `passive` 默认值
- 结果：顶部导航交互从“仅展开菜单”改为“展开并进入目标页面”，页面滚动响应性告警消除


### 2026-04-05: 数据开发模块架构设计与 ADR-006

- 完成"数据开发模块"架构方案设计，定位为脚本研发中心（SQL/Python），聚焦脚本资产管理、版本管理、执行触发与执行记录查询
- 确定与 ETL 的关系：模型独立，执行层复用 `apps.executors`，避免重复建设执行器体系
- 新增 `docs/adr/ADR-006-数据开发模块架构决策.md`，记录模块定位、复用策略、首期语言范围、权限策略与非目标边界
- 确立后续实施基线：脚本研发 → 版本化 → 执行触发 → 执行记录追踪完整闭环，首版不做多租户细粒度权限

### 2026-04-05: DataETL 执行器通用化抽象

- 将执行器抽象基类与工厂从 `apps.dataetl.executors.base` 下沉为通用模块：`apps.executors`
- 新增 `backend/apps/executors/base.py` 与 `backend/apps/executors/__init__.py`
- 保持兼容：`apps.dataetl.executors.base` 继续导出 `BaseETLExecutor` 与 `ExecutorFactory`
- 目标达成：ETL 现有调用路径无需改动，同时为其他业务模块复用执行器机制提供统一入口


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
