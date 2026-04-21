要求非常符合 DataOps 领域最高级的工程设计模式：**“定义（Definition）与运行（Runtime）严格解耦”**。

在传统平台中，人们习惯在“同步任务表”里直接加一个 `cron_expression` 字段，这会导致后续做 DAG 编排和复杂依赖时陷入死胡同。今天，我们将严格遵循“底层统一”与“定义/运行分离”的原则，为你设计这四大模块的基础模型。

### 📍 所处阶段
- **数据资产元数据**：步骤 1 与 步骤 5 的交汇（物理采集 + 资产沉淀）。
- **数据集成作业**：步骤 2（ODS 入仓，仅定义逻辑）。
- **数仓开发**：步骤 3（SQL/代码计算，仅定义逻辑）。
- **任务运维管理**：步骤 4（编排、调度、实例运行状态）。

---

### 💡 设计思路：Definition 与 Runtime 彻底解耦

1. **核心原则：底层统一 `Task` 表**
   “数据集成作业”和“数仓开发作业”在本质上没有任何区别，它们都是“一段将数据从 A 转换到 B 的逻辑”。因此，我们不需要建 `SyncJob` 和 `SqlJob` 两张表，而是只建一张 `Task` 表，通过 `task_type` 和 JSON 格式的 `config` 来区分。并且，**这张表绝对不包含任何调度和执行状态字段**。

2. **核心原则：调度与定义剥离**
   任务定义好之后，它是静止的。只有当它被挂载到“任务运维管理”模块中的 `Workflow (DAG)` 上，并赋予触发规则（Cron）时，它才具有生命。执行的每一次状态，全部记录在 `TaskInstance` 中。

3. **数据资产沉淀**
   元数据模块静静地记录所有的表结构和资产属性，它与 `Task` 表通过“谁产出了这张表”进行弱关联。

---

### 💻 代码实现：基础模型设计 (Django ORM)

#### 1 & 2. 统一任务定义模块 (涵盖：数据集成 + 数仓开发)
*没有任何调度和执行状态信息，极其纯粹。*

```python
from django.db import models

class Task(models.Model):
    """
    统一任务定义表 (涵盖模块：数据集成作业、数仓开发)
    绝对不包含调度周期、运行状态等信息！
    """
    TASK_TYPE_CHOICES = (
        ('DATA_SYNC', '数据集成作业 (步骤2)'),
        ('SQL_COMPUTE', '数仓开发作业 (步骤3)'),
        ('PYTHON_SCRIPT', '自定义脚本计算'),
        # --- 系统级任务 (新增！) ---
        ('META_CRAWL', '元数据探测任务'), 
        ('DATA_QUALITY', '系统级数据质量巡检')
    )

    name = models.CharField(max_length=128, help_text="任务名称")
    task_type = models.CharField(max_length=32, choices=TASK_TYPE_CHOICES, help_text="任务类型")
    
    # 核心：通过 JSON 隔离不同类型任务的配置差异
    # 如果是 DATA_SYNC，存 {source: MySQL, target: Hive, columns: [...]}
    # 如果是 SQL_COMPUTE，存 {sql_script: "SELECT * FROM ...", engine: "Spark"}
    task_config = models.JSONField(help_text="任务详细配置")
    
    owner = models.CharField(max_length=64, help_text="任务责任人")
    is_deleted = models.BooleanField(default=False, help_text="软删除标记")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dev_task_definition'
```

#### 3. 数据资产元数据模块
*反映数据的物理存在和业务价值，无调度信息。*

