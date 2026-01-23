# 数据ETL模块设计方案（数据仓库场景）

## 文档版本
- **版本号**：2.0
- **最后更新**：2026年1月
- **适用场景**：基于数据仓库（Data Warehouse）的ETL/ELT数据处理
- **关键词**：ETL、Extract、Transform、Load、数据仓库、数据湖、离线处理、实时流处理

---

## 一、模块定位

### 1.1 核心目标
数据ETL模块是数据资产平台的**"数据管道中枢"**，通过完整的**抽取（Extract）→ 转换（Transform）→ 加载（Load）**流程，将分散在各业务系统的数据（多租户分库场景）按照数据仓库架构（STG→ODS→DWD→DWS→ADS）进行多阶段处理，保障数据流的**实时性、准确性、一致性**。

### 1.2 在数据仓库中的位置
```
业务系统数据（多租户分库）
    ↓
STG（临时缓冲层）← 按租户/按数据源分区存放原始数据
    ↓
ODS（原始数据层）← 跨租户汇总、标准化、去重
    ↓
DWD（明细数据层）← 主题化、维度化
    ↓
DWS（汇总层） → ADS（应用层） → 数据服务/BI报表

数据集成模块承载：
- 业务系统 → STG：按租户/按数据源采集原始数据（DataX）
- STG → ODS：数据汇总、标准化、去重（Spark SQL）
- ODS → DWD：数据清洗、维度化（Spark SQL）
- DWD → DWS：聚合计算（Spark SQL）
- DWS → ADS：应用转化（Spark SQL）
```

### 1.3 核心价值
| 价值维度 | 具体体现 |
|--------|--------|
| **抽取灵活性** | 支持多种数据源（MySQL/Oracle/PostgreSQL等）、多租户隔离抽取、增量/全量灵活策略 |
| **转换完整性** | 字段级清洗、表级关联、流程级控制；支持复杂聚合、窗口函数、维度化处理 |
| **加载精确性** | 多层次ODS/DWD/DWS/ADS加载、分区管理、去重合并、质量检查 |
| **时效性覆盖** | 离线（T+0/T+1）、准实时（分钟级）、实时（秒级）三种处理模式 |
| **可追溯性** | 完整的数据血缘（表级/字段级），STG保留原始数据支持审计 |
| **可维护性** | 可视化ETL配置、版本管理、失败自动重试、成本透明分配 |

---

## 二、系统架构设计

### 2.1 分层架构（含多租户STG层）
```
┌──────────────────────────────────────────────────────┐
│              数据仓库应用层（ADS/报表）                │
├──────────────────────────────────────────────────────┤
│    汇总层（DWS）←→ 汇总数据集成                 │
├──────────────────────────────────────────────────────┤
│    明细层（DWD）←→ 明细数据集成                 │
├──────────────────────────────────────────────────────┤
│    原始层（ODS）← 跨租户汇总、标准化、去重        │
├──────────────────────────────────────────────────────┤
│ ★ 临时缓冲层（STG）← 按租户/数据源分区存放      │
│   每个租户/数据源的数据独立存放，便于追踪和隔离   │
├──────────────────────────────────────────────────────┤
│  数据集成模块（ETL/ELT）                 │
│  ┌────────────────────────────────────────┐ │
│  │ 任务配置 | 数据转换 | 调度执行 | 监控告警 │ │
│  └────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────┤
│  业务系统数据源（多租户分库）              │
│  └─ 租户A(DB1)  租户B(DB2)  租户C(DB3)  │
│     └─ MySQL    └─ Oracle   └─ PostgreSQL│
└──────────────────────────────────────────────────────┘
```

### 2.2 模块构成
```
数据ETL模块
├── 【Extract】抽取层
│  ├── DataX执行器（外部异构数据库）
│  ├── Sqoop执行器（Hadoop生态集成）
│  ├── API采集（RESTful/GraphQL）
│  └── 文件导入（CSV/Parquet/ORC）
│
├── 【Transform】转换层
│  ├── 字段级转换（映射、清洗、脱敏）
│  ├── 表级转换（去重、关联、聚合）
│  ├── 流程级控制（条件分支、循环处理）
│  └── 质量检查（NULL检查、范围验证、一致性校验）
│
├── 【Load】加载层
│  ├── STG层（临时缓冲） ★ 多租户隔离存储
│  ├── ODS层（原始数据） ← 汇总、标准化
│  ├── DWD层（明细层）
│  ├── DWS层（汇总层）
│  └── ADS层（应用层）
│
├── 执行引擎
│  ├── DataX执行器（高效批量抽取）
│  ├── Spark SQL执行器（分布式转换）
│  ├── Spark Streaming执行器（实时流处理）
│  └── 调度执行管理（Celery Beat + Cron）
│
├── 多租户支撑
│  ├── 租户隔离存储（按tenant_id分区）
│  ├── 数据源追踪（source_id标记）
│  ├── 权限隔离（租户级访问控制）
│  └── 成本分配（按租户统计存储成本）
│
└── 协同功能
   ├── 元数据管理（自动同步DW元数据）
   ├── 数据血缘（表级/字段级追踪）
   ├── 版本管理（配置版本控制）
   └── 监控告警（失败告警、质量告警）
```

---

## 三、核心功能模块详设

### 3.1 ETL任务管理

#### 3.1.1 任务类型划分（ETL生命周期）

根据数据流向（抽取→转换→加载）和数据仓库分层，定义以下任务类型：

```python
TASK_TYPES = [
    # 临时缓冲层（多租户/多数据源采集）
    ('stg_incremental', 'STG增量采集（按租户/数据源隔离）'),
    ('stg_full', 'STG全量采集（按租户/数据源隔离）'),
    
    # 原始层（跨租户汇总）
    ('ods_summary', 'ODS跨租户汇总'),
    ('ods_standardize', 'ODS标准化处理'),
    ('ods_dedup', 'ODS去重处理'),
    
    # 明细层开发
    ('dwd_dimension', 'DWD维度表'),
    ('dwd_fact', 'DWD事实表'),
    ('dwd_cleaning', 'DWD数据清洗'),
    
    # 汇总层开发
    ('dws_agg', 'DWS聚合计算'),
    ('dws_union', 'DWS数据合并'),
    
    # 应用层
    ('ads_app', 'ADS应用表'),
    
    # 其他
    ('api_collection', 'API数据采集'),
    ('file_import', '文件导入'),
]
```

#### 3.1.2 任务配置结构

**数据模型设计**：
```python
class IntegrationTask(BaseModel):
    """ETL任务"""
    
    # 基本信息
    task_name = models.CharField(max_length=128, verbose_name='任务名称')
    task_type = models.CharField(max_length=30, choices=TASK_TYPES)
    description = models.TextField(blank=True, verbose_name='描述')
    
    # 业务信息
    business_domain = models.CharField(max_length=64, verbose_name='业务域')  # 订单、用户、商品等
    priority = models.IntegerField(choices=[(0, 'P0'), (1, 'P1'), (2, 'P2'), (3, 'P3')], default=2)
    responsible_person = models.CharField(max_length=64, verbose_name='负责人')
    
    # 数据仓库分层信息
    dw_layer = models.CharField(
        max_length=10,
        choices=[('ods', 'ODS'), ('dwd', 'DWD'), ('dws', 'DWS'), ('ads', 'ADS')],
        verbose_name='数据仓库层级'
    )
    
    # 源端配置
    source_datasource = models.ForeignKey('datasource.DataSource', on_delete=models.CASCADE)
    source_tables = models.JSONField(default=list, verbose_name='源表列表')  # [{'table': 'user', 'database': 'production'}]
    source_filter = models.TextField(blank=True, verbose_name='源数据过滤条件')  # WHERE子句
    
    # 目标端配置
    target_datasource = models.ForeignKey('datasource.DataSource', on_delete=models.CASCADE, related_name='target_tasks')
    target_table = models.CharField(max_length=128, verbose_name='目标表')
    target_database = models.CharField(max_length=128, verbose_name='目标数据库')
    
    # 分区配置（数据仓库关键）
    partition_type = models.CharField(
        max_length=20,
        choices=[('date', '日期分区'), ('dimension', '维度分区'), ('none', '不分区')],
        default='date',
        verbose_name='分区类型'
    )
    partition_field = models.CharField(max_length=64, blank=True, verbose_name='分区字段')  # ds或其他维度
    
    # 增量策略（数据仓库关键）
    incremental_type = models.CharField(
        max_length=20,
        choices=[
            ('full', '全量'),
            ('incremental_append', '增量追加'),  # 仅新增记录
            ('incremental_upsert', '增量更新'),  # 新增+更新
            ('merge', '合并'),  # 源端数据和目标端合并
        ],
        default='full',
        verbose_name='增量策略'
    )
    incremental_field = models.CharField(
        max_length=64, 
        blank=True, 
        verbose_name='增量字段'  # update_time, ts 等
    )
    
    # 调度配置
    schedule_type = models.CharField(
        max_length=20,
        choices=[('cron', 'Cron'), ('interval', '间隔'), ('once', '单次'), ('realtime', '实时')],
        default='cron'
    )
    schedule_conf = models.CharField(max_length=256, verbose_name='调度配置')  # Cron或间隔
    
    # 运行配置
    enabled = models.BooleanField(default=True, verbose_name='是否启用')
    retry_count = models.IntegerField(default=3, verbose_name='失败重试次数')
    timeout_minutes = models.IntegerField(default=60, verbose_name='超时时间(分钟)')
    
    # 转换配置（JSON存储）
    transform_config = models.JSONField(default=dict, verbose_name='数据转换配置')
    
    # 质量规则配置
    quality_rules = models.JSONField(default=list, verbose_name='质量规则')
    
    # 状态信息
    status = models.CharField(max_length=20, default='draft', choices=[
        ('draft', '草稿'),
        ('testing', '测试'),
        ('published', '发布'),
        ('offline', '下线'),
    ])
    
    class Meta:
        db_table = 'dataintegration_task'
        indexes = [
            models.Index(fields=['business_domain', 'dw_layer']),
            models.Index(fields=['status', 'enabled']),
            models.Index(fields=['responsible_person']),
        ]


class IntegrationTaskVersion(BaseModel):
    """任务配置版本"""
    task = models.ForeignKey(IntegrationTask, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    config_json = models.JSONField(verbose_name='完整配置')
    change_reason = models.CharField(max_length=256, blank=True)
    is_current = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'dataintegration_task_version'
        unique_together = [['task', 'version_number']]


class IntegrationExecutionLog(BaseModel):
    """ETL执行日志"""
    task = models.ForeignKey(IntegrationTask, on_delete=models.CASCADE, related_name='execution_logs')
    
    # 执行信息
    execution_id = models.CharField(max_length=64, unique=True)  # 唯一标识
    status = models.CharField(max_length=20, choices=[
        ('waiting', '待执行'),
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('timeout', '超时'),
        ('skipped', '跳过'),
    ])
    
    # 时间信息
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    duration_seconds = models.IntegerField(default=0)
    
    # 数据统计
    source_row_count = models.IntegerField(default=0, verbose_name='源端数据量')
    target_row_count = models.IntegerField(default=0, verbose_name='目标端数据量')
    insert_count = models.IntegerField(default=0, verbose_name='新增行数')
    update_count = models.IntegerField(default=0, verbose_name='更新行数')
    delete_count = models.IntegerField(default=0, verbose_name='删除行数')
    skip_count = models.IntegerField(default=0, verbose_name='跳过行数')
    
    # 错误信息
    error_message = models.TextField(blank=True)
    error_line = models.IntegerField(default=0, verbose_name='错误所在行')
    
    class Meta:
        db_table = 'dataintegration_execution_log'
        indexes = [
            models.Index(fields=['task', '-start_time']),
            models.Index(fields=['status']),
            models.Index(fields=['execution_id']),
        ]
```

