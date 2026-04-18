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

### 3.2.1 当前项目执行铁律（会话启动即生效）

以下规则用于约束 Claude Code / Copilot 在本项目中的执行方式，**优先级高于自由发挥**：

1. **单轮只做一个主目标**
   - 每次用户消息只聚焦一个可交付结果，例如“修复 500”“打通前后端接口”“改一个首页布局”
   - 在当前主目标完成前，不得自行展开额外优化、顺手重构、视觉 polish 或 reviewer 式扩展整改

2. **故障优先级最高**
   - 只要出现页面报错、接口 500、构建失败、运行异常，必须立即停止当前扩展工作
   - 先做根因定位，再做修复，再恢复原主线任务
   - 不允许在故障未澄清前继续做样式、交互或结构优化

3. **禁止未授权扩 scope**
   - 未经用户明确要求，不主动增加以下工作：
     - 额外审查轮次
     - 非阻断性重构
     - 文案/样式延展
     - “顺手一起改掉”的附属优化
   - 如果发现问题但不属于当前主线，应先归档，再等待用户确认

4. **先交付闭环，再做体验优化**
   - 默认顺序固定为：**可用性 > 正确性 > 稳定性 > 体验优化**
   - 未完成“能用且正确”的闭环前，不进入视觉美化和信息层重排

5. **输出必须围绕主线**
   - 过程汇报默认只说明：
     - 当前主目标
     - 当前阻塞 / 风险
     - 正在执行的下一步
     - 已完成的结果
   - 避免输出与当前主目标无关的探索性说明

6. **文档与审查后置**
   - `docs/requirements/active_tasks.md`、`docs/changelog.md`、额外 review 收口统一放在主线代码完成后处理
   - 如果当前阶段仍在定位故障或打通闭环，不优先消耗时间在文档整理和审查回合

7. **有分歧先停，不自行拍板**
   - 对产品取舍、界面风格、范围边界存在多个合理方案时，先给出简短选项并等待用户确认
   - 不允许在需求未收敛时连续多轮自发改版

8. **默认以最小必要改动交付**
   - 若现有接口、页面、模型已足够支撑当前目标，优先复用，不新增第二套表达
   - 仅在现有实现无法支撑主线目标时，才引入新结构

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
| **主线优先** | 回复、实现和排障都围绕当前唯一主目标推进，不在未授权情况下横向发散 |

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
