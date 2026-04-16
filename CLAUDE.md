# Claude Code 项目指令

本文件是 Claude Code (claude.ai/code) 在此项目中工作的**核心行为准则**。

---

## 一、项目定位

**Data Admin** 是一个统一数据管理平台：
- **后端**：Django 5.2 + DRF 3.16 + SimpleJWT + drf-spectacular
- **前端**：Vue 3.5 + Element Plus 2.10 + Vite 6 + Pinia（使用 **JavaScript**，非 TypeScript）
- **包管理器**：`uv`（后端）、`pnpm`（前端）
- **数据库**：SQLite（开发环境），支持连接外部 MySQL/PostgreSQL/Presto/StarRocks

**核心功能**：数据源管理、元数据目录、在线 SQL 查询、数据接口服务、数据开发、系统管理。

---

## 二、详细规范索引

以下文件包含具体的技术规范和代码模式，**需要时请先查阅**：

| 文件 | 说明 |
|------|------|
| [docs/developments/backend-conventions.md](docs/developments/backend-conventions.md) | 后端开发模式、命名规范、API 设计 |
| [docs/developments/frontend-conventions.md](docs/developments/frontend-conventions.md) | 前端 API 封装、组件模式、命名规范 |
| [docs/developments/creating-modules.md](docs/developments/creating-modules.md) | 创建新模块的完整步骤 |
| [docs/developments/quick-reference.md](docs/developments/quick-reference.md) | 常用命令、文件位置、端点速查 |

**外部文档**：
- [backend/README.md](backend/README.md) - 后端 API 详情
- [frontend/README.md](frontend/README.md) - 前端架构说明

---

## 三、AI 行为准则（必须遵守）

### 3.1 核心价值观

| 原则 | 说明 |
|------|------|
| **ADR 优先** | 涉及技术选型、数据库变更或重大功能实现时，必须先检查 `/docs/adr/` 目录 |
| **文档同步** | 代码更新时，同步更新 `/docs/requirements/active_tasks.md` 和 `docs/changelog.md` ，注意按照新记录添加在旧记录之前|
| **类型安全** | 后端使用 type hints；前端使用 JavaScript，**不要提示迁移至 TypeScript** |
| **中文化** | 提交信息、用户界面文本使用中文（技术术语除外） |

### 3.2 工作流程

接到任务后，按以下路径思考：

```
1. 上下文分析 → 检索 @workspace 相关代码，优先读取 /docs/ 相关规范
2. 决策评估   → 检查是否与已有 ADR 冲突，有冲突先提出
3. 方案确认   → 先给出伪代码或逻辑大纲，确认后再生成完整代码
4. 验证清单   → 提供测试/验证方法
```

### 3.3 编码规范

| 规范 | 要求 |
|------|------|
| **模块化** | 组件/函数不超过 500 行，按功能拆分 |
| **错误处理** | 所有外部 API 调用、数据库查询必须 try-catch，含明确错误日志 |
| **命名规范** | 变量名描述"是什么"，函数名描述"做什么" |
| **DRY 原则** | 发现重复代码，主动提出重构方案 |

### 3.4 交互模式

| 模式 | 说明 |
|------|------|
| **保持简洁** | 直接给出核心逻辑和代码，避免长篇大论 |
| **直言不讳** | 发现架构缺陷或更优方案时，明确指出 |
| **Git 友好** | 提交信息遵循 Conventional Commits：`<type>(<scope>): <中文描述>` |

---

## 四、快速启动

```bash
# 后端
cd backend && uv sync
uv run manage.py migrate && uv run manage.py initdata
uv run manage.py runserver 0.0.0.0:8000

# 前端
cd frontend && pnpm install && pnpm dev
```

**默认账号**：`admin / admin123`
