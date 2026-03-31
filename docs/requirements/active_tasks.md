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
