# Data Admin 文档中心

欢迎使用 Data Admin 数据管理平台文档。

---

## 📚 文档目录

### 核心文档

| 文档 | 说明 | 读者 |
|------|------|------|
| [platform-architecture-design.md](platform-architecture-design.md) | 总体架构设计，包含五大模块详细设计、数据模型、功能说明 | 所有人 |
| [development-guide.md](development-guide.md) | 开发指南，包含核心抽象层、命名规范、开发模式、快速上手 | 开发者 |
| [data-asset-module.md](data-asset-module.md) | 数据资产管理模块，包含 API、测试、使用指南、迁移指南 | 开发者、用户 |
| [data-service-module.md](data-service-module.md) | 数据服务模块，包含数据服务接口管理、API 文档、使用指南 | 开发者、用户 |
| [deployment-guide.md](deployment-guide.md) | 部署指南，包含安装、配置、生产部署、故障排查 | 运维人员 |

### 故障排查文档

| 文档 | 说明 | 读者 |
|------|------|------|
| [troubleshooting-backend-startup.md](troubleshooting-backend-startup.md) | 后端启动故障排查指南，包含常见问题及解决方案 | 开发者、运维人员 |

---

## 🚀 快速导航

### 我想...

**了解项目**
- 阅读 [总体架构设计](platform-architecture-design.md) 了解平台概览
- 阅读 [开发指南](development-guide.md) 了解技术架构

**开始开发**
- 阅读 [开发指南](development-guide.md) 的快速开始部分
- 了解 [核心抽象层](development-guide.md#核心抽象) 和 [命名规范](development-guide.md#命名规范)

**部署应用**
- 阅读 [部署指南](deployment-guide.md)
- 按照步骤完成环境配置、数据迁移、服务启动

**使用数据资产管理模块**
- 阅读 [数据资产模块文档](data-asset-module.md)
- 了解 API 端点、功能使用、路由配置

**使用数据服务模块**
- 阅读 [数据服务模块文档](data-service-module.md)
- 了解数据服务接口管理、API 文档

**排查故障**
- 阅读 [后端启动故障排查指南](troubleshooting-backend-startup.md)
- 查看常见问题及解决方案

---

## 📖 阅读建议

### 初次使用者

1. 先读 [总体架构设计](platform-architecture-design.md) 了解平台全貌
2. 再读 [部署指南](deployment-guide.md) 完成环境搭建
3. 最后读 [数据资产模块文档](data-asset-module.md) 了解核心功能

### 开发者

1. 先读 [开发指南](development-guide.md) 掌握开发规范
2. 再读 [总体架构设计](platform-architecture-design.md) 了解业务架构
3. 最后读 [数据资产模块文档](data-asset-module.md) 了解具体实现

### 运维人员

1. 直接读 [部署指南](deployment-guide.md) 完成部署
2. 遇到问题时查看故障排查章节

---

## 🔑 关键概念

### 五大模块

1. **数据资产管理（Asset）**
   - 数据源管理
   - 元数据采集与浏览
   - 表血缘追踪

2. **数据 ETL 开发**
   - 任务配置
   - 转换规则
   - 版本管理

3. **数据质量管理**
   - 规则定义
   - 质量检查
   - 问题修复

4. **任务运维**
   - 任务调度
   - 监控告警
   - 日志查询

5. **数据服务**
   - 查询引擎
   - 报表服务
   - API 网关

### 核心抽象

- **BaseModel** - 所有数据模型的基础
- **BaseViewSet** - 统一的视图集合
- **DataSourceExecutor** - 数据库执行器抽象

---

## 📝 文档贡献

### 文档规范

- 使用 Markdown 格式
- 标题层级清晰（最多 4 级）
- 代码块标注语言
- 表格对齐整齐

### 提交文档

1. 在 `docs/` 目录下创建或修改文档
2. 更新本索引文件（`docs/README.md`）
3. 提交 Pull Request

---

## 🛠️ 文档维护

| 文档 | 维护者 | 最后更新 |
|------|--------|----------|
| platform-architecture-design.md | 架构团队 | 2025-01-21 |
| development-guide.md | 开发团队 | 2025-02-05 |
| data-asset-module.md | 数据资产团队 | 2026-02-05 |
| data-service-module.md | 数据服务团队 | 2026-02-05 |
| deployment-guide.md | 运维团队 | 2025-02-05 |
| troubleshooting-backend-startup.md | 运维团队 | 2025-02-05 |

---

## 💡 常见问题

### Q: 文档找不到答案？

A: 请尝试：
1. 使用 `Ctrl+F` 在文档中搜索关键词
2. 查看相关文档的交叉引用
3. 在 Issues 中提问

### Q: 发现文档错误？

A: 请：
1. 记录错误位置和具体内容
2. 提交 Issue 或直接 PR 修复

### Q: 想添加新文档？

A: 请：
1. 确认文档主题不在现有文档中
2. 创建新文档并更新本索引
3. 遵循文档规范

---

## 📞 联系方式

- 项目主页：[GitHub Repository]
- 问题反馈：[Issues]
- 文档仓库：[docs/](./)

---

**文档版本**: v1.1.0
**最后更新**: 2026-02-05