#### 3.1.3 多租户STG层设计（Extract阶段隔离）

**核心价值**：在多租户分库场景下，ETL的抽取阶段采用STG（Staging）临时缓冲层，具有以下优势：

| 优势 | 说明 |
|-----|-----|
| **租户隔离** | 每个数据源/租户的数据独立存放，互不混淆，便于追踪 |
| **数据审计** | STG保留原始数据，便于问题排查和数据审计 |
| **降低耦合** | 数据采集和汇总解耦，ODS层专注于标准化处理 |
| **成本分配** | 按租户统计存储成本，支持成本透明和分摊 |
| **权限隔离** | STG层支持租户级权限控制，DWD/DWS支持跨租户查询 |
| **性能优化** | ODS汇总时只需扫描当日新增的STG数据，而非全量数据 |

**架构模式**：

```
租户A数据库               租户B数据库               租户C数据库
    ↓                       ↓                       ↓
[DataX]                 [DataX]                 [DataX]
    ↓                       ↓                       ↓
STG_user (tenant_id=A)  STG_user (tenant_id=B)  STG_user (tenant_id=C)
    ↓                       ↓                       ↓
    └─────────────── [Spark SQL] ──────────────┘
                           ↓
                    ODS_user (标准化汇总)
                      ↓
                   DWD/DWS/ADS
```

**STG层存储结构**：

```python
# HDFS存储路径
/warehouse/stg/{business_domain}/{table_name}/
    ├── tenant_id={tenant_a}/
    │   ├── ds=20260120/
    │   │   ├── part-00000.orc
    │   │   └── part-00001.orc
    │   └── ds=20260121/
    ├── tenant_id={tenant_b}/
    │   ├── ds=20260120/
    │   └── ds=20260121/
    └── tenant_id={tenant_c}/
        ├── ds=20260120/
        └── ds=20260121/

# STG表字段示例（添加租户和源追踪字段）
CREATE TABLE stg_user (
    id BIGINT,
    user_name STRING,
    email STRING,
    created_at STRING,
    updated_at STRING,
    -- ★ 租户和源追踪字段
    tenant_id STRING,        # 租户标识
    source_id STRING,        # 数据源标识
    source_table STRING,     # 源表名
    etl_load_time TIMESTAMP, # ETL加载时间
    -- 分区字段
    ds STRING                # 日期分区YYYYMMDD
) PARTITIONED BY (tenant_id STRING, ds STRING)
STORED AS ORC;
```

**STG→ODS转换流程**：

```python
# Spark SQL示例：STG汇总到ODS

# 第一步：从多个租户STG读取数据
stg_data = spark.sql("""
    SELECT 
        id, user_name, email, created_at, updated_at,
        tenant_id, source_id, etl_load_time
    FROM stg_user
    WHERE ds = '{current_date}'  # 仅处理当日数据
""")

# 第二步：数据标准化（租户维度）
standardized = stg_data \
    .withColumn('email', lower(trim('email'))) \
    .withColumn('created_date', substring('created_at', 1, 10)) \
    .withColumn('is_active', when('updated_at' > add_months(current_date(), -1), 1).otherwise(0))

# 第三步：跨租户去重（去除同一租户内的重复记录）
deduplicated = standardized \
    .withColumn('rn', 
        row_number().over(
            Window.partitionBy('tenant_id', 'id')
                  .orderBy(desc('updated_at'))
        )
    ) \
    .filter('rn = 1') \
    .drop('rn')

# 第四步：写入ODS（合并模式：INSERT OR UPDATE）
deduplicated.write \
    .format('orc') \
    .mode('overwrite') \
    .partitionBy('ds') \
    .option('path', f'hdfs://nn:9000/warehouse/ods/user') \
    .insertInto('ods_user')
```

**STG层任务配置模型扩展**：

```python
class IntegrationTask(BaseModel):
    # ... 既有字段 ...
    
    # ★ 多租户STG相关字段
    is_stg_task = models.BooleanField(default=False, verbose_name='是否为STG采集任务')
    
    # STG层特有配置（当is_stg_task=True时生效）
    tenant_id_field = models.CharField(
        max_length=64, 
        blank=True,
        verbose_name='源端租户ID字段'
    )  # 如source中user.tenant_id = 'A'，则在STG中保留tenant_id字段
    
    source_id_field = models.CharField(
        max_length=64,
        blank=True, 
        verbose_name='源端数据源ID字段'
    )  # 追踪数据的来源
    
    target_layer = models.CharField(
        max_length=10,
        choices=[('stg', 'STG'), ('ods', 'ODS'), ('dwd', 'DWD'), ('dws', 'DWS'), ('ads', 'ADS')],
        default='ods',
        verbose_name='目标数据仓库层级'
    )  # 更精细的层级控制
    
    # 分区配置增强
    partition_by_tenant = models.BooleanField(
        default=False,
        verbose_name='是否按租户分区'
    )  # STG层建议启用

    class Meta:
        db_table = 'dataintegration_task'
        indexes = [
            models.Index(fields=['business_domain', 'target_layer']),
            models.Index(fields=['status', 'enabled']),
            models.Index(fields=['responsible_person']),
            models.Index(fields=['is_stg_task']),
        ]
```

---

#### 3.1.4 任务配置接口

```python
# 创建/编辑ETL任务
POST   /dataintegration/tasks/
PUT    /dataintegration/tasks/{id}/

# 响应示例
{
  "code": 200,
  "data": {
    "id": 1,
    "taskName": "用户表ODS采集",
    "taskType": "ods_incremental",
    "dwLayer": "ods",
    "sourceDatasource": {"id": 1, "name": "生产数据库"},
    "sourceTables": [
      {"table": "user", "database": "production", "schema": "public"}
    ],
    "targetTable": "ods_user",
    "partitionType": "date",
    "partitionField": "ds",
    "incrementalType": "incremental_upsert",
    "incrementalField": "update_time",
    "scheduleType": "cron",
    "scheduleConf": "0 2 * * *",  // 每日2点执行
    "transformConfig": {...},
    "qualityRules": [...]
  }
}

# 获取版本历史
GET    /dataintegration/tasks/{id}/versions/

# 回滚版本
POST   /dataintegration/tasks/{id}/versions/{versionId}/rollback/

# 对比版本
GET    /dataintegration/tasks/{id}/versions/compare/
?fromVersion=1&toVersion=2
```

---

### 3.2 数据转换配置（Transform阶段核心）

#### 3.2.1 转换规则体系

在ETL的Transform阶段，数据转换分为三类：

```
┌─ 1. 字段级转换（最细粒度）
│  ├─ 字段映射：源字段 → 目标字段
│  ├─ 字段清洗：类型转换、null处理、格式规范
│  ├─ 字段加工：拼接、截断、条件转换
│  └─ 字段脱敏：对敏感字段隐藏或替换
│
├─ 2. 表级转换（中层级）
│  ├─ 去重：基于主键去重
│  ├─ 关联：与维度表关联、补充维度信息
│  ├─ 聚合：分组统计、同环比计算
│  └─ 分割：一个源表拆分为多个目标表
│
└─ 3. 流程级控制（高层级）
   ├─ 条件分支：based on某个字段值的不同处理
   ├─ 循环处理：多行处理逻辑
   └─ 错误处理：异常行处理策略
```

#### 3.2.2 转换配置数据结构

```python
class TransformConfig(BaseModel):
    """数据转换配置"""
    task = models.OneToOneField(IntegrationTask, on_delete=models.CASCADE)
    
    # 转换步骤（有序）
    steps = models.JSONField(default=list, verbose_name='转换步骤')
    # 示例:
    # [
    #   {
    #     "id": "step_1",
    #     "name": "字段清洗",
    #     "type": "field_cleaning",
    #     "operations": [
    #       {
    #         "field": "user_age",
    #         "operation": "convert_type",
    #         "params": {"from_type": "string", "to_type": "int"}
    #       },
    #       {
    #         "field": "user_phone",
    #         "operation": "mask",  // 脱敏
    #         "params": {"pattern": "****XXXX"}
    #       }
    #     ]
    #   },
    #   {
    #     "id": "step_2",
    #     "name": "维度关联",
    #     "type": "dimension_join",
    #     "operations": [
    #       {
    #         "join_type": "left",
    #         "dim_table": "dim_region",
    #         "on": "source.region_id = dim.region_id",
    #         "select_fields": ["region_name", "region_code"]
    #       }
    #     ]
    #   },
    #   {
    #     "id": "step_3",
    #     "name": "数据聚合",
    #     "type": "aggregation",
    #     "operations": [...]
    #   }
    # ]
    
    # 字段映射（显式映射关系）
    field_mapping = models.JSONField(default=dict, verbose_name='字段映射')
    # 示例:
    # {
    #   "user_id": {
    #     "source_field": "user_id",
    #     "source_table": "user",
    #     "target_field": "user_id",
    #     "data_type": "bigint",
    #     "description": "用户ID",
    #     "is_partition_field": false,
    #     "is_primary_key": true
    #   },
    #   "user_name": {...}
    # }
    
    # 去重配置
    dedup_config = models.JSONField(default=dict, verbose_name='去重配置')
    # 示例:
    # {
    #   "enabled": true,
    #   "keys": ["user_id", "order_id"],  // 基于这些字段去重
    #   "keep_strategy": "first"  // first|last|max_update_time
    # }
    
    # 校验规则
    validation_rules = models.JSONField(default=list, verbose_name='校验规则')
    # 示例:
    # [
    #   {
    #     "rule_id": "rule_1",
    #     "rule_name": "user_id 非空检验",
    #     "field": "user_id",
    #     "condition": "is_not_null",
    #     "on_failure": "reject"  // reject|skip|log
    #   },
    #   {
    #     "rule_id": "rule_2",
    #     "rule_name": "user_age 范围检验",
    #     "field": "user_age",
    #     "condition": "between 0 and 150",
    #     "on_failure": "skip"
    #   }
    # ]
    
    class Meta:
        db_table = 'dataintegration_transform_config'


class TransformTemplate(BaseModel):
    """转换模板（可复用）"""
    template_name = models.CharField(max_length=128)
    template_category = models.CharField(max_length=64)  # 数据清洗、维度加工、聚合等
    template_config = models.JSONField()
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)  # 公开模板或私有
    
    class Meta:
        db_table = 'dataintegration_transform_template'
```

#### 3.2.3 转换操作库

```python
# 支持的转换操作（可扩展）
TRANSFORM_OPERATIONS = {
    # 字段清洗
    'convert_type': '类型转换',
    'trim': '去除空格',
    'null_fill': 'null填充',
    'format_validate': '格式验证',
    'mask': '数据脱敏',
    
    # 字段加工
    'string_concat': '字符串拼接',
    'substring': '字符串截取',
    'case_when': '条件判断',
    'replace': '字符串替换',
    'split': '字符串分割',
    
    # 时间处理
    'date_format': '日期格式化',
    'date_add': '日期加减',
    'date_diff': '日期相差',
    
    # 数值处理
    'round': '数值四舍五入',
    'floor': '向下取整',
    'ceil': '向上取整',
    
    # 聚合函数
    'sum': '求和',
    'avg': '平均值',
    'count': '计数',
    'max': '最大值',
    'min': '最小值',
    'count_distinct': '去重计数',
    
    # 关联
    'left_join': '左关联',
    'inner_join': '内关联',
    'full_join': '全关联',
    'union': '合并',
    
    # 其他
    'window_function': '开窗函数',
    'custom_sql': '自定义SQL',
}
```

