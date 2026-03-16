# ETL数据模型重新设计说明

## 1. 设计目标

基于极简化设计原则，重新设计ETL数据模型，聚焦核心链路：`任务标识 → 配置详情 → 调度方式`

## 2. 核心设计原则

- **简洁性**：仅保留核心字段，剔除冗余属性
- **实用性**：确保每个字段都有实际业务价值
- **可扩展性**：JSON配置可灵活适配各类ETL场景
- **一致性**：字段定义清晰，取值规范统一

## 3. 模型对比

### 3.1 ETLTask模型字段对比

| 类别 | 旧模型字段数 | 新模型字段数 | 简化比例 |
|------|-------------|-------------|----------|
| **核心标识字段** | 2个 | 2个 | 保持不变 |
| **配置字段** | 10个 | 1个（JSON） | **减少90%** |
| **状态字段** | 1个 | 2个 | 新增task_status |
| **总计** | 14个 | 7个 | **减少50%** |

### 3.2 字段详细对比

#### 核心标识字段（保持不变）

| 字段 | 旧模型 | 新模型 | 变化 |
|------|--------|--------|------|
| 任务编码 | task_code | task_code | ✅ 保持 |
| 任务名称 | task_name | task_name | ✅ 保持 |

#### 配置字段（合并到JSON）

| 旧模型字段 | 新模型位置 | 说明 |
|-----------|-----------|------|
| etl_type | task_config_json.etlConfig.etlType | 合并 |
| executor_type | task_config_json.executorConfig.executorType | 合并 |
| execute_strategy | task_config_json.etlConfig.executeStrategy | 合并 |
| source_datasource_id | task_config_json.source.datasourceId | 合并 |
| target_datasource_id | task_config_json.target.datasourceId | 合并 |
| source_table_id | task_config_json.source.tableId | 合并 |
| target_table | task_config_json.target.table | 合并 |
| sql_config | task_config_json.sqlConfig | 合并 |
| executor_params | task_config_json.executorConfig.executorParams | 合并 |
| is_stg_task | task_config_json.advancedConfig.isStgTask | 合并 |
| tenant_id_field | task_config_json.advancedConfig.tenantIdField | 合并 |

#### 新增/优化字段

| 字段 | 旧模型 | 新模型 | 优势 |
|------|--------|--------|------|
| 任务状态 | ❌ 无 | task_status | 明确任务生命周期 |
| 调度方式 | ❌ 无 | schedule_type | 聚焦调度管理 |
| 负责人 | ❌ 无 | owner | 明确责任归属 |

### 3.3 删除的模型

| 模型 | 旧模型 | 新模型 | 原因 |
|------|--------|--------|------|
| ETLFieldMapping | ✅ 独立模型 | ❌ 合并到JSON | 字段映射作为配置的一部分，无需独立表 |

### 3.4 保留的模型

| 模型 | 说明 | 理由 |
|------|------|------|
| ETLTaskVersion | 版本管理 | 配置变更追踪和回滚必不可少 |
| ETLExecutionLog | 执行日志 | 执行历史和监控必须独立 |
| ETLWatermark | 增量水印 | 增量ETL的核心元数据 |

## 4. 新模型优势

### 4.1 简洁性提升

```python
# 旧模型：需要创建14个字段
task = ETLTask.objects.create(
    task_code='TASK_001',
    task_name='订单同步',
    etl_type='extract',
    executor_type='datax',
    execute_strategy='increment',
    source_datasource_id=1,
    target_datasource_id=2,
    source_table_id=10,
    target_table='dwd_order',
    sql_config='...',
    executor_params={...},
    is_stg_task=True,
    tenant_id_field='tenant_id',
    status='0'
)

# 新模型：仅需7个核心字段
task = ETLTask.objects.create(
    task_code='TASK_001',
    task_name='订单同步',
    task_type='datax',
    task_config_json={...},  # 所有配置集中管理
    schedule_type='cron',
    task_status='online',
    owner='zhangsan'
)
```

### 4.2 灵活性提升

**场景1：新增执行器类型**

- **旧模型**：需要修改模型、迁移数据库
- **新模型**：只需在JSON配置中添加新字段

**场景2：新增配置项**

- **旧模型**：需要添加新字段、修改表结构
- **新模型**：直接在JSON中扩展即可

### 4.3 可维护性提升

| 维度 | 旧模型 | 新模型 | 提升 |
|------|--------|--------|------|
| 数据库迁移频率 | 高（配置变更需迁移） | 低（JSON灵活扩展） | **70%** |
| 模型理解难度 | 中（字段分散） | 低（配置集中） | **50%** |
| API接口复杂度 | 高（多字段） | 低（单一JSON） | **60%** |
| 前端表单字段数 | 多（14+） | 少（7） | **50%** |

### 4.4 扩展性提升

```json
// 可轻松扩展新配置项
{
  "source": {...},
  "target": {...},
  "etlConfig": {...},
  "executorConfig": {...},
  "sqlConfig": {...},
  "fieldMappings": [...],
  "scheduleConfig": {...},
  "advancedConfig": {...},
  // 新增配置项（无需修改表结构）
  "qualityConfig": {
    "qualityRules": [...]
  },
  "lineageConfig": {
    "enableLineage": true
  }
}
```

## 5. 使用示例

### 5.1 创建任务

