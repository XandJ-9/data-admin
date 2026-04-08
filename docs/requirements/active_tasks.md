# 任务追踪

### 2026-04-08: dbutils 查询安全与分页边界修复

- ✅ `DataSourceExecutor.execute_query` 复用 `_check_sql` 规范化结果，避免注释/空白导致语句类型误判
- ✅ SQL 执行阶段保留原始 SQL（含注释）传入驱动，修复标准化后报错行号偏移问题
- ✅ SQL 校验方法更名为 `_check_and_normalized_sql`，语义与职责更清晰，并完成调用与测试同步
- ✅ `_strip_trailing_semicolon` 调整为“最后一个非注释行”分号判定，避免尾部注释行影响分页拼接
- ✅ `_check_sql` 增强：支持块注释与行内注释剥离、仅允许单条 SQL、允许末尾分号
- ✅ `_check_sql` 增强：拦截 `WITH` 语句中的写操作/DDL 关键词，收敛只读查询边界
- ✅ 分页逻辑改为 `page_size + 1` 探测下一页，修复总数整除时 `has_more` 误判
- ✅ 新增 `apps.dbutils` 单元测试，覆盖 SHOW 不分页、WITH 写操作拦截、分页边界与分号/多语句校验

### 2026-04-06: 脚本执行切换为真实数据源执行

- ✅ execute_script 移除 mock 数据，改用 dbutils.get_executor 连接真实数据源执行 SQL
- ✅ 新增前置校验：数据源关联、当前版本存在性、脚本内容非空
- ✅ 执行失败时记录 status=failed 的执行记录，日志记录异常详情
- ✅ executor 在 finally 块中正确关闭，防止连接泄漏

### 2026-04-06: 数据开发工作台评审问题修复

- ✅ P0: 后端模拟 Spark SQL 执行，返回列名/行数据/耗时，前端 `handleRun` 解析结果填充 ResultPanel
- ✅ P0: CodeEditor 新增 `changeCursor` 监听并 emit `cursor-change`，StatusBar 正确显示光标行列
- ✅ P1: `handlePreviewVersion` 不再覆盖 `savedContent`，修复预览历史版本后脏状态误判
- ✅ P1: `confirmSave` 移除本地 `versionNumber++`，改由 `openScript` 从后端重新同步版本号
- ✅ P1: SidePanel 脚本节点新增删除按钮，index.vue 新增 `handleDeleteScript` 含确认弹窗与 tab 清理
- ✅ P2: 新建脚本对话框新增脚本类型选择（SQL/Python），移除硬编码的 `scriptType: 'sql'`
- ✅ P2: SidePanel 脚本节点新增编辑按钮，index.vue 新增编辑脚本信息弹窗（重命名/移动目录/修改描述）
- ✅ P3: `loadScripts` 从循环分页遍历改为单次 `pageSize=9999` 请求

### 2026-04-06: 数据开发 IDE 侧边栏代码检查与优化

- ✅ 移除冗余 `activeDirectoryFilter` 本地状态，消除与 `props.activeDirectoryId` 的双源真值问题
- ✅ 刷新按钮升级：新增 `refresh` emit，父组件监听后重新请求目录和脚本数据
- ✅ 修复 `comment` 字段未映射：目录 `remark` 和脚本 `description` 正确传入树节点
- ✅ "未分配目录" 增加快捷新建脚本按钮
- ✅ 删除未使用的 `.ds-icon` CSS 类
- ✅ 目录节点新增子项计数标签（`childCount`）
- ✅ `catalogTreeProps` 增加 `isLeaf` 映射，空目录也显示展开/折叠箭头
- ✅ `default-expand-all` 改为 `default-expanded-keys`，仅默认展开第一层目录

### 2026-04-06: IDE 资源导航树目录-脚本树改造

- ✅ 资源导航树改为树状结构：目录节点下直接展示该目录所属脚本
- ✅ 新增“默认目录”节点：无所属目录脚本统一归集到默认目录下
- ✅ 资源树点击行为增强：点击脚本节点直接打开脚本，点击目录节点继续触发目录筛选

### 2026-04-06: 数据目录新增入口恢复