#### 3.2.4 前端转换配置UI

```vue
<template>
  <div class="transform-config">
    <!-- 步骤面板 -->
    <div class="steps-panel">
      <div v-for="step in steps" :key="step.id" class="step-card">
        <div class="step-header">
          <span class="step-name">{{ step.name }}</span>
          <el-button-group>
            <el-button size="small" @click="editStep(step)">编辑</el-button>
            <el-button size="small" @click="deleteStep(step)">删除</el-button>
          </el-button-group>
        </div>
        <div class="step-body">
          <!-- 显示step内容预览 -->
        </div>
      </div>
      <el-button type="primary" @click="addStep">+ 添加转换步骤</el-button>
    </div>
    
    <!-- 字段映射 -->
    <div class="field-mapping">
      <el-table :data="fieldMapping">
        <el-table-column prop="sourceField" label="源字段" />
        <el-table-column prop="targetField" label="目标字段" />
        <el-table-column prop="dataType" label="数据类型" />
        <el-table-column prop="transformation" label="转换" />
      </el-table>
    </div>
    
    <!-- 测试执行 -->
    <div class="test-section">
      <el-button type="primary" @click="testTransform">测试转换</el-button>
      <div v-if="testResult" class="test-result">
        <el-table :data="testResult.data">
          <!-- 展示测试结果 -->
        </el-table>
      </div>
    </div>
  </div>
</template>
```

---

### 3.3 调度与执行管理

#### 3.3.1 数据仓库多阶段ETL策略（含多租户STG）

在多租户分库的数据仓库场景中，建议采用「STG缓冲层」的分层ETL流程：

```
┌─────────────────────────────────────────────────────────────────┐
│  外部数据源（多租户分库）【Extract 抽取源】                    │
│  ├─ 租户A: MySQL(production_db_a)                             │
│  ├─ 租户B: Oracle(production_db_b)                            │
│  └─ 租户C: PostgreSQL(production_db_c)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ 【阶段0：多租户抽取到STG】
                             │ 工具：DataX（按租户执行）
                             │ 特点：隔离存储、便于追踪、支持成本分配
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  STG层（临时缓冲层 - Hive/HDFS）                              │
│  ├─ stg_user/tenant_id=A/ds=20260120/  (租户A数据)           │
│  ├─ stg_user/tenant_id=B/ds=20260120/  (租户B数据)           │
│  └─ stg_user/tenant_id=C/ds=20260120/  (租户C数据)           │
│  特点：按租户+按日期分区，原始数据无处理                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ 【阶段1：STG汇总到ODS】
                             │ 工具：Spark SQL（跨租户处理）
                             │ 特点：去重、标准化、数据质量检查
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  ODS层（原始数据层 - Hive）                                    │
│  ├─ ods_user （汇总所有租户数据，去重、标准化）              │
│  特点：跨租户统一存储，原始字段结构，便于下游开发            │
└────────────────────────────┬────────────────────────────────────┘
                             │ 【阶段2：ODS清洗维度化到DWD】
                             │ 工具：Spark SQL
                             │ 特点：业务规则应用、维度关联、脱敏
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  DWD层（明细数据层 - Hive）                                    │
│  ├─ dwd_user （维度化、业务属性加工）                          │
│  ├─ dwd_order （事实表）                                       │
│  特点：已加工、含业务属性、支持多维分析                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ 【阶段3：DWD聚合计算到DWS】
                             │ 工具：Spark SQL
                             │ 特点：维度聚合、指标计算
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  DWS层（汇总数据层 - Hive）                                    │
│  ├─ dws_user_daily （用户日均指标）                            │
│  ├─ dws_order_stats （订单统计指标）                           │
│  特点：预计算指标、支持快速查询和报表                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ 【阶段4：DWS应用化到ADS】
                             │ 工具：Spark SQL / Python / API
                             │ 特点：宽表、标签、应用专用
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  ADS层（应用数据层 - Hive）                                    │
│  ├─ ads_user_label （用户标签）                                │
│  ├─ ads_order_fact （订单宽表）                                │
│  特点：面向应用、高性能查询、OLAP维表                        │
└─────────────────────────────────────────────────────────────────┘
```

**为什么需要STG缓冲层？**

| 问题 | 无STG方案 | 含STG方案 |
|-----|---------|---------|
| **租户数据隔离** | DataX直写ODS，数据混淆，难以追踪 | STG按租户存储，ODS进行汇总处理 ✓ |
| **问题排查** | ODS中无原始数据，无法复审 | STG保留原始数据，便于审计 ✓ |
| **增量效率** | ODS汇总时需扫描全量数据 | 只需扫描当日新增的STG数据，性能好 ✓ |
| **成本分配** | 难以统计各租户的存储成本 | STG按租户分区，易于成本分摊 ✓ |
| **并发控制** | 所有租户竞争同一ODS写入 | STG写入互不影响，ODS顺序汇总 ✓ |
| **失败重试** | 重新执行整个ODS流程 | 只需重试该租户的STG→ODS步骤 ✓ |
                             │ 【第一阶段：原始数据采集】
                             │ 工具：DataX（推荐）/ Sqoop
                             │ 特点：专业数据同步工具，支持异构DB，性能好
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  ODS层（Hive/HDFS - 原始数据层）                               │
│  特点：完整保留源表结构，无任何处理                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ 【第二阶段：数据清洗和维度化】
                             │ 工具：Spark SQL / Hive SQL
                             │ 特点：分布式计算，支持复杂转换
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  DWD层（Hive - 明细数据层）                                    │
│  特点：去重、清洗、维度化、脱敏                                │
└────────────────────────────┬────────────────────────────────────┘
                             │ 【第三阶段：数据聚合计算】
                             │ 工具：Spark SQL / Hive SQL
                             │ 特点：复杂统计和同环比计算
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  DWS层（Hive - 汇总数据层）                                    │
│  特点：维度聚合、指标计算、派生字段                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ 【第四阶段：应用转化】
                             │ 工具：Spark SQL / Python / API
                             │ 特点：面向特定应用的数据转化
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  ADS层（Hive - 应用数据层）                                    │
│  特点：宽表、标签、OLAP维表                                    │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 工具选择矩阵

| 集成阶段 | 工具选择 | 应用场景 | 优点 | 缺点 |
|---------|--------|--------|------|------|
| **外部→ODS** | DataX | 异构数据库同步到Hive | 专业工具、配置灵活、性能优异 | 学习成本、维护复杂 |
| **外部→ODS** | Sqoop | MySQL→HDFS/Hive | 简单易用、官方支持 | 性能一般、功能简单 |
| **ODS→DWD** | Spark SQL | 数据清洗、维度化、脱敏 | 分布式、性能好、支持复杂转换 | 需要开发 |
| **DWD→DWS** | Spark SQL | 聚合计算、同环比 | 分布式、支持开窗函数 | 需要开发 |
| **DWS→ADS** | Spark SQL | 应用宽表生成 | 灵活、支持复杂业务逻辑 | 需要开发 |
| **准实时** | Spark Streaming | 流式数据处理 | 实时性强、与Spark生态统一 | 开发复杂 |

#### 3.3.3 集成模式（按时效性分类）

**1. 离线批量集成（最常用）**
```
特点：定时执行、增量/全量、容错能力强
场景：日常T+1数据同步、DW内部数据处理
工具链：
  - ODS采集：DataX（外部→Hive）
  - DWD/DWS处理：Spark SQL
  - 调度方式：Celery Beat + Cron表达式
示例：
  DAY_0 02:00 - DataX执行全量/增量同步：MySQL user表 → ods_user (Hive)
  DAY_0 04:00 - Spark SQL执行DWD清洗：ods_user → dwd_user
  DAY_0 06:00 - Spark SQL执行DWS聚合：dwd_user → dws_user_daily
```

**2. 准实时集成（分钟级）**
```
特点：高频DataX任务 / Spark Streaming
场景：订单、交易等关键数据10分钟更新一次
工具链：
  - 高频DataX调度：每10分钟执行一次增量抽取
  - 或使用Spark Streaming：消费Kafka → Hive
调度方式：Celery Beat 高频调度
示例：
  每10分钟执行一次 DataX：MySQL orders表 → ods_orders (Hive)
  Spark Streaming 持续消费订单日志 → real_time_orders
```

**3. 实时流集成（秒级）**
```
特点：实时性强、变更驱动、需要特殊引擎
场景：用户行为、支付交易等需要秒级响应
工具链：
  - CDC工具：Canal/Flink CDC 监听MySQL binlog
  - 流处理：Spark Streaming / Flink
  - 存储：Hive / Kafka
架构：
  MySQL binlog → Canal → Kafka → Spark Streaming/Flink → Hive
```

#### 3.3.4 执行引擎架构（多工具适配+STG支持）

**STG层执行策略**：

多租户分库场景下，执行流程如下：

```
【Step 1】：多租户DataX采集 → STG
  - 为每个租户执行一次DataX任务
  - 数据写入：/warehouse/stg/{table}/tenant_id={A|B|C}/ds={date}/
  
【Step 2】：STG→ODS跨租户汇总（Spark SQL）
  - 读取所有租户STG数据，去重、标准化
  - 写入ODS：/warehouse/ods/{table}/ds={date}/
  
【Step 3-5】：ODS→DWD→DWS→ADS（Spark SQL）
  - 清洗、维度化、聚合、应用化
```

基于不同的集成阶段，执行引擎需要支持多种执行工具的适配：

