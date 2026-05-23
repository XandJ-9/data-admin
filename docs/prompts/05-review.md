# 代码评审提示词

适用场景：提交前、合并前、较大改动后，按项目 reviewer 口径检查真实问题。

```text
请使用 .claude/agents/data-admin-reviewer.md 的标准审查本轮变更。

审查范围：
- 优先审查 git diff --staged 和 git diff。
- 如果没有 diff，则审查最近 5 个提交中与本任务相关的改动。
- 不要修改文件。

必须读取：
- CLAUDE.md
- docs/adr/ 中与本次改动相关的 ADR
- docs/requirements/active_tasks.md
- docs/changelog.md
- 必要时读取 docs/developments/backend-conventions.md
- 必要时读取 docs/developments/frontend-conventions.md
- 涉及任务执行或模块边界时读取 docs/developments/module-responsibility-execution-guide.md

重点检查：
1. 是否违反 ADR-002 阶段职责边界。
2. 是否违反 ADR-003 的业务任务真源、Task 平台镜像、TaskInstance 唯一执行记录边界。
3. 是否重复实现已有功能。
4. 是否未同步 active_tasks.md 和 changelog.md。
5. 后端是否缺少必要 type hints、输入校验、权限校验、错误处理。
6. 前端是否误引入 TypeScript，或没有使用项目封装的 request/API 模式。
7. 权限是否做到后端 permission_map、菜单 perms、前端 v-hasPermi 一致。
8. 数据库访问是否绕过 apps.dbutils。
9. 任务执行是否绕过 apps.executors / TaskService / source handler。
10. 是否存在 SQL 注入、硬编码密钥、敏感信息泄露、权限绕过。
11. 是否存在 N+1 查询、软删除唯一约束问题、历史数据兼容问题。
12. 是否存在未覆盖的高风险回归测试。

只报告你有 >80% 把握的真实问题。不要输出主观风格偏好。

输出格式：

[严重级别] 问题标题
文件: 文件路径:行号
问题: 具体描述问题是什么，违反了哪条规范。
修复: 给出具体修复建议。

## 评审总结

| 严重级别 | 数量 | 状态 |
|----------|------|------|
| CRITICAL | 0 | 通过 |
| HIGH | 0 | 通过 |
| MEDIUM | 0 | 通过 |
| LOW | 0 | 通过 |

结论: 通过/警告/阻止 — <一句话说明是否建议合并>
```

严重级别：

- CRITICAL：安全漏洞、核心 ADR 冲突、架构边界严重漂移、会导致数据破坏或主链路不可用。
- HIGH：潜在 Bug、权限缺口、重要规范违反、明显回归风险。
- MEDIUM：文档不同步、可维护性问题、测试覆盖不足、兼容风险。
- LOW：命名、格式、轻微重复等低风险问题。
