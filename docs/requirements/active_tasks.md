# 活跃任务追踪

## 技术债务（待处理）

### TD-002: 组件行数超过 200 行限制

**优先级**: 中  
**违反原则**: 模块化 — 组件/函数长度不得超过 200 行  
**超限文件清单**（核心业务文件）:

| 文件 | 行数 | 建议 |
|------|------|------|
| `views/tool/build/RightPanel.vue` | 845 | 拆分为子组件 |
| `views/data/service/interface/index.vue` | 564 | 拆分列表/表单组件 |
| `views/data/asset/lineage/index.vue` | 525 | 拆分图谱/面板组件 |
| `views/data/etl/taskDetail.vue` | 499 | 已拆分 Tab 子组件，继续拆分脚本逻辑 |
| `backend/apps/dataetl/serializers_legacy.py` | 已删除 | ✅ 已拆分为 serializers/ 包 |
| `backend/apps/dataetl/views_legacy.py` | 已删除 | ✅ 已拆分为 views/ 包 |

---

### TD-003: ADR 文档缺失

**优先级**: 中  
**违反原则**: ADR 优先 — 任何技术选型必须有 ADR 记录  
**待补充 ADR**:
- ADR-001: 技术栈选型（Django + Vue3）✅ 已完成
- ADR-002: ETL 执行器架构✅ 已完成
- ADR-003: 包管理器选择（pnpm / uv）✅ 已完成
- ADR-004: 数据库选型✅ 已完成

## 已完成

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