```python
class ExecutionEngine:
    """集成任务执行引擎（统一接口，多工具适配+STG支持）"""
    
    def execute(self, task: IntegrationTask, execution_context: ExecutionContext):
        """
        根据任务类型和所在DW层级选择合适的执行工具
        """
        # 1. 前置检查
        self.pre_execute_check(task)
        
        # 2. 初始化执行日志
        log = IntegrationExecutionLog.objects.create(
            task=task,
            status='running',
            execution_engine=self.get_engine_type(task)
        )
        
        # 3. 根据任务类型选择执行引擎（★ 优先处理STG相关任务）
        if task.target_layer == 'stg' and task.is_stg_task:
            # ========== STG采集（多租户）：DataX ==========
            result = self.execute_stg_datax(task, log)
            log.execution_engine = 'datax_stg'
        elif task.task_type == 'ods_summary':
            # ========== STG→ODS汇总：Spark SQL ==========
            result = self.execute_stg_to_ods(task, log)
            log.execution_engine = 'spark_sql_stg_agg'
        elif task.task_type in ['ods_full', 'ods_incremental']:
            # ODS层：使用DataX进行外部数据源集成
            result = self.execute_with_datax(task, log)
            log.execution_engine = 'datax'
        elif task.task_type in ['dwd_dimension', 'dwd_fact', 'dwd_cleaning']:
            # DWD层：使用Spark SQL进行数据清洗和维度化
            result = self.execute_with_spark_sql(task, log)
            log.execution_engine = 'spark_sql'
        elif task.task_type in ['dws_agg', 'dws_union']:
            # DWS层：使用Spark SQL进行聚合计算
            result = self.execute_with_spark_sql(task, log)
            log.execution_engine = 'spark_sql'
        elif task.task_type == 'ads_app':
            # ADS层：可使用Spark SQL或Python
            result = self.execute_with_spark_sql(task, log)
            log.execution_engine = 'spark_sql'
        elif task.schedule_type == 'realtime':
            # 实时：使用Spark Streaming或Flink
            result = self.execute_with_spark_streaming(task, log)
            log.execution_engine = 'spark_streaming'
        else:
            raise ValueError(f"Unsupported task type: {task.task_type}")
        
        # 4. 更新执行日志
        self.update_execution_log(log, result)
        
        # 5. 后置处理（数据质量检测、元数据同步等）
        self.post_execute_process(task, log, result)
        
        return result
    
    def execute_stg_datax(self, task, log):
        """执行STG层DataX采集（多租户隔离）"""
        executor = DataXExecutorForSTG(task)
        return executor.execute(task)
    
    def execute_stg_to_ods(self, task, log):
        """执行STG→ODS汇总（跨租户去重、标准化）"""
        executor = STGToODSAggregator(task)
        return executor.execute(task)
    
    def get_engine_type(self, task) -> str:
        """获取适合任务的执行引擎类型"""
        if task.target_layer == 'stg' and task.is_stg_task:
            return 'datax_stg'
        elif task.task_type == 'ods_summary':
            return 'spark_sql_stg_agg'
        elif task.task_type in ['ods_full', 'ods_incremental']:
            return 'datax'
        elif task.task_type in ['dwd_dimension', 'dwd_fact', 'dwd_cleaning', 'dws_agg', 'dws_union', 'ads_app']:
            return 'spark_sql'
        elif task.schedule_type == 'realtime':
            return 'spark_streaming'
        return 'unknown'


class DataXExecutorForSTG:
    """
    STG层专用DataX执行器
    特点：支持按租户分区、数据源追踪
    """
    
    def execute(self, task):
        """为每个租户执行DataX采集"""
        config = self.generate_stg_config(task)
        
        # 添加字段变换器（追踪字段）
        config['job']['content'][0]['transformer'] = [
            {
                "name": "script",
                "parameter": {
                    "scriptType": "python",
                    "content": f"""
import json
from datetime import datetime

def transform(record):
    # 为每行数据添加追踪字段
    record['tenant_id'] = '{task.tenant_id_field}'
    record['source_id'] = '{task.source_datasource.id}'
    record['etl_load_time'] = datetime.now().isoformat()
    return record
"""
                }
            }
        ]
        
        runner = DataXJobRunner()
        result = runner.run_job(config, task)
        
        return result
    
    def generate_stg_config(self, task):
        """生成STG层的DataX配置"""
        return {
            "job": {
                "content": [{
                    "reader": self._build_reader(task),
                    "writer": {
                        "name": "hdfswriter",
                        "parameter": {
                            # ★ 关键：按租户+日期分区
                            "path": f"hdfs://namenode:9000/warehouse/stg/{task.business_domain}/{task.source_tables[0]['table']}/tenant_id={task.tenant_id_field}/ds=${{ds}}/",
                            "fileType": "orc",
                            "compress": "SNAPPY",
                            "writeMode": "append"
                        }
                    }
                }],
                "setting": {"speed": {"channel": 4}, "errorLimit": {"percentage": 0.01}}
            }
        }


class STGToODSAggregator:
    """
    STG→ODS跨租户聚合执行器
    功能：将多个租户的原始数据汇总、去重、标准化
    """
    
    def execute(self, task):
        """STG数据汇总到ODS"""
        from pyspark.sql import SparkSession, Window
        from pyspark.sql.functions import row_number, desc, col, lower, trim
        
        spark = SparkSession.builder.appName('stg-to-ods').enableHiveSupport().getOrCreate()
        
        # Step 1：读取所有租户的STG数据（当前分区）
        stg_df = spark.sql(f"SELECT * FROM stg_{task.target_table} WHERE ds = '{self.get_current_date()}'")
        
        # Step 2：数据标准化（全局处理）
        std_df = stg_df.withColumn('email', lower(trim(col('email')))) \
            .na.fill('unknown', ['user_type'])
        
        # Step 3：去重（租户维度）
        dedup_window = Window.partitionBy('tenant_id', 'id').orderBy(desc('updated_at'))
        dedup_df = std_df.withColumn('rn', row_number().over(dedup_window)) \
            .filter(col('rn') == 1).drop('rn')
        
        # Step 4：质量检查
        validated = dedup_df.filter(col('id').isNotNull()).filter(col('tenant_id').isNotNull())
        
        # Step 5：写入ODS（UPSERT）
        validated.write.mode('overwrite').partitionBy('ds') \
            .insertInto(f'ods_{task.target_table}')
        
        # Step 6：刷新分区
        spark.sql(f"MSCK REPAIR TABLE ods_{task.target_table}")
        
        return {
            'success': True,
            'target_records': validated.count(),
            'error_message': ''
        }


class DataXExecutor(ExecutionEngine):
    """
    DataX执行器：用于外部数据源 → Hive/HDFS的数据同步
    支持：MySQL、Oracle、PostgreSQL、MongoDB、FTP、文件等
    """
    
    def execute_with_datax(self, task: IntegrationTask, log: IntegrationExecutionLog):
        """
        使用DataX进行数据同步
        DataX会自动处理：
        - 并发读取源数据
        - 类型转换
        - 写入Hive分区
        - 错误重试
        """
        try:
            # 1. 生成DataX JSON配置
            datax_config = self.generate_datax_config(task)
            
            # 2. 保存配置文件
            config_path = self.save_datax_config(datax_config)
            
            # 3. 执行DataX任务
            # 执行命令：python /datax/bin/datax.py config.json
            result = self.run_datax_job(config_path, task)
            
            log.source_row_count = result['source_records']
            log.target_row_count = result['target_records']
            log.status = 'success' if result['success'] else 'failed'
            log.error_message = result.get('error_message', '')
            
            # 4. 更新Hive分区元数据
            if result['success']:
                self.update_hive_partitions(task)
            
            return result
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            raise
    
    def generate_datax_config(self, task: IntegrationTask) -> dict:
        """
        生成DataX JSON配置
        示例配置：
        {
          "job": {
            "content": [
              {
                "reader": {
                  "name": "mysqlreader",
                  "parameter": {
                    "username": "root",
                    "password": "xxx",
                    "column": ["id", "name", "update_time"],
                    "connection": [{
                      "jdbcUrl": ["jdbc:mysql://host:3306/db"],
                      "table": ["user"]
                    }],
                    "where": "update_time > '${last_checkpoint}'",
                    "fetchSize": 1024
                  }
                },
                "writer": {
                  "name": "hdfswriter",
                  "parameter": {
                    "path": "hdfs://namenode:9000/warehouse/ods_user/${ds}/",
                    "fileName": "data",
                    "fileType": "orc",
                    "column": [{"name": "id", "type": "bigint"}, ...],
                    "writeMode": "append",
                    "compress": "SNAPPY"
                  }
                }
              }
            ]
          }
        }
        """
        source_info = task.source_datasource.info
        target_info = task.target_datasource.info
        
        # 根据源数据库类型选择reader
        reader_config = {
            'name': f'{source_info["db_type"]}reader',
            'parameter': {
                'username': source_info['username'],
                'password': source_info['password'],
                'connection': [{
                    'jdbcUrl': [self.build_jdbc_url(source_info)],
                    'table': [t['table'] for t in task.source_tables]
                }],
                'column': self.get_source_columns(task),
            }
        }
        
        # 添加增量过滤条件
        if task.incremental_type != 'full':
            checkpoint = self.get_last_checkpoint(task)
            reader_config['parameter']['where'] = \
                f"{task.incremental_field} > '{checkpoint}'"
        
        # 根据目标类型选择writer（通常为Hive）
        writer_config = {
            'name': 'hdfswriter',
            'parameter': {
                'path': self.build_hive_path(task),
                'fileName': 'data',
                'fileType': 'orc',  # 推荐使用ORC格式
                'column': self.get_target_columns(task),
                'writeMode': 'append' if task.incremental_type != 'full' else 'truncate',
                'compress': 'SNAPPY'
            }
        }
        
        config = {
            'job': {
                'content': [{
                    'reader': reader_config,
                    'writer': writer_config
                }],
                'setting': {
                    'speed': {
                        'channel': 4,  # 并发通道数
                        'byte': 1048576  # 1MB
                    }
                }
            }
        }
        
        return config
    
    def run_datax_job(self, config_path: str, task: IntegrationTask) -> dict:
        """
        执行DataX任务
        """
        import subprocess
        import json
        
        try:
            # 执行DataX命令
            cmd = f'python /datax/bin/datax.py {config_path}'
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=task.timeout_minutes * 60)
            
            if process.returncode != 0:
                return {
                    'success': False,
                    'error_message': stderr,
                    'source_records': 0,
                    'target_records': 0
                }
            
            # 解析DataX输出获取统计信息
            stats = self.parse_datax_output(stdout)
            
            return {
                'success': True,
                'source_records': stats.get('source_records', 0),
                'target_records': stats.get('target_records', 0),
                'error_message': ''
            }
            
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                'success': False,
                'error_message': f'DataX job timeout after {task.timeout_minutes} minutes',
                'source_records': 0,
                'target_records': 0
            }
    
    def update_hive_partitions(self, task: IntegrationTask):
        """
        更新Hive分区元数据（刷新MSC）
        """
        # 连接Hive，执行MSCK REPAIR TABLE命令
        hive_executor = self.get_hive_executor(task.target_datasource)
        partition_sql = f"MSCK REPAIR TABLE {task.target_database}.{task.target_table}"
        hive_executor.execute(partition_sql)


class SparkSQLExecutor(ExecutionEngine):
    """
    Spark SQL执行器：用于DW内部数据处理（ODS→DWD→DWS→ADS）
    支持：Hive表关联、复杂转换、聚合计算、窗口函数等
    """
    
    def execute_with_spark_sql(self, task: IntegrationTask, log: IntegrationExecutionLog):
        """
        使用Spark SQL进行数据处理
        """
        try:
            # 1. 根据转换配置生成Spark SQL
            spark_sql = self.generate_spark_sql(task)
            
            # 2. 提交Spark作业
            app_id = self.submit_spark_job(task, spark_sql)
            
            # 3. 等待Spark作业完成
            result = self.wait_for_spark_job(app_id, task.timeout_minutes)
            
            if result['success']:
                # 4. 从Hive查询目标表数据统计
                stats = self.get_table_stats(task)
                log.target_row_count = stats['row_count']
                log.status = 'success'
            else:
                log.status = 'failed'
                log.error_message = result.get('error_message', '')
            
            return result
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            raise
    
    def generate_spark_sql(self, task: IntegrationTask) -> str:
        """
        根据转换配置生成Spark SQL
        
        示例：将ODS用户表清洗、脱敏、去重后写入DWD层
        
        CREATE TABLE IF NOT EXISTS dwd_user (
            user_id BIGINT,
            user_name STRING,
            user_phone STRING,
            gender STRING,
            age INT,
            region_id BIGINT,
            region_name STRING,
            ds STRING
        )
        PARTITIONED BY (ds STRING)
        STORED AS ORC;
        
        INSERT OVERWRITE TABLE dwd_user PARTITION(ds='${ds}')
        SELECT
            a.user_id,
            a.user_name,
            CONCAT(SUBSTR(a.user_phone, 1, 3), '****', SUBSTR(a.user_phone, 8)) AS user_phone,
            CASE
                WHEN a.gender = 'M' THEN 'male'
                WHEN a.gender = 'F' THEN 'female'
                ELSE 'unknown'
            END AS gender,
            CAST(a.age AS INT) AS age,
            b.region_id,
            b.region_name
        FROM (
            SELECT DISTINCT
                user_id,
                user_name,
                user_phone,
                gender,
                age
            FROM ods_user
            WHERE ds='${ds}' AND user_id IS NOT NULL
        ) a
        LEFT JOIN dim_region b ON a.region_code = b.region_code
        """
        
        transform_config = task.transform_config
        
        # 1. 构造SELECT子句（字段映射+转换）
        select_clause = self.build_select_clause(task, transform_config)
        
        # 2. 构造FROM子句（源表+去重）
        from_clause = self.build_from_clause(task, transform_config)
        
        # 3. 构造JOIN子句（维度关联）
        join_clause = self.build_join_clause(task, transform_config)
        
        # 4. 构造WHERE子句（过滤条件+去重）
        where_clause = self.build_where_clause(task, transform_config)
        
        # 5. 组装完整SQL
        target_table_def = self.build_target_table_def(task)
        
        sql = f"""
        {target_table_def}
        INSERT OVERWRITE TABLE {task.target_database}.{task.target_table} 
            PARTITION(ds='${{ds}}')
        {select_clause}
        {from_clause}
        {join_clause}
        {where_clause}
        """
        
        return sql
    
    def submit_spark_job(self, task: IntegrationTask, spark_sql: str) -> str:
        """
        提交Spark SQL作业到Yarn集群
        """
        import subprocess
        import uuid
        
        app_name = f"data_integration_{task.id}_{uuid.uuid4()}"
        
        cmd = [
            'spark-submit',
            '--master', 'yarn',
            '--deploy-mode', 'cluster',
            '--driver-memory', '4g',
            '--executor-memory', '4g',
            '--executor-cores', '4',
            '--num-executors', '10',
            '--queue', 'default',
            '--name', app_name,
            '--class', 'org.apache.spark.sql.hive.HiveContext',
            '/opt/spark/scripts/spark_sql_runner.py',
            spark_sql
        ]
        
        # 提交作业并获取application ID
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 解析output获取app_id
        for line in result.stdout.split('\n'):
            if 'application_' in line:
                return line.strip()
        
        raise Exception(f"Failed to submit Spark job: {result.stderr}")
    
    def wait_for_spark_job(self, app_id: str, timeout_minutes: int) -> dict:
        """
        等待Spark作业完成并获取结果
        """
        import time
        import requests
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while True:
            # 查询Yarn应用状态
            status_url = f"http://yarn-resourcemanager:8088/ws/v1/cluster/apps/{app_id}"
            response = requests.get(status_url)
            
            if response.status_code == 200:
                app_info = response.json()['app']
                state = app_info['state']
                
                if state == 'FINISHED':
                    final_status = app_info['finalStatus']
                    return {
                        'success': final_status == 'SUCCEEDED',
                        'error_message': '' if final_status == 'SUCCEEDED' else 'Spark job failed'
                    }
                elif state in ['FAILED', 'KILLED']:
                    return {
                        'success': False,
                        'error_message': f'Spark job {state}'
                    }
            
            # 检查超时
            if time.time() - start_time > timeout_seconds:
                return {
                    'success': False,
                    'error_message': f'Spark job timeout after {timeout_minutes} minutes'
                }
            
            # 每30秒检查一次
            time.sleep(30)


class SparkStreamingExecutor(ExecutionEngine):
    """
    Spark Streaming执行器：用于实时或准实时数据处理
    """
    
    def execute_with_spark_streaming(self, task: IntegrationTask, log: IntegrationExecutionLog):
        """
        使用Spark Streaming进行实时数据处理
        """
        # 1. 创建Spark Streaming应用
        # 2. 定义数据源（Kafka、Hive等）
        # 3. 定义转换逻辑
        # 4. 定义输出目标（Hive表）
        # 5. 持续运行
        pass


# 数据模型更新：记录执行引擎类型
class IntegrationExecutionLog(BaseModel):
    """集成执行日志"""
    task = models.ForeignKey(IntegrationTask, on_delete=models.CASCADE, related_name='execution_logs')
    
    # 执行信息
    execution_id = models.CharField(max_length=64, unique=True)
    # 【新增】执行引擎类型
    execution_engine = models.CharField(
        max_length=30,
        choices=[
            ('datax', 'DataX'),
            ('spark_sql', 'Spark SQL'),
            ('spark_streaming', 'Spark Streaming'),
            ('flink', 'Flink'),
            ('python', 'Python Script'),
        ],
        verbose_name='执行引擎'
    )
    # 【新增】Spark/DataX应用ID
    application_id = models.CharField(max_length=64, blank=True, verbose_name='应用ID')
    
    status = models.CharField(max_length=20, choices=[
        ('waiting', '待执行'),
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('timeout', '超时'),
        ('skipped', '跳过'),
    ])
    
    # ... 其他字段保持不变
```

