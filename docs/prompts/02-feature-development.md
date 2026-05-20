# 单任务功能开发提示词

适用场景：实现一个明确功能、补齐一个接口、完成一个页面闭环或调整一个模块能力。

```text
请自主完成以下单任务开发。

目标：
<用一句话说明本轮唯一目标>

允许修改范围：
- <列出允许修改的目录或文件>

禁止修改范围：
- <列出明确不要碰的目录、模块或行为>
- 不要顺手重构无关代码
- 不要新增与目标无关的功能、入口、文案或样式

项目规则：
- 先应用 docs/prompts/01-project-rules.md 的固定规则。
- 如果涉及 datasource、dataintegration、datadev、datatask、executors 或 dbutils，必须先应用 docs/prompts/04-module-boundary-check.md。

开发流程：
1. 检查 git 状态和当前分支。
2. 阅读 CLAUDE.md，以及本任务相关的 ADR、开发规范和当前状态文档。
3. 搜索当前项目是否已有同职责实现，优先复用已有模式。
4. 简短说明实现计划和将修改的文件。
5. 按最小必要改动实现功能。
6. 补充或更新必要测试，测试范围与风险成比例。
7. 运行最小必要测试。
8. 同步 docs/requirements/active_tasks.md 和 docs/changelog.md。
9. 输出改动摘要、测试结果、风险点和建议后续验证项。

验收标准：
- <标准 1：用户可见行为或接口行为>
- <标准 2：权限、边界、数据一致性或错误处理>
- <标准 3：测试或构建通过>
```

示例：

```text
请自主完成以下单任务开发。

目标：
修复 datadev 模型详情接口返回已软删除字段的问题。

允许修改范围：
- backend/apps/datadev
- docs/requirements/active_tasks.md
- docs/changelog.md

禁止修改范围：
- 不要修改前端页面样式
- 不要调整 datatask 架构
- 不要改变 DataDevModel 是否同步平台任务镜像的现有口径

验收标准：
- 模型详情只返回 del_flag='0' 的字段
- 更新模型多次后不会带回历史字段
- uv run python manage.py test apps.datadev 通过
```