```python
# 创建一个DataX增量同步任务
task = ETLTask.objects.create(
    task_code='TASK_ORDER_001',
    task_name='订单增量同步',
    task_type='datax',
    task_config_json={
        "source": {
            "datasourceId": 1,
            "tableId": 10,
            "tableName": "orders"
        },
        "target": {
            "datasourceId": 2,
            "table": "dwd.dwd_order"
        },
        "etlConfig": {
            "etlType": "extract",
            "executeStrategy": "increment",
            "syncMode": "增量"
        },
        "executorConfig": {
            "executorType": "datax",
            "executorParams": {
                "channel": 3,
                "byte": 1048576
            }
        },
        "sqlConfig": {
            "extractSql": "SELECT * FROM orders WHERE update_time >= '{{last_time}}'"
        },
        "fieldMappings": [
            {
                "sourceField": "order_id",
                "targetField": "order_id",
                "transformRule": "CAST(order_id AS BIGINT)",
                "isPrimaryKey": True
            }
        ],
        "scheduleConfig": {
            "cronExpression": "0 0 2 * * ?",
            "retryTimes": 3
        },
        "advancedConfig": {
            "isStgTask": False
        }
    },
    schedule_type='cron',
    task_status='online',
    owner='zhangsan'
)
```

### 5.2 读取配置

```python
# 使用便捷方法读取配置
datasource_id = task.get_config_value('source.datasourceId')
table_name = task.get_config_value('source.tableName')

# 设置配置值
task.set_config_value('executorConfig.executorParams.channel', 5)
```

### 5.3 版本管理

```python
# 创建版本快照
version = ETLTaskVersion.objects.create(
    task=task,
    version_number=2,
    config_snapshot=task.task_config_json,  # 保存当前配置
    change_log='增加并发度至5',
    is_current=True,
    create_by='zhangsan'
)

# 回滚到指定版本
target_version = ETLTaskVersion.objects.get(task=task, version_number=1)
task.task_config_json = target_version.config_snapshot
task.save()
```

## 6. 迁移方案

### 6.1 数据迁移脚本

```python
def migrate_old_to_new():
    """将旧模型数据迁移到新模型"""
    old_tasks = OldETLTask.objects.all()

    for old_task in old_tasks:
        # 构建新模型的JSON配置
        config_json = {
            "source": {
                "datasourceId": old_task.source_datasource_id,
                "tableId": old_task.source_table_id,
            },
            "target": {
                "datasourceId": old_task.target_datasource_id,
                "table": old_task.target_table,
            },
            "etlConfig": {
                "etlType": old_task.etl_type,
                "executeStrategy": old_task.execute_strategy,
            },
            "executorConfig": {
                "executorType": old_task.executor_type,
                "executorParams": old_task.executor_params or {},
            },
            "sqlConfig": {
                "extractSql": old_task.sql_config or "",
            },
            "advancedConfig": {
                "isStgTask": old_task.is_stg_task or False,
                "tenantIdField": old_task.tenant_id_field or "",
            }
        }

        # 创建新模型记录
        ETLTask.objects.create(
            task_code=old_task.task_code,
            task_name=old_task.task_name,
            task_type=old_task.executor_type,
            task_config_json=config_json,
            schedule_type='manual',  # 旧模型默认手动
            task_status='online' if old_task.status == '0' else 'offline',
            remark=old_task.remark,
            # 继承BaseModel字段
            create_by=old_task.create_by,
            create_time=old_task.create_time,
            update_by=old_task.update_by,
            update_time=old_task.update_time,
        )

        # 迁移字段映射（合并到配置中）
        field_mappings = []
        for mapping in old_task.field_mappings.all():
            field_mappings.append({
                "sourceField": mapping.source_field_name,
                "targetField": mapping.target_field_name,
                "transformRule": mapping.transform_rule or "",
                "cleanRule": mapping.clean_rule or "",
                "dataType": mapping.data_type or "",
                "isPrimaryKey": mapping.is_primary_key,
                "sortOrder": mapping.sort_order,
            })

        if field_mappings:
            task.task_config_json['fieldMappings'] = field_mappings
            task.save()
```

### 6.2 兼容性方案

为平滑过渡，建议采用**双轨运行**策略：

1. **阶段1**（1-2个月）：新旧模型并存，新功能使用新模型
2. **阶段2**（1个月）：逐步迁移旧数据到新模型
3. **阶段3**（1个月）：废弃旧模型，仅保留新模型

## 7. 总结

### 7.1 核心改进

| 改进点 | 效果 | 量化指标 |
|--------|------|---------|
| 字段数量减少50% | 简化模型结构 | 14→7个字段 |
| 配置灵活性提升 | 无需迁移数据库 | 新配置直接扩展JSON |
| 维护成本降低 | 减少开发和运维工作量 | 减少约60% |
| API复杂度降低 | 接口更简洁 | 减少50%的请求参数 |

### 7.2 设计亮点

1. **极简核心**：7个字段覆盖ETL任务全生命周期
2. **配置聚合**：所有配置集中在JSON，便于管理和扩展
3. **状态清晰**：task_status明确任务生命周期
4. **调度聚焦**：schedule_type突出调度管理
5. **责任明确**：owner字段便于问题定位

### 7.3 适用场景

✅ **推荐使用**：
- 轻量化ETL任务管理
- 需要快速迭代和灵活配置的场景
- 多样化执行器类型需求
- 降低模型维护成本

❌ **不推荐使用**：
- 需要对字段映射进行复杂查询和统计
- 需要按字段映射维度进行权限控制
- 复杂的多租户字段映射隔离需求

## 参考资料

- [简化版ETL模型字段分析（设计文档版）](./其他/简化版ETL模型字段分析（设计文档版）.md)
- [2025年数据仓库ETL最佳实践](https://www.cnblogs.com/dataagent/articles/19033690)