---

### 3.4 数据质量管理

在数据仓库中，数据质量至关重要。质量规则应该贯穿整个集成过程。

#### 3.4.1 质量规则引擎

```python
class QualityRule(BaseModel):
    """数据质量规则"""
    
    RULE_TYPES = [
        ('null_check', 'NULL值检查'),
        ('unique_check', '唯一性检查'),
        ('format_check', '格式检查'),
        ('range_check', '范围检查'),
        ('consistency_check', '一致性检查'),
        ('completeness_check', '完整性检查'),
        ('timeliness_check', '及时性检查'),
    ]
    
    rule_name = models.CharField(max_length=128)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)
    task = models.ForeignKey(IntegrationTask, on_delete=models.CASCADE)
    
    # 规则配置（JSON）
    config = models.JSONField()
    # 示例：
    # {
    #   "field": "user_id",
    #   "operator": "is_not_null",
    #   "threshold": 0,  // 允许的失败百分比
    #   "action": "reject"  // reject|alert|skip
    # }
    
    # 规则状态
    enabled = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'dataintegration_quality_rule'


class QualityCheckResult(BaseModel):
    """质量检查结果"""
    execution_log = models.ForeignKey(IntegrationExecutionLog, on_delete=models.CASCADE)
    rule = models.ForeignKey(QualityRule, on_delete=models.CASCADE)
    
    # 检查结果
    status = models.CharField(max_length=20, choices=[
        ('passed', '通过'),
        ('warning', '警告'),
        ('failed', '失败'),
    ])
    
    # 统计信息
    total_records = models.IntegerField()
    passed_records = models.IntegerField()
    failed_records = models.IntegerField()
    passed_rate = models.FloatField()  # %
    
    # 问题记录
    issue_sample = models.JSONField(default=list)  # 问题样本
    issue_detail = models.TextField(blank=True)
    
    class Meta:
        db_table = 'dataintegration_quality_check_result'
```

#### 3.4.2 质量检查流程

```python
class QualityChecker:
    """数据质量检查器"""
    
    def check_quality(self, execution_log: IntegrationExecutionLog):
        """
        对集成任务的目标数据进行质量检查
        """
        task = execution_log.task
        target_data = self.fetch_target_data(task)
        
        # 遍历所有应用于该任务的质量规则
        for rule in task.quality_rules:
            result = self.check_single_rule(rule, target_data)
            
            # 保存检查结果
            QualityCheckResult.objects.create(
                execution_log=execution_log,
                rule=rule,
                status=result['status'],
                total_records=result['total_records'],
                passed_records=result['passed_records'],
                failed_records=result['failed_records'],
                passed_rate=result['passed_rate'],
                issue_sample=result['issue_sample'][:100]  # 仅保存前100个问题样本
            )
            
            # 如果检查失败且action为reject，则标记整个任务失败
            if result['status'] == 'failed' and rule['config'].get('action') == 'reject':
                raise QualityCheckException(f"Quality check failed: {rule.rule_name}")
        
        return True
    
    def check_single_rule(self, rule: QualityRule, data):
        """检查单条规则"""
        rule_type = rule.rule_type
        config = rule.config
        
        if rule_type == 'null_check':
            return self._check_null(data, config)
        elif rule_type == 'unique_check':
            return self._check_unique(data, config)
        elif rule_type == 'format_check':
            return self._check_format(data, config)
        # ... 其他检查类型
    
    def _check_null(self, data, config):
        """NULL值检查"""
        field = config['field']
        null_count = sum(1 for row in data if row[field] is None)
        passed_count = len(data) - null_count
        
        passed_rate = (passed_count / len(data)) * 100
        
        return {
            'status': 'passed' if passed_rate >= (100 - config['threshold']) else 'failed',
            'total_records': len(data),
            'passed_records': passed_count,
            'failed_records': null_count,
            'passed_rate': passed_rate,
            'issue_sample': [row for row in data if row[field] is None]
        }
```

---

### 3.5 数据血缘管理

数据血缘是数据仓库的重要资产，用于影响分析、数据溯源等。

#### 3.5.1 血缘数据模型

```python
class DataLineage(BaseModel):
    """数据血缘关系"""
    
    # 源端信息
    source_table = models.CharField(max_length=128)
    source_database = models.CharField(max_length=128)
    source_field = models.CharField(max_length=128, blank=True)  # 字段级血缘
    
    # 目标端信息
    target_table = models.CharField(max_length=128)
    target_database = models.CharField(max_length=128)
    target_field = models.CharField(max_length=128, blank=True)
    
    # 关联任务
    task = models.ForeignKey(IntegrationTask, on_delete=models.CASCADE)
    
    # 转换关系
    transformation = models.CharField(max_length=256, blank=True)  # 转换描述
    
    # 血缘类型
    lineage_type = models.CharField(max_length=20, choices=[
        ('direct', '直接'),  // 源字段直接映射到目标字段
        ('transform', '转换'),  // 源字段经过转换得到目标字段
        ('aggregate', '聚合'),  // 多个源字段聚合为目标字段
    ])
    
    class Meta:
        db_table = 'dataintegration_lineage'
        indexes = [
            models.Index(fields=['source_table', 'target_table']),
            models.Index(fields=['target_field']),
        ]


class LineageGraph:
    """血缘关系图管理"""
    
    def build_lineage(self, task: IntegrationTask):
        """
        基于任务配置构建血缘关系
        """
        transform_config = task.transform_config
        field_mapping = transform_config.get('field_mapping', {})
        
        for target_field, mapping_info in field_mapping.items():
            source_field = mapping_info['source_field']
            source_table = mapping_info['source_table']
            
            DataLineage.objects.create(
                source_table=source_table,
                source_database=mapping_info.get('source_database'),
                source_field=source_field,
                target_table=task.target_table,
                target_database=task.target_database,
                target_field=target_field,
                task=task,
                transformation=mapping_info.get('transformation', ''),
                lineage_type='direct' if not mapping_info.get('transformation') else 'transform'
            )
    
    def get_upstream_lineage(self, table: str, field: str = None):
        """
        获取上游血缘（该表的数据来自哪些源表）
        """
        if field:
            return DataLineage.objects.filter(
                target_table=table,
                target_field=field
            ).select_related('task')
        else:
            return DataLineage.objects.filter(
                target_table=table
            ).distinct('source_table').select_related('task')
    
    def get_downstream_lineage(self, table: str, field: str = None):
        """
        获取下游血缘（该表的数据被哪些表使用）
        """
        if field:
            return DataLineage.objects.filter(
                source_table=table,
                source_field=field
            ).select_related('task')
        else:
            return DataLineage.objects.filter(
                source_table=table
            ).distinct('target_table').select_related('task')
    
    def get_impact_analysis(self, table: str):
        """
        影响分析：该表故障会影响哪些下游表
        """
        # BFS遍历获取所有下游表
        visited = set()
        queue = [table]
        impact_tables = []
        
        while queue:
            current_table = queue.pop(0)
            if current_table in visited:
                continue
            visited.add(current_table)
            
            downstream = DataLineage.objects.filter(
                source_table=current_table
            ).values_list('target_table', flat=True).distinct()
            
            for downstream_table in downstream:
                impact_tables.append(downstream_table)
                queue.append(downstream_table)
        
        return impact_tables
```

