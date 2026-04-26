# 前端（Vue 3 + Element Plus）

## 当前定位

前端基于 Vue 3.5 + Element Plus 2.10 + Vite 6 + Pinia，承载当前主干的五类业务页面：

| 页面域 | 目录 | 当前职责 |
|--------|------|----------|
| 数据源 | `src/views/data/datasource/` | 数据源管理、源端发现 |
| 数据集成 | `src/views/data/integration/` | 同步任务配置、执行与记录 |
| 数据开发 | `src/views/data/dev/` | 脚本开发、模型设计、执行历史 |
| 任务运维 | `src/views/data/task/` / `orchestration/` | 统一任务与实例运维 |
| 数据资产 / 服务 | `src/views/data/asset/` / `service/` | 资产目录、血缘、查询与接口 |

当前重要口径：

1. 数据集成表单已改为直接填写源库/源表，不再选择 snapshot。
2. 数据源页面已移除采集任务入口，当前保留连接管理与库表字段发现。
3. 登录页依赖验证码与后端失败次数限流。

## 运行命令

```bash
cd frontend
pnpm install
pnpm dev
pnpm build:prod
```

- Node.js：`18+`
- 开发地址：`http://localhost:80/data-admin/`

## 关键目录

```text
frontend/src/
├── api/
│   ├── data/
│   ├── system/
│   └── monitor/
├── views/
│   ├── data/
│   ├── system/
│   ├── monitor/
│   ├── login.vue
│   └── error/
├── store/modules/
├── router/
├── components/
├── layout/
└── utils/
```

## 当前约定

1. API 封装统一放在 `src/api/`，页面不直接写请求细节。
2. 页面默认遵循 RuoYi 风格的搜索表单 + 表格 + 分页 + 弹窗模式。
3. 前端使用 **JavaScript**，当前项目不做 TypeScript 迁移。
4. 生产构建使用 `pnpm build:prod`，压缩器为 `terser`。

## 进一步阅读

- 项目入口：`../README.md`
- 当前状态：`../docs/requirements/active_tasks.md`
- 前端约定：`../docs/developments/frontend-conventions.md`