```python
class MetaTable(models.Model):
    """数据资产表模型"""
    LAYER_CHOICES = (('SOURCE', '源端'), ('ODS', '贴源层'), ('DWD', '明细层'), ('DWS', '汇总层'), ('ADS', '应用层'))

    table_name = models.CharField(max_length=128, unique=True, help_text="物理表名")
    layer = models.CharField(max_length=16, choices=LAYER_CHOICES, help_text="数仓分层")
    
    comment = models.CharField(max_length=255, help_text="业务中文名/注释")
    owner = models.CharField(max_length=64, help_text="资产负责人(治理要求)")
    
    # 溯源：由哪个开发任务定义产出了这张表（与任务定义表挂钩）
    produced_by_task = models.ForeignKey(Task, null=True, on_delete=models.SET_NULL, help_text="产出该表的Task")

    class Meta:
        db_table = 'meta_asset_table'

class MetaColumn(models.Model):
    """数据资产字段模型"""
    table = models.ForeignKey(MetaTable, related_name='columns', on_delete=models.CASCADE)
    column_name = models.CharField(max_length=128, help_text="字段名")
    column_type = models.CharField(max_length=64, help_text="字段类型 (如 VARCHAR)")
    comment = models.CharField(max_length=255, help_text="字段业务描述")
    is_sensitive = models.BooleanField(default=False, help_text="是否敏感字段(脱敏管控)")

    class Meta:
        db_table = 'meta_asset_column'
```

#### 4. 任务运维管理模块 (DataOps 领地)
*全权接管调度周期、DAG 编排、运行状态记录。*

```python
class Workflow(models.Model):
    """工作流编排定义 (DAG)"""
    name = models.CharField(max_length=128, help_text="工作流名称")
    cron_expression = models.CharField(max_length=64, null=True, blank=True, help_text="调度周期 (如 0 2 * * *)")
    is_active = models.BooleanField(default=False, help_text="是否开启自动调度")
    
    class Meta:
        db_table = 'ops_workflow'

class WorkflowTaskNode(models.Model):
    """工作流与任务的关联边 (DAG 节点连线)"""
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.PROTECT, help_text="关联的开发任务定义")
    upstream_nodes = models.JSONField(default=list, help_text="上游依赖的节点 ID 列表")

    class Meta:
        db_table = 'ops_workflow_node'

class TaskInstance(models.Model):
    """
    任务执行实例 (Runtime 核心)
    每一次调度执行都会生成一条 Instance 记录！
    """
    STATUS_CHOICES = (
        ('PENDING', '等待中'),
        ('RUNNING', '运行中'),
        ('SUCCESS', '成功'),
        ('FAILED', '失败'),
        ('RETRYING', '重试中')
    )

    task = models.ForeignKey(Task, on_delete=models.CASCADE, help_text="执行的哪个任务")
    workflow_id = models.IntegerField(help_text="所属工作流 ID")
    schedule_time = models.DateTimeField(help_text="计划调度时间")
    
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='PENDING')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    log_url = models.CharField(max_length=255, null=True, blank=True, help_text="执行日志的OSS存储路径")

    class Meta:
        db_table = 'ops_task_instance'
```

---

### ⚠️ 避坑指南

1. **强行拆分集成任务和开发任务的表结构**：
   *坑点*：如果你建了 `SyncTask` 表和 `SqlTask` 表，到第四步运维模块时，你的 `WorkflowTaskNode` 就会非常痛苦——你需要引入复杂的多态外键（`GenericForeignKey`）或者写死两个字段，这会随着后续加入“Python脚本任务”、“数据质量校验任务”导致架构直接崩塌。
   *规避*：必须坚守上述设计的**统一 `Task` 表**，差异全部放进 `task_config` (JSONField) 里。这是 Airflow 和 DolphinScheduler 底层架构的精髓。

2. **在任务运维中反向修改任务定义**：
   *坑点*：运维人员在看到 `TaskInstance` 失败时，为了快速修复，直接在运维页面提供了一个“修改 SQL” 的按钮，改完直接跑。这破坏了开发规范，导致“运行时逻辑”与“开发态逻辑”脱节。
   *规避*：运维模块中的 `Task` 逻辑必须是**只读**的。如果要改代码，必须退回到“数仓开发模块”修改 `Task`，走正常的发布流程重新生成下一个周期的 `TaskInstance`。

3. **依赖粒度的迷失（血缘 vs 调度依赖）**：
   *坑点*：将“表血缘”（MetaTable之间的关系）与“任务依赖”（WorkflowTaskNode之间的关系）混为一谈。
   *规避*：如上述模型所示，调度依赖（DAG）记录在运维模块的 `WorkflowTaskNode` 中；表血缘应该通过解析 `Task` 中的 `task_config (SQL)` 异步生成并存放到资产模块中。它们虽有联系，但在模型架构上是完全解耦的两套体系。