- ✅ 数据目录管理页恢复“新增目录”按钮，支持在目录列表页直接创建目录
- ✅ 目录编辑弹窗复用为“新增/修改”双模式，新增时自动加载上级目录树
- ✅ 目录提交逻辑补充分支：无 `directoryId` 时调用新增接口，有 `directoryId` 时调用更新接口

### 2026-04-06: 数据开发数据目录前后端闭环实现

- ✅ 前端新增数据目录管理页面：`/datadev/catalog` 支持目录树查询、新增、修改、删除
- ✅ 前端新增目录 API 封装：`list/getTree/add/update/delete` 全量接入 `datadev/directories`
- ✅ IDE 侧边栏完成目录化联动：目录节点筛选脚本、目录/数据源节点支持新建脚本自动带入 `directoryId`
- ✅ 新建脚本流程从 `layer` 切换为 `directoryId`，与后端模型保持一致
- ✅ 后端目录逻辑增强：父子循环校验、目录树节点返回 `scriptCount`、删除前阻止存在子目录/脚本的目录
- ✅ 补充后端单测：覆盖目录父子循环校验与目录树脚本统计字段

### 2026-04-06: 数据开发数据目录模型与初始化

- ✅ 数据开发模块新增 `DataDevDirectory` 模型，用于承载开发脚本目录项
- ✅ 初始化命令 `initdata` 接入数据目录种子数据，默认创建 ODS/DWD/DWS/ADS 四个目录项
- ✅ 数据目录模型支持后续扩展新增目录项，不再依赖菜单结构承载目录内容
- ✅ 新增后端测试，验证 `initdata --force` 可正确初始化默认数据目录

### 2026-04-06: 数据开发版本历史交互增强（点击即查看）

- ✅ 版本历史列表支持点击版本条目直接查看对应版本内容
- ✅ 增加版本条目选中态高亮，明确当前正在查看的历史版本
- ✅ 增加未保存内容保护：切换查看历史版本前二次确认，避免误覆盖编辑区内容

### 2026-04-06: 数据开发脚本版本管理逻辑约束落地

- ✅ 草稿版本单例化：保存草稿时改为更新同一脚本下已有草稿版本，避免重复新增多个草稿版本
- ✅ 正式版本可多次发布：发布操作继续按版本号递增创建正式版本快照
- ✅ 版本当前态一致性：每次保存/发布都会重置并维护唯一 `is_current` 版本
- ✅ 新增后端单元测试：覆盖“重复保存草稿”“多次发布正式版本”“先草稿后发布”场景

### 2026-04-06: 数据开发执行引擎与版本视图策略更新

- ✅ 执行引擎策略统一：数据开发脚本执行请求固定为 Spark SQL 引擎
- ✅ 新建脚本流程简化：移除“选择数据源”步骤，创建时默认 Spark SQL 语义
- ✅ 版本历史视图增强：支持按“全部/正式/草稿”筛选，便于同时查看历史版本与草稿版本
- ✅ ADR-006 补充落地：增加“执行引擎策略补充（2026-04-06）”条款

### 2026-04-06: 数据开发 IDE 前端界面重构（ADR-006 对齐）

- ✅ 中央编辑区升级为多页签模式：支持同时打开多个脚本并在页签间切换
- ✅ 页签关闭保护：未保存变更脚本关闭前二次确认
- ✅ 编辑器工具栏重构：新增当前文档标识，执行入口调整为“运行当前文档”
- ✅ 左侧资源区视觉升级：对齐“资源导航树”语义，强化层级与脚本分组可读性
- ✅ 全局样式升级：页面采用统一 IDE 风格卡片布局与移动端断点适配
- 🔲 待补充：前端构建在当前终端被中断，需在稳定会话中完成一次完整构建校验

### 2026-04-06: 数据开发脚本版本管理升级（草稿版与正式版）

- ✅ 脚本编辑器新增“发布”入口：在“保存草稿版本”之外，支持一键发布正式版本
- ✅ 版本管理策略调整：草稿脚本允许入版本表，但标记为“草稿版本（非正式可用）”
- ✅ 发布策略落地：发布动作创建“正式可用”版本快照，并同步脚本状态为 `published`
- ✅ 后端新增发布接口：`POST /datadev/scripts/{id}/versions/publish`
- ✅ 版本列表可视化区分：前端版本历史展示“草稿/正式”标签

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