#### 3.5.2 血缘展示接口

```
# 获取表级血缘
GET /dataintegration/lineage/table/{tableName}/

# 获取字段级血缘
GET /dataintegration/lineage/field/{tableName}/{fieldName}/

# 获取上游血缘（追溯数据源）
GET /dataintegration/lineage/{tableName}/upstream/

# 获取下游血缘（影响分析）
GET /dataintegration/lineage/{tableName}/downstream/

# 影响分析（故障影响范围）
POST /dataintegration/lineage/impact-analysis/
{
  "table": "ods_user",
  "affectType": "full_failure"  // full_failure|data_error
}
返回：受影响的所有下游表及其任务
```

---

### 3.6 监控告警

#### 3.6.1 监控指标

在数据仓库场景中，关键监控指标包括：

```python
MONITORING_METRICS = {
    # 执行指标
    '任务成功率': 'success_count / total_count',
    '任务平均耗时': 'avg(duration_seconds)',
    '任务超时率': 'timeout_count / total_count',
    
    # 数据指标
    '数据延迟': 'current_time - max(update_time)',
    '数据行数变化': '(target_row_count - prev_row_count) / prev_row_count',
    '脏数据比例': 'failed_records / total_records',
    '质量检查失败率': 'failed_checks / total_checks',
    
    # 资源指标
    '任务并发数': 'running_tasks_count',
    '数据库连接数': 'active_connections',
    '磁盘使用率': 'used_disk / total_disk',
}
```

#### 3.6.2 告警规则配置

```python
class AlertRule(BaseModel):
    """集成任务告警规则"""
    
    ALERT_TYPES = [
        ('execution_failure', '执行失败'),
        ('execution_timeout', '执行超时'),
        ('quality_check_failed', '质量检查失败'),
        ('data_delay', '数据延迟'),
        ('unusual_data_volume', '数据量异常'),
        ('resource_exhaustion', '资源耗尽'),
    ]
    
    alert_name = models.CharField(max_length=128)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    task = models.ForeignKey(IntegrationTask, on_delete=models.CASCADE, null=True)
    
    # 触发条件
    condition = models.JSONField()
    # 示例：
    # {
    #   "metric": "execution_failure",
    #   "operator": "==",
    #   "threshold": 3,  // 连续失败3次
    #   "time_window": 3600  // 1小时内
    # }
    
    # 通知配置
    notify_channels = models.CharField(max_length=256)  # email, dingtalk, wechat
    notify_receivers = models.TextField()  # 邮件地址或钉钉ID
    
    # 告警级别
    severity = models.CharField(max_length=10, choices=[
        ('P0', '紧急'),
        ('P1', '重要'),
        ('P2', '一般'),
        ('P3', '提示'),
    ], default='P2')
    
    enabled = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'dataintegration_alert_rule'
```

---

## 四、与数据仓库架构的深度整合

### 4.1 分层管理支持

集成模块应提供对数据仓库分层的原生支持：

```python
class DWLayer:
    """数据仓库分层管理"""
    
    # ODS层：原始数据完整保存，不做任何处理
    # - 字段映射：保持源表结构
    # - 分区：按日期分区，保存全历史
    # - 保留期：根据法律要求（通常3-5年）
    
    # DWD层：数据清洗和维度化
    # - 去重：基于业务主键
    # - 维度加工：关联维度表
    # - 字段脱敏：隐藏敏感信息
    # - 分区：按日期分区
    
    # DWS层：数据聚合和指标计算
    # - 聚合：分组统计
    # - 派生指标：同环比、排名等
    # - 分区：按日期分区
    
    # ADS层：应用数据
    # - 宽表：多表关联的最终表
    # - 无分区或按维度分区
    # - 面向特定应用
```

### 4.2 分区策略

```python
class PartitionStrategy:
    """分区策略配置"""
    
    # 日期分区（最常用）
    PARTITION_DATE = {
        'field': 'ds',  // 分区字段
        'format': 'YYYYMMDD',  // 日期格式
        'retention_days': 365 * 3,  // 保留3年
    }
    
    # 多级分区
    PARTITION_MULTI = {
        'partitions': [
            {'field': 'country', 'type': 'string'},
            {'field': 'ds', 'type': 'date'},
        ]
    }
```

### 4.3 增量策略深度设计

```python
class IncrementalStrategy:
    """增量抽取策略"""
    
    # 1. 基于时间戳的增量
    # 适用场景：源表有update_time字段
    # 优点：简单可靠
    # 缺点：可能漏掉中间删除的数据
    TIMESTAMP_BASED = {
        'type': 'incremental_upsert',
        'field': 'update_time',
        'checkpoint': 'select max(update_time) from target_table'
    }
    
    # 2. 基于日志的增量（CDC）
    # 适用场景：需要捕获删除操作
    # 优点：完整准确
    # 缺点：对源库有要求
    LOG_BASED = {
        'type': 'cdc',
        'source': 'binlog|wal|redo_log',
        'tool': 'canal|flink_cdc|debezium'
    }
    
    # 3. 基于主键的全表对比
    # 适用场景：源表无update_time
    # 优点：准确
    # 缺点：性能较差
    KEY_BASED = {
        'type': 'full_compare',
        'keys': ['user_id'],
        'algorithm': 'hash_based|row_based'
    }
```

---

## 五、前端架构设计

### 5.1 页面结构

```
frontend/src/views/dataintegration/
├── index.vue                        # 首页/任务列表
├── task/
│  ├── list.vue                     # 任务列表
│  ├── create.vue                   # 创建任务
│  ├── edit.vue                     # 编辑任务
│  ├── detail/
│  │  ├── index.vue                # 任务详情
│  │  ├── config.vue               # 配置信息
│  │  ├── transform.vue            # 转换规则
│  │  ├── execution.vue            # 执行历史
│  │  ├── lineage.vue              # 数据血缘
│  │  └── quality.vue              # 质量检查
│  └── version.vue                  # 版本管理
├── execution/
│  ├── index.vue                    # 执行监控
│  ├── logs.vue                     # 执行日志
│  └── detail.vue                   # 日志详情
├── monitor/
│  ├── dashboard.vue                # 监控仪表板
│  ├── metrics.vue                  # 关键指标
│  ├── alerts.vue                   # 告警管理
│  └── rules.vue                    # 告警规则
├── lineage/
│  ├── index.vue                    # 血缘可视化
│  ├── impact.vue                   # 影响分析
│  └── detail.vue                   # 血缘详情
├── quality/
│  ├── rules.vue                    # 质量规则
│  └── reports.vue                  # 质量报告
└── components/
   ├── TaskForm.vue                 # 任务表单
   ├── TransformEditor.vue          # 转换编辑器
   ├── LineageGraph.vue             # 血缘关系图
   └── ExecutionChart.vue           # 执行统计图
```

### 5.2 任务配置表单

```vue
<template>
  <div class="task-form">
    <!-- 基本信息 -->
    <el-form-item label="任务名称" prop="taskName">
      <el-input v-model="form.taskName" />
    </el-form-item>
    
    <!-- 数据仓库分层选择 -->
    <el-form-item label="DW分层" prop="dwLayer">
      <el-select v-model="form.dwLayer" @change="onLayerChange">
        <el-option label="ODS（原始层）" value="ods" />
        <el-option label="DWD（明细层）" value="dwd" />
        <el-option label="DWS（汇总层）" value="dws" />
        <el-option label="ADS（应用层）" value="ads" />
      </el-select>
    </el-form-item>
    
    <!-- 源端配置 -->
    <el-form-item label="源数据源" prop="sourceDatasourceId">
      <el-select v-model="form.sourceDatasourceId">
        <el-option v-for="ds in datasources" :key="ds.id" :label="ds.name" :value="ds.id" />
      </el-select>
    </el-form-item>
    
    <!-- 源表选择 -->
    <el-form-item label="源表" prop="sourceTables">
      <el-select v-model="form.sourceTables" multiple>
        <el-option v-for="table in availableTables" :key="table.name" 
                   :label="table.name" :value="table" />
      </el-select>
    </el-form-item>
    
    <!-- 目标端配置 -->
    <el-form-item label="目标数据源" prop="targetDatasourceId">
      <el-select v-model="form.targetDatasourceId">
        <el-option v-for="ds in datasources" :key="ds.id" :label="ds.name" :value="ds.id" />
      </el-select>
    </el-form-item>
    
    <!-- 增量策略选择 -->
    <el-form-item label="增量策略" prop="incrementalType">
      <el-select v-model="form.incrementalType" @change="onIncrementalChange">
        <el-option label="全量" value="full" />
        <el-option label="增量追加" value="incremental_append" />
        <el-option label="增量更新" value="incremental_upsert" />
      </el-select>
    </el-form-item>
    
    <!-- 增量字段 -->
    <el-form-item v-if="form.incrementalType !== 'full'" label="增量字段" prop="incrementalField">
      <el-select v-model="form.incrementalField">
        <el-option v-for="field in timestampFields" :key="field" 
                   :label="field" :value="field" />
      </el-select>
    </el-form-item>
    
    <!-- 分区配置 -->
    <el-form-item label="分区类型" prop="partitionType">
      <el-select v-model="form.partitionType">
        <el-option label="日期分区" value="date" />
        <el-option label="维度分区" value="dimension" />
        <el-option label="不分区" value="none" />
      </el-select>
    </el-form-item>
    
    <!-- 调度配置 -->
    <el-form-item label="调度方式" prop="scheduleType">
      <el-select v-model="form.scheduleType">
        <el-option label="Cron表达式" value="cron" />
        <el-option label="固定间隔" value="interval" />
        <el-option label="实时" value="realtime" />
      </el-select>
    </el-form-item>
    
    <el-form-item label="调度配置" prop="scheduleConf">
      <el-input v-model="form.scheduleConf" 
                :placeholder="schedulePlaceholder" />
    </el-form-item>
  </div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        taskName: '',
        dwLayer: 'ods',
        sourceDatasourceId: null,
        sourceTables: [],
        targetDatasourceId: null,
        incrementalType: 'full',
        partitionType: 'date',
        scheduleType: 'cron',
        scheduleConf: '0 2 * * *'
      },
      schedulePlaceholder: '例：0 2 * * *（每日2点）'
    }
  },
  methods: {
    onLayerChange(layer) {
      // 不同分层提示不同的模板
      this.$message.info(`ODS层：原始数据采集；DWD层：数据清洗；DWS层：聚合计算`);
    },
    onIncrementalChange(type) {
      // 增量类型变更时，刷新增量字段选项
      if (type !== 'full') {
        this.fetchTimestampFields();
      }
    }
  }
}
</script>
```

---

## 六、实现路线图

### 6.1 分阶段交付计划

**第一阶段（2周）：核心集成框架**
- [ ] 数据模型设计与迁移
- [ ] 基础CRUD接口实现
- [ ] ODS层采集（全量+增量）
- [ ] 执行日志记录
- [ ] 简单任务调度

**第二阶段（2周）：数据转换与质量**
- [ ] 转换规则引擎
- [ ] 字段映射可视化
- [ ] 数据清洗算子库
- [ ] 质量规则和检查
- [ ] 转换测试功能

**第三阶段（2周）：高级功能**
- [ ] 数据血缘管理
- [ ] 版本管理与回滚
- [ ] 监控告警系统
- [ ] 执行历史查询
- [ ] 分层管理支持

**第四阶段（1周）：优化与测试**
- [ ] 性能优化
- [ ] 全面测试
- [ ] 文档编写
- [ ] 用户培训

### 6.2 技术栈

| 层级 | 技术选型 | 说明 |
|-----|--------|------|
| **后端框架** | Django 5.x + DRF | 任务配置和API |
| **任务调度** | Celery Beat | 定时/周期任务 |
| **执行引擎** | **DataX + Spark SQL** | 阶段化工具选择 |
| **ODS采集** | **DataX** | 异构数据库同步到Hive |
| **DW内部处理** | **Spark SQL** | ODS→DWD→DWS→ADS数据处理 |
| **准实时** | Spark Streaming / DataX高频 | 分钟级数据更新 |
| **实时处理** | Canal / Flink CDC + Spark Streaming | 秒级数据集成 |
| **元数据存储** | MySQL | 任务配置、日志 |
| **数据存储** | **Hive + HDFS** | ODS/DWD/DWS/ADS数据存储 |
| **前端框架** | Vue3 + Element Plus | UI展示 |
| **图表展示** | ECharts + G6 | 数据血缘、执行统计 |

---

## 七、与现有系统的整合

### 7.1 与数据源管理模块的整合
```
DataSource（数据源）
    ↓
复用连接信息、执行器、测试连接能力
    ↓
IntegrationTask（集成任务）
    - source_datasource FK
    - target_datasource FK
```

### 7.2 与元数据管理模块的整合
```
IntegrationTask（集成任务）
    ↓
执行成功后同步元数据
    ↓
MetaTable / MetaColumn（元数据）
    - 目标表字段信息
    - 最后同步时间
    - 数据量
```

### 7.3 与数据任务运维模块的整合
```
IntegrationTask
    ↓
转换为 DataTask（运维任务）
    ↓
集成模块专注"配置和执行"
运维模块专注"监控和告警"
```

---

## 八、关键设计决策

### 决策1：为什么采用阶段化工具选择（DataX + Spark SQL）？

**分阶段工具划分**：
- **ODS层（外部→Hive）**：使用 **DataX**
  - 优势：专业数据同步工具、支持异构DB、性能优异、内置容错
  - DataX特点：并发读取、智能类型转换、自动分区管理
  - 避免Django ORM处理大数据量的性能问题

- **DWD/DWS层（Hive内部处理）**：使用 **Spark SQL**
  - 优势：分布式计算、支持复杂转换、窗口函数、生态完善
  - 与Hive无缝集成、支持ORC存储格式
  - 相比Hive CLI更灵活，支持Python/Scala编写复杂逻辑

**为什么不全用Django ORM或SQLAlchemy？**
- ORM不适合：大数据处理（>GB级）需要分布式计算能力
- 性能问题：单机数据库操作无法应对数据仓库规模
- 生态问题：缺乏时间序列、窗口函数、聚合函数的原生支持

### 决策2：DataX的工作流程和优势

**DataX工作流程**：
```
DataX Job配置（JSON）
  ↓
[Reader]          [Transformer]         [Writer]
MySQL Reader  →   Type Convert    →   HDFS Writer
(并发读取)        数据清洗             (写入Hive分区)
(断点续传)        格式转换             (自动分区创建)
                                        (ORC压缩)
```

**DataX相比手写SQL的优势**：
1. **开箱即用**：无需编写驱动代码，配置即可运行
2. **性能优异**：内置并发调度、内存优化、网络优化
3. **容错能力**：自动重试、断点续传、脏数据隔离
4. **格式转换**：自动处理MySQL→Hive的类型映射
5. **分区管理**：自动创建和刷新Hive分区

**DataX配置示例**（从MySQL到Hive的增量同步）：
```json
{
  "job": {
    "content": [{
      "reader": {
        "name": "mysqlreader",
        "parameter": {
          "username": "root",
          "password": "pass",
          "connection": [{
            "jdbcUrl": ["jdbc:mysql://mysql-host:3306/business_db"],
            "table": ["user_account"]
          }],
          "column": ["id", "name", "email", "update_time"],
          "where": "update_time > '2026-01-20 00:00:00'",
          "fetchSize": 2048
        }
      },
      "writer": {
        "name": "hdfswriter",
        "parameter": {
          "path": "hdfs://namenode:9000/warehouse/ods_user_account/ds=${ds}/",
          "fileName": "data",
          "fileType": "orc",
          "column": [
            {"name": "id", "type": "bigint"},
            {"name": "name", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "update_time", "type": "string"}
          ],
          "writeMode": "append",
          "compress": "SNAPPY"
        }
      }
    }]
  }
}
```

### 决策3：Spark SQL处理DW内部数据的优势

**Spark SQL的应用场景**：

1. **ODS→DWD**：数据清洗和维度化
```sql
-- 清洗用户表：去重、脱敏、维度化
INSERT OVERWRITE TABLE dwd_user PARTITION(ds='${ds}')
SELECT
    a.user_id,
    a.user_name,
    MASK_PHONE(a.user_phone) AS user_phone,  -- 脱敏
    b.region_name,
    b.region_code,
    a.update_time
FROM (
    SELECT DISTINCT  -- 去重
        user_id,
        user_name,
        user_phone,
        region_id,
        update_time
    FROM ods_user
    WHERE ds='${ds}' AND user_id IS NOT NULL
) a
LEFT JOIN dim_region b ON a.region_id = b.region_id
```

2. **DWD→DWS**：聚合计算和同环比
```sql
-- 计算日均订单数和环比
INSERT OVERWRITE TABLE dws_order_daily PARTITION(ds='${ds}')
SELECT
    ds,
    region_id,
    COUNT(DISTINCT order_id) AS order_cnt,
    SUM(order_amount) AS order_amount,
    LAG(COUNT(DISTINCT order_id)) OVER (
        PARTITION BY region_id 
        ORDER BY ds
    ) AS prev_day_order_cnt,
    ROUND(
        (COUNT(DISTINCT order_id) - LAG(COUNT(DISTINCT order_id)) OVER (
            PARTITION BY region_id 
            ORDER BY ds
        )) / LAG(COUNT(DISTINCT order_id)) OVER (
            PARTITION BY region_id 
            ORDER BY ds
        ),
        4
    ) AS order_cnt_pct_change
FROM dwd_order
WHERE ds='${ds}'
GROUP BY ds, region_id
```

3. **DWS→ADS**：宽表生成
```sql
-- 生成用户360度画像宽表
INSERT OVERWRITE TABLE ads_user_profile PARTITION(ds='${ds}')
SELECT
    a.user_id,
    a.user_name,
    b.total_orders,
    b.total_amount,
    c.recent_purchase_date,
    d.user_tags,
    a.update_time
FROM dwd_user a
LEFT JOIN dws_user_order b ON a.user_id = b.user_id AND b.ds='${ds}'
LEFT JOIN dws_user_purchase c ON a.user_id = c.user_id AND c.ds='${ds}'
LEFT JOIN dws_user_tags d ON a.user_id = d.user_id AND d.ds='${ds}'
WHERE a.ds='${ds}'
```

### 决策4：为什么分别支持离线/准实时/实时三种模式？

| 模式 | 场景 | 工具 | 成本 | 实时性 |
|-----|------|------|------|--------|
| **离线** | 日常T+1数据同步、月度汇总 | DataX + Cron | 低 | 小时级 |
| **准实时** | 订单、交易等10分钟更新 | DataX高频 / Spark Streaming | 中 | 分钟级 |
| **实时** | 用户行为、支付等秒级需求 | Canal + Spark Streaming | 高 | 秒级 |

**为什么不全部做实时？**
- 成本：实时架构复杂、基础设施投入大
- 维护：CDC工具（Canal/Flink）学习曲线陡
- 必要性：大多数数据分析不需要秒级实时
- 渐进性：先做离线/准实时，后续再升级

### 决策5：分区策略和增量字段选择

**分区设计**：
```python
# 按日期分区（推荐）
ODS层：/warehouse/ods_user/ds=20260120/
DWD层：/warehouse/dwd_user/ds=20260120/
DWS层：/warehouse/dws_user_daily/ds=20260120/

# 多级分区（可选）
/warehouse/dws_order_daily/ds=20260120/region_id=1/
```

**增量字段选择优先级**：
1. **update_time**：推荐，应用最广，业务含义清晰
2. **modified_at / last_modified**：同等可用
3. **ts / timestamp**：时间戳格式需注意毫秒/秒的区别
4. **modify_date**：日期级粒度，不精确
5. **无增量字段**：使用全表对比（性能差）

---

## 九、分阶段工具集成实现指南

### 9.1 DataX集成步骤

**第一步：安装DataX**
```bash
# 下载DataX
cd /opt
wget https://github.com/alibaba/DataX/releases/download/datax_1.0.0/datax.tar.gz
tar -xzf datax.tar.gz

# 验证安装
python /opt/datax/bin/datax.py -version
```

**第二步：Django中生成和执行DataX配置**
```python
# backend/apps/dataintegration/executors/datax_executor.py

import json
import subprocess
from django.template import Template, Context

class DataXConfigGenerator:
    """生成DataX配置"""
    
    def generate_config(self, task):
        """生成完整的DataX配置"""
        config = {
            "job": {
                "content": [self._build_job_content(task)],
                "setting": self._build_settings(task)
            }
        }
        return config
    
    def _build_job_content(self, task):
        """构建job content"""
        return {
            "reader": self._build_reader(task),
            "writer": self._build_writer(task)
        }
    
    def _build_reader(self, task):
        """根据源数据库类型构建Reader"""
        source = task.source_datasource
        reader_type = self._get_reader_type(source.db_type)
        
        return {
            "name": reader_type,
            "parameter": {
                "username": source.username,
                "password": source.password,
                "connection": [{
                    "jdbcUrl": [self._build_jdbc_url(source)],
                    "table": [t["table"] for t in task.source_tables]
                }],
                "column": self._get_source_columns(task),
                "where": self._build_where_clause(task),
                "fetchSize": 2048,
                "queryTimeout": task.timeout_minutes * 60
            }
        }
    
    def _build_writer(self, task):
        """构建Hive Writer"""
        return {
            "name": "hdfswriter",
            "parameter": {
                "path": self._build_hive_path(task),
                "fileName": "data",
                "fileType": "orc",
                "column": self._get_target_columns(task),
                "writeMode": self._get_write_mode(task),
                "compress": "SNAPPY"
            }
        }
    
    def _build_settings(self, task):
        """构建执行参数"""
        return {
            "speed": {
                "channel": 4,  # 并发通道数
                "byte": 1048576  # 1MB
            },
            "errorLimit": {
                "record": 0,  # 记录数错误限制
                "percentage": 0.01  # 百分比错误限制1%
            }
        }
    
    def _get_reader_type(self, db_type):
        """获取Reader类型"""
        reader_map = {
            'mysql': 'mysqlreader',
            'oracle': 'oraclereader',
            'postgresql': 'postgresqlreader',
            'mongodb': 'mongodbreader',
            'ftp': 'ftpreader',
        }
        return reader_map.get(db_type, 'mysqlreader')
    
    def _build_jdbc_url(self, source):
        """构建JDBC连接字符串"""
        if source.db_type == 'mysql':
            return f"jdbc:mysql://{source.host}:{source.port}/{source.database}?allowMultiQueries=true"
        elif source.db_type == 'oracle':
            return f"jdbc:oracle:thin:@{source.host}:{source.port}:{source.database}"
        # ... 其他数据库类型
    
    def _build_where_clause(self, task):
        """构建过滤条件"""
        if task.incremental_type == 'full':
            return task.source_filter or "1=1"
        else:
            # 增量：基于最后一次checkpoint
            last_checkpoint = self._get_last_checkpoint(task)
            return f"{task.incremental_field} > '{last_checkpoint}'"
    
    def _build_hive_path(self, task):
        """构建Hive HDFS路径"""
        # 支持分区变量替换
        if task.partition_type == 'date':
            return f"hdfs://namenode:9000/warehouse/{task.target_database}/{task.target_table}/ds=${{ds}}/"
        else:
            return f"hdfs://namenode:9000/warehouse/{task.target_database}/{task.target_table}/"
    
    def _get_write_mode(self, task):
        """获取写入模式"""
        # 全量覆盖，增量追加
        return "truncate" if task.incremental_type == 'full' else "append"


class DataXJobRunner:
    """执行DataX任务"""
    
    def run_job(self, config, task):
        """执行DataX任务"""
        import tempfile
        import os
        
        # 替换变量（如${ds}）
        config_str = json.dumps(config)
        config_str = self._replace_variables(config_str)
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(config_str)
            config_file = f.name
        
        try:
            # 执行DataX
            cmd = f'python /opt/datax/bin/datax.py {config_file}'
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=task.timeout_minutes * 60)
            
            # 解析输出
            result = self._parse_datax_output(stdout, stderr, process.returncode)
            
            return result
            
        finally:
            os.unlink(config_file)
    
    def _replace_variables(self, config_str):
        """替换配置中的变量"""
        from datetime import datetime
        
        now = datetime.now()
        variables = {
            'ds': now.strftime('%Y%m%d'),
            'hms': now.strftime('%H%M%S'),
            'year': now.strftime('%Y'),
            'month': now.strftime('%m'),
            'day': now.strftime('%d'),
        }
        
        for key, value in variables.items():
            config_str = config_str.replace(f'${{{key}}}', value)
        
        return config_str
    
    def _parse_datax_output(self, stdout, stderr, returncode):
        """解析DataX输出"""
        result = {
            'success': returncode == 0,
            'error_message': '',
            'source_records': 0,
            'target_records': 0,
        }
        
        if returncode != 0:
            result['error_message'] = stderr
            return result
        
        # 从stdout解析统计信息
        # DataX输出格式: "Read 1000 records, Write 1000 records"
        import re
        
        match_read = re.search(r'Read (\d+) records', stdout)
        if match_read:
            result['source_records'] = int(match_read.group(1))
        
        match_write = re.search(r'Write (\d+) records', stdout)
        if match_write:
            result['target_records'] = int(match_write.group(1))
        
        return result
```

### 9.2 Spark SQL集成步骤

**第一步：编写Spark SQL脚本**
```python
# backend/apps/dataintegration/executors/spark_sql_executor.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import *

class SparkSQLExecutor:
    """Spark SQL执行器"""
    
    def __init__(self, app_name='data-integration'):
        self.spark = SparkSession \
            .builder \
            .appName(app_name) \
            .config("hive.exec.dynamic.partition", "true") \
            .config("hive.exec.dynamic.partition.mode", "nonstrict") \
            .enableHiveSupport() \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("INFO")
    
    def execute_transformation(self, task):
        """执行数据转换"""
        # 1. 读取ODS源表
        source_df = self.spark.sql(f"""
            SELECT * FROM {task.source_datasource.database}.{task.source_tables[0]['table']}
            WHERE ds = '{self._get_ds()}'
        """)
        
        # 2. 应用转换规则
        transformed_df = self._apply_transformations(source_df, task.transform_config)
        
        # 3. 应用质量规则检查
        validated_df = self._apply_quality_rules(transformed_df, task.quality_rules)
        
        # 4. 写入目标表（ORC格式，分区存储）
        validated_df.coalesce(10).write \
            .mode("overwrite") \
            .format("orc") \
            .partitionBy("ds") \
            .option("path", f"hdfs://namenode:9000/warehouse/{task.target_database}/{task.target_table}") \
            .saveAsTable(f"{task.target_database}.{task.target_table}")
        
        # 5. 刷新分区
        self.spark.sql(f"MSCK REPAIR TABLE {task.target_database}.{task.target_table}")
        
        # 6. 获取统计信息
        stats = self.spark.sql(f"""
            SELECT COUNT(*) as row_count FROM {task.target_database}.{task.target_table}
            WHERE ds = '{self._get_ds()}'
        """).collect()[0]
        
        return {
            'success': True,
            'row_count': stats.row_count,
            'error_message': ''
        }
    
    def _apply_transformations(self, df, transform_config):
        """应用转换规则"""
        # 应用字段清洗
        for field_name, field_config in transform_config.get('field_mapping', {}).items():
            operation = field_config.get('operation')
            
            if operation == 'mask_phone':
                # 脱敏手机号：****XXXX
                df = df.withColumn(
                    field_name,
                    concat(lit("****"), substring(col(field_name), 8, 4))
                )
            elif operation == 'type_convert':
                # 类型转换
                to_type = field_config.get('to_type')
                df = df.withColumn(field_name, col(field_name).cast(to_type))
            elif operation == 'null_fill':
                # NULL填充
                default_value = field_config.get('default_value')
                df = df.na.fill(default_value, [field_name])
        
        # 去重
        if transform_config.get('dedup_config', {}).get('enabled'):
            dedup_keys = transform_config['dedup_config'].get('keys', [])
            df = df.dropDuplicates(dedup_keys)
        
        # 维度关联
        for join_config in transform_config.get('joins', []):
            dim_table = join_config['dim_table']
            on_condition = join_config['on']
            
            dim_df = self.spark.sql(f"SELECT * FROM {dim_table}")
            df = df.join(dim_df, on_condition, join_config.get('join_type', 'left'))
        
        return df
    
    def _apply_quality_rules(self, df, quality_rules):
        """应用质量规则"""
        for rule in quality_rules:
            rule_type = rule.get('rule_type')
            
            if rule_type == 'null_check':
                # NULL值检查
                field = rule.get('field')
                df = df.filter(col(field).isNotNull())
            
            elif rule_type == 'range_check':
                # 范围检查
                field = rule.get('field')
                min_val = rule.get('min')
                max_val = rule.get('max')
                df = df.filter((col(field) >= min_val) & (col(field) <= max_val))
        
        return df
    
    def _get_ds(self):
        """获取当前分区日期"""
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d')
    
    def close(self):
        """关闭Spark会话"""
        self.spark.stop()
```

**第二步：提交Spark作业到Yarn集群**
```python
class SparkJobSubmitter:
    """提交Spark作业到Yarn"""
    
    def submit_job(self, task, spark_sql_script):
        """提交Spark SQL作业"""
        import subprocess
        
        cmd = [
            'spark-submit',
            '--master', 'yarn',
            '--deploy-mode', 'cluster',
            '--driver-memory', '4g',
            '--executor-memory', '4g',
            '--executor-cores', '4',
            '--num-executors', '10',
            '--queue', 'default',
            '--conf', 'spark.sql.adaptive.enabled=true',
            '--conf', 'spark.sql.shuffle.partitions=200',
            '--conf', 'spark.default.parallelism=400',
            '--name', f'data-integration-{task.id}',
            '/opt/spark-scripts/runner.py',
            spark_sql_script
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 解析application ID
        for line in result.stdout.split('\n'):
            if 'application_' in line:
                return line.strip()
        
        raise Exception(f"Failed to submit Spark job: {result.stderr}")
```

### 9.3 调度流程（示例）

```python
# 完整的集成任务执行流程

from celery import shared_task

@shared_task
def execute_integration_task(task_id):
    """执行集成任务（由Celery Beat调度）"""
    
    task = IntegrationTask.objects.get(id=task_id)
    
    # 1. 创建执行日志
    log = IntegrationExecutionLog.objects.create(
        task=task,
        status='running'
    )
    
    try:
        if task.task_type in ['ods_full', 'ods_incremental']:
            # ========== ODS层：使用DataX ==========
            generator = DataXConfigGenerator()
            config = generator.generate_config(task)
            
            runner = DataXJobRunner()
            result = runner.run_job(config, task)
            
            log.execution_engine = 'datax'
            log.source_row_count = result['source_records']
            log.target_row_count = result['target_records']
            
        else:
            # ========== DWD/DWS层：使用Spark SQL ==========
            executor = SparkSQLExecutor()
            
            result = executor.execute_transformation(task)
            
            log.execution_engine = 'spark_sql'
            log.target_row_count = result['row_count']
            executor.close()
        
        # 2. 质量检查
        quality_checker = QualityChecker()
        quality_checker.check_quality(log)
        
        # 3. 元数据同步
        lineage_builder = LineageGraph()
        lineage_builder.build_lineage(task)
        
        # 4. 更新执行状态
        log.status = 'success'
        log.save()
        
        # 5. 触发后续任务（如果有依赖的下游任务）
        trigger_downstream_tasks(task)
        
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.save()
        
        # 失败重试
        if log.retry_count < task.retry_count:
            execute_integration_task.apply_async(
                (task_id,),
                countdown=300  # 5分钟后重试
            )
        else:
            # 通知告警
            send_alert(task, str(e))
        
        raise
```

---

## 十、安全与权限

### 9.1 数据安全
- **敏感字段脱敏**：在转换阶段自动脱敏
- **数据加密**：传输和存储加密
- **审计日志**：所有操作记录

### 9.2 权限控制
- **任务权限**：基于RBAC，区分查看/编辑/执行权限
- **数据源权限**：复用数据源管理的权限
- **高危操作审批**：删除任务、修改质量规则需审批

---

## 十、安全与权限

### 核心价值
✅ 统一的ETL平台，支持多种集成场景  
✅ 数据仓库原生架构，支持分层和分区  
✅ 完整的数据血缘，支持影响分析  
✅ 自动化质量检查，保证数据质量  
✅ 可视化配置，降低技术门槛  

### 演进方向
- **实时集成**：集成Canal/Flink CDC实现秒级同步
- **智能推荐**：基于元数据和血缘推荐最佳映射方案
- **自动化修复**：质量检查失败后自动触发修复流程
- **多云支持**：支持云数据仓库（Snowflake、BigQuery等）

