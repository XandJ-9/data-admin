# 数据任务运维模块设计方案

## 文档版本
- **版本号**：1.0
- **最后更新**：2026年1月
- **作者**：Data Admin Team
- **适用对象**：后端工程师、前端工程师、产品经理

---

## 一、模块概述

### 1.1 核心定位
数据任务运维模块是 Data Admin 平台的**运维中枢**，核心目标是保障数据任务全生命周期的**可用性、稳定性、效率与合规性**。通过**可视化监控、自动化处理、智能告警、闭环复盘**，帮助数据团队快速定位和解决数据问题。

### 1.2 设计理念
- **分层架构**：工作台（展示）→ 任务运维（核心）→ 资源监控（基础）→ 告警/审计（支撑）
- **闭环管理**：监控 → 告警 → 处理 → 复盘 → 改进
- **自动化优先**：尽可能减少人工干预，提升运维效率
- **实时可追溯**：所有运维操作、故障、指标数据可追溯、可审计

### 1.3 核心价值
| 角色 | 价值体现 |
|------|--------|
| 数据工程师 | 故障快速定位、一键修复、日志追溯 |
| 数据运维人员 | 自动化巡检、告警收敛、成本感知 |
| 数据管理员 | 权限审计、操作审计、SLA达标率 |
| 业务用户 | 数据可用性提升、服务级别承诺 |

---

## 二、功能架构设计

### 2.1 总体功能分层
```
┌─────────────────────────────────────────┐
│  运维工作台（驾驶舱）                    │  <- 全局视图：监控指标、关键指标、快捷操作
├─────────────────────────────────────────┤
│  数据任务运维（核心）                    │  <- 任务编排、执行、故障、版本管理
│  数据资源运维（支撑）                    │  <- 资源监控、资源管理、成本管理
├─────────────────────────────────────────┤
│  告警运维（告警、分级、处理）            │  <- 规则配置、告警分级、渠道管理
│  审计运维（操作审计、故障复盘）          │  <- 工单管理、RCA、权限审计
├─────────────────────────────────────────┤
│  自动化运维（脚本、巡检、修复）          │  <- 脚本管理、定时巡检、自动修复
└─────────────────────────────────────────┘
```

### 2.2 核心功能模块清单

#### 一级模块
1. **运维工作台**（可视化仪表盘）
2. **数据任务运维**（生命周期管理）
3. **告警管理**（规则、告警、处理）
4. **故障复盘**（工单、RCA、审计）

#### 二级模块（未来扩展）
- 数据资源运维（资源监控、扩缩容）
- 自动化运维（脚本、巡检、修复规则）
- 数据权限运维（权限审计、敏感数据监控）

---

## 三、核心模块详设

### 3.1 运维工作台（驾驶舱）

#### 3.1.1 功能概览
为运维人员提供全局视图，展示关键指标、故障告警、任务健康度，支持快捷操作。

#### 3.1.2 核心指标
```
┌─ 今日概览
│  ├─ 总任务数：N 个
│  ├─ 成功率：XX%
│  ├─ 失败数：N 个
│  ├─ 延迟数：N 个
│  └─ 告警数：N 个
├─ 任务健康度
│  ├─ TOP5 失败任务（失败原因）
│  ├─ TOP5 耗时任务（执行时间）
│  ├─ TOP5 高失败率任务（失败率）
│  └─ 近7天执行趋势（折线图：成功/失败/延迟）
├─ 资源概览（未来）
│  ├─ 存储使用率：XX%
│  ├─ 计算资源使用率：XX%
│  └─ 成本月度汇总：¥XXXX
└─ 待处理事项
   ├─ 未处理告警：N 条
   ├─ 未关闭工单：N 个
   └─ 需确认操作：N 项
```

#### 3.1.3 快捷操作栏
- **一键重试**：选中失败任务，一键重试
- **任务暂停/启动**：快速暂停/启动任务
- **查看日志**：跳转至任务日志详情
- **创建告警**：快速创建新告警规则
- **查看配置**：查看任务配置历史

#### 3.1.4 后端设计

**数据模型**（基于已有模型扩展）：
```python
# 已有：DataTask, TaskLog, AlertRule, AlertRecord
# 扩展字段：
class DataTask(BaseModel):
    # ... 现有字段 ...
    failure_reason = models.CharField(max_length=256, blank=True, verbose_name='失败原因')
    execution_duration = models.IntegerField(default=0, verbose_name='执行时长(秒)')
    last_success_time = models.DateTimeField(null=True, blank=True, verbose_name='上次成功时间')
    retry_count = models.IntegerField(default=0, verbose_name='重试次数')
```

**接口设计**：
```
GET /datataskmonitor/dashboard/
返回：
{
  "code": 200,
  "data": {
    "today": {
      "totalTasks": 42,
      "successRate": 95.2,
      "failureCount": 2,
      "delayCount": 1,
      "alertCount": 5
    },
    "topFailedTasks": [...],
    "topSlowTasks": [...],
    "trendData": [...],  // 7天趋势
    "pendingAlerts": N,
    "openWorkOrders": N
  }
}
```

#### 3.1.5 前端设计

**目录结构**：
```
frontend/src/views/data/taskmonitor/
├── index.vue                 # 工作台主页
├── dashboard/
│  ├── overview.vue          # 概览卡片组件
│  ├── metrics.vue           # 关键指标
│  ├── trendChart.vue        # 趋势图表
│  └── quickActions.vue      # 快捷操作
└── components/
   └── ...
```

**核心组件**：
- 仪表盘卡片（Overview Card）：展示关键指标，支持钻取
- 图表组件：折线图（趋势）、柱状图（对比）、饼图（占比）
- 快捷操作条：按钮组件，支持批量操作确认

---

### 3.2 数据任务运维

#### 3.2.1 功能概览
核心模块，覆盖任务的全生命周期管理：编排 → 配置 → 执行 → 监控 → 故障处理 → 版本管理。

#### 3.2.2 核心子功能

##### (1) 任务编排与配置

**功能描述**：
- 可视化 DAG 编排：拖拽创建任务依赖关系
- 任务配置：任务名、描述、调度方式、超时配置、重试策略
- 前置/后置任务：配置任务依赖关系

**数据模型**：
```python
class DataTask(BaseModel):
    # ... 现有字段 ...
    parent_tasks = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        related_name='child_tasks',
        verbose_name='前置任务'
    )
    timeout_seconds = models.IntegerField(default=3600, verbose_name='超时时间(秒)')
    retry_policy = models.JSONField(
        default=dict,  # {'max_retries': 3, 'retry_interval': 300}
        verbose_name='重试策略'
    )
    skip_on_failure = models.BooleanField(default=False, verbose_name='前置失败时跳过')
```

**接口设计**：
```
# 获取任务DAG
GET /datataskmonitor/tasks/{id}/dag/
返回：节点信息 + 边信息（依赖关系）

# 更新任务配置
PUT /datataskmonitor/tasks/{id}/
{"taskName": "...", "retryPolicy": {...}, "parentTasks": [1, 2]}

# 获取任务依赖树
GET /datataskmonitor/tasks/{id}/dependencies/
返回：上游依赖、下游依赖、影响范围
```

##### (2) 任务执行与日志

**功能描述**：
- 实时执行监控：任务状态、进度、资源占用
- 详细日志：系统日志、业务日志、错误日志
- 日志检索：关键字搜索、日期范围筛选
- 日志导出：支持多种格式导出（txt、csv、json）

**数据模型**（扩展）：
```python
class TaskLog(BaseModel):
    task = models.ForeignKey(DataTask, on_delete=models.CASCADE, verbose_name='关联任务')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='运行状态')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    message = models.TextField(blank=True, verbose_name='日志信息')
    # 扩展字段
    execution_duration = models.IntegerField(default=0, verbose_name='执行时长(秒)')
    data_processed = models.IntegerField(default=0, verbose_name='处理数据量')
    error_detail = models.TextField(blank=True, verbose_name='错误详情')
    log_level = models.CharField(
        max_length=10,
        choices=[('INFO', '信息'), ('WARN', '警告'), ('ERROR', '错误')],
        default='INFO',
        verbose_name='日志级别'
    )

class TaskLogDetail(BaseModel):
    """详细日志表"""
    task_log = models.ForeignKey(TaskLog, on_delete=models.CASCADE, related_name='details')
    log_type = models.CharField(
        max_length=20,
        choices=[('system', '系统'), ('business', '业务'), ('error', '错误')],
        verbose_name='日志类型'
    )
    log_content = models.TextField(verbose_name='日志内容')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='时间')
    
    class Meta:
        db_table = 'dt_task_log_detail'
        indexes = [models.Index(fields=['task_log', 'timestamp'])]
```

**接口设计**：
```
# 获取任务日志
GET /datataskmonitor/task-logs/?taskId=1&pageNum=1&pageSize=20
返回：日志列表 + 分页信息

# 获取日志详情
GET /datataskmonitor/task-logs/{logId}/details/
返回：系统日志、业务日志、错误日志

# 搜索日志
GET /datataskmonitor/task-logs/search/?keyword=error&startTime=...&endTime=...

# 导出日志
GET /datataskmonitor/task-logs/{logId}/export/?format=json
```

##### (3) 故障处理（重试、断点续跑）

**功能描述**：
- 失败任务一键重试（包括重新配置参数）
- 断点续跑：从失败节点恢复执行（涉及下游依赖管理）
- 任务重跑：支持选择重跑时间范围（全量/增量）
- 强制停止：停止运行中的任务

**数据模型**：
```python
class TaskExecution(BaseModel):
    """任务执行记录（支持重试追溯）"""
    task = models.ForeignKey(DataTask, on_delete=models.CASCADE, verbose_name='任务')
    execution_type = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', '定时执行'),
            ('manual', '手动执行'),
            ('retry', '重试执行'),
            ('resume', '断点续跑'),
            ('rerun', '任务重跑')
        ],
        verbose_name='执行类型'
    )
    trigger_by = models.CharField(max_length=64, verbose_name='触发者')
    retry_count = models.IntegerField(default=0, verbose_name='重试次数')
    original_log = models.ForeignKey(
        TaskLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_executions',
        verbose_name='原始日志'
    )
    # 断点续跑信息
    resume_from_node = models.CharField(max_length=128, blank=True, verbose_name='从节点恢复')
    resume_reason = models.CharField(max_length=256, blank=True, verbose_name='续跑原因')
```

**接口设计**：
```
# 重试失败任务
POST /datataskmonitor/tasks/{id}/retry/
{"retryCount": 3, "retryInterval": 300}

# 断点续跑
POST /datataskmonitor/tasks/{id}/resume/
{"resumeFromNode": "node_name", "reason": "..."}

# 任务重跑
POST /datataskmonitor/tasks/{id}/rerun/
{"rerunMode": "full", "startTime": "2026-01-01", "endTime": "2026-01-20"}

# 强制停止
POST /datataskmonitor/task-logs/{logId}/stop/
```

##### (4) 版本管理与配置对比

**功能描述**：
- 任务配置版本化：每次修改自动保存版本
- 版本回滚：快速回滚到历史版本
- 版本对比：对比两个版本的差异
- 变更记录：记录配置变更者、时间、原因

**数据模型**：
```python
class TaskConfigVersion(BaseModel):
    """任务配置版本"""
    task = models.ForeignKey(DataTask, on_delete=models.CASCADE, related_name='config_versions')
    version_number = models.IntegerField(verbose_name='版本号')
    config_json = models.JSONField(verbose_name='配置内容')
    change_reason = models.CharField(max_length=256, blank=True, verbose_name='变更原因')
    is_current = models.BooleanField(default=False, verbose_name='是否当前版本')
    
    class Meta:
        db_table = 'dt_task_config_version'
        unique_together = [['task', 'version_number']]
        indexes = [models.Index(fields=['task', 'is_current'])]
```

**接口设计**：
```
# 获取版本历史
GET /datataskmonitor/tasks/{id}/config-versions/

# 对比两个版本
GET /datataskmonitor/tasks/{id}/config-versions/compare/
?fromVersion=1&toVersion=2

# 回滚到历史版本
PUT /datataskmonitor/tasks/{id}/config-versions/{versionId}/rollback/
```

##### (5) 任务依赖关系与影响分析

**功能描述**：
- 展示任务上下游依赖关系（DAG 图）
- 影响分析：分析任务失败/延迟对下游任务的影响
- 依赖失败策略：配置下游任务是否阻止执行或跳过

**接口设计**：
```
# 获取依赖关系
GET /datataskmonitor/tasks/{id}/dependencies/
返回：
{
  "upstreamTasks": [
    {"id": 1, "taskName": "task1", "status": "success"}
  ],
  "downstreamTasks": [
    {"id": 2, "taskName": "task2", "failurePolicy": "block"}
  ]
}

# 影响分析
POST /datataskmonitor/tasks/{id}/impact-analysis/
{"failureTime": "2026-01-20 10:00:00"}
返回：受影响的下游任务列表 + 预计延迟时间
```

#### 3.2.3 后端架构

**模块结构**：
```
backend/apps/datataskmonitor/
├── models.py                 # 数据模型（含扩展字段）
├── serializers.py           # 序列化器
├── views/
│  ├── __init__.py
│  ├── task.py              # 任务管理（列表、详情、创建、编辑）
│  ├── execution.py         # 任务执行（日志、重试、续跑）
│  ├── version.py           # 版本管理
│  ├── dependency.py        # 依赖管理
│  └── dashboard.py         # 工作台接口
├── urls.py
├── taskmanager/
│  ├── __init__.py
│  ├── executor.py          # 任务执行器（调度、执行、日志记录）
│  ├── scheduler.py         # 调度管理器（Celery 集成）
│  └── utils.py             # 工具函数
└── migrations/
```

**关键类设计**：

```python
# models.py
from apps.system.models import BaseModel

class DataTask(BaseModel):
    """数据任务模型（扩展）"""
    TASK_TYPES = [
        ('collection', '数据采集'),
        ('sync', '数据同步'),
        ('calculation', '数据计算'),
    ]
    
    task_name = models.CharField(max_length=128)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    schedule_type = models.CharField(max_length=20)  # cron/interval/once
    schedule_conf = models.CharField(max_length=256)
    enabled = models.CharField(max_length=1, default='0')
    status = models.CharField(max_length=20)
    
    # 扩展字段
    timeout_seconds = models.IntegerField(default=3600)
    retry_policy = models.JSONField(default=dict)
    skip_on_failure = models.BooleanField(default=False)
    execution_duration = models.IntegerField(default=0)
    failure_reason = models.CharField(max_length=256, blank=True)
    
    # 依赖关系
    parent_tasks = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        related_name='child_tasks'
    )


class TaskLog(BaseModel):
    """任务日志（扩展）"""
    task = models.ForeignKey(DataTask, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    
    # 扩展字段
    execution_duration = models.IntegerField(default=0)
    data_processed = models.IntegerField(default=0)
    error_detail = models.TextField(blank=True)
    log_level = models.CharField(max_length=10, default='INFO')


# views/task.py
class DataTaskViewSet(BaseViewSet):
    """任务管理视图"""
    queryset = DataTask.objects.all()
    serializer_class = DataTaskSerializer
    
    def list(self, request, *args, **kwargs):
        """列出任务（支持筛选、排序、分页）"""
        ...
    
    def retrieve(self, request, *args, **kwargs):
        """获取任务详情"""
        ...
    
    @action(detail=True, methods=['get'])
    def dag(self, request, pk=None):
        """获取任务DAG信息"""
        ...
    
    @action(detail=True, methods=['get'])
    def dependencies(self, request, pk=None):
        """获取任务依赖关系"""
        ...


# views/execution.py
class TaskExecutionViewSet(BaseViewSet):
    """任务执行管理视图"""
    
    @action(detail=False, methods=['post'])
    def retry(self, request):
        """重试失败任务"""
        task_id = request.data.get('task_id')
        retry_count = request.data.get('retry_count', 1)
        # 调用 TaskExecutor 重试
        ...
    
    @action(detail=False, methods=['post'])
    def resume(self, request):
        """断点续跑"""
        ...
    
    @action(detail=False, methods=['post'])
    def stop(self, request):
        """停止运行任务"""
        ...


# taskmanager/executor.py
class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, task_id):
        self.task = DataTask.objects.get(id=task_id)
        self.logger = ...
    
    def execute(self):
        """执行任务"""
        log = TaskLog.objects.create(task=self.task, status='running')
        try:
            # 1. 检查前置任务状态
            # 2. 执行任务逻辑
            # 3. 记录日志、更新状态
            log.status = 'success'
            log.save()
        except Exception as e:
            log.status = 'failed'
            log.error_detail = str(e)
            log.save()
            raise
    
    def retry(self, retry_count=1):
        """重试任务"""
        ...
    
    def resume(self, resume_from_node):
        """断点续跑"""
        ...
```

---

### 3.3 告警管理

#### 3.3.1 功能概览
全面的告警系统：规则配置 → 告警生成 → 收敛过滤 → 渠道分发 → 告警处理。

#### 3.3.2 核心功能

##### (1) 告警规则配置

**功能描述**：
- 预设告警模板：常用告警场景（任务失败、超时、延迟）
- 自定义规则：支持多条件组合（如"CPU>90% AND 持续>10分钟"）
- 规则模板管理：保存、复用、编辑规则模板
- 规则分级：按严重程度分级（P0/P1/P2/P3）
- 规则启用/禁用：灵活管理规则生效时间

**数据模型**（扩展）：
```python
class AlertRule(BaseModel):
    """告警规则"""
    RULE_TYPES = [
        ('task_failure', '任务失败'),
        ('task_timeout', '任务超时'),
        ('task_delay', '数据延迟'),
        ('resource_exceed', '资源超限'),
    ]
    
    SEVERITY_LEVELS = [
        ('P0', '紧急 - 核心任务故障'),
        ('P1', '重要 - 资源超限'),
        ('P2', '一般 - 数据延迟'),
        ('P3', '提示 - 低使用率'),
    ]
    
    rule_name = models.CharField(max_length=128)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # 规则条件（JSON）
    conditions = models.JSONField(default=dict)  # {'field': 'task_status', 'operator': '==', 'value': 'failed'}
    
    # 通知配置
    notification_channels = models.CharField(max_length=256)  # email,dingtalk,wechat
    receivers = models.TextField()  # 逗号分隔
    
    # 规则生效时间
    enabled = models.BooleanField(default=True)
    silence_period = models.JSONField(
        default=dict,  # {'start': '00:00', 'end': '08:00'} - 静默时间
        verbose_name='静默期'
    )
    
    # 规则模板
    is_template = models.BooleanField(default=False, verbose_name='是否模板')
    template_category = models.CharField(max_length=64, blank=True, verbose_name='模板分类')


class AlertTemplate(BaseModel):
    """告警规则模板"""
    template_name = models.CharField(max_length=128, verbose_name='模板名称')
    template_category = models.CharField(max_length=64, verbose_name='分类')
    rule_type = models.CharField(max_length=30, verbose_name='规则类型')
    conditions = models.JSONField(verbose_name='规则条件')
    default_severity = models.CharField(max_length=10, verbose_name='默认级别')
    default_channels = models.CharField(max_length=256, verbose_name='默认渠道')
    description = models.TextField(blank=True, verbose_name='描述')
    
    class Meta:
        db_table = 'dt_alert_template'
```

**接口设计**：
```
# 获取告警规则列表
GET /datataskmonitor/alert-rules/?severity=P0&enabled=true

# 创建告警规则
POST /datataskmonitor/alert-rules/
{
  "ruleName": "核心任务失败告警",
  "ruleType": "task_failure",
  "severity": "P0",
  "conditions": {"taskId": [1, 2, 3]},
  "notificationChannels": ["email", "dingtalk"],
  "receivers": "admin@example.com,user@example.com"
}

# 获取告警模板
GET /datataskmonitor/alert-templates/?category=task_failure

# 从模板创建规则
POST /datataskmonitor/alert-rules/from-template/
{"templateId": 1, "customConfig": {...}}
```

##### (2) 告警分级与分发

**功能描述**：
- 四级告警系统：P0（紧急）→ P1（重要）→ P2（一般）→ P3（提示）
- 按级别配置渠道：P0 同时推送钉钉+短信+电话，P3 仅发邮件
- 告警升级：未处理 P1 告警 30 分钟自动升级为 P0

**数据模型**：
```python
class AlertRecord(BaseModel):
    """告警记录"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('acknowledged', '已确认'),
        ('resolved', '已解决'),
        ('ignored', '已忽略'),
    ]
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=30)  # task_failure, timeout 等
    severity = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='pending')
    
    # 触发信息
    trigger_time = models.DateTimeField(auto_now_add=True)
    trigger_entity = models.CharField(max_length=128)  # 触发实体（任务ID等）
    alert_message = models.TextField()  # 告警信息
    
    # 处理信息
    handler = models.CharField(max_length=64, blank=True)  # 处理人
    handle_time = models.DateTimeField(null=True, blank=True)
    handle_remark = models.TextField(blank=True)  # 处理备注
    
    # 升级信息
    escalated = models.BooleanField(default=False)  # 是否已升级
    escalation_time = models.DateTimeField(null=True, blank=True)
    original_severity = models.CharField(max_length=10, blank=True)


class AlertChannelConfig(BaseModel):
    """告警渠道配置"""
    CHANNELS = [
        ('email', '邮件'),
        ('dingtalk', '钉钉'),
        ('wechat', '企业微信'),
        ('sms', '短信'),
        ('phone', '电话'),
    ]
    
    channel = models.CharField(max_length=30, choices=CHANNELS)
    severity = models.CharField(max_length=10)  # P0-P3
    enabled = models.BooleanField(default=True)
    
    # 渠道配置（JSON）
    channel_config = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'dt_alert_channel_config'
        unique_together = [['channel', 'severity']]
```

**接口设计**：
```
# 获取告警记录
GET /datataskmonitor/alert-records/?severity=P0&status=pending

# 处理告警
PUT /datataskmonitor/alert-records/{id}/handle/
{"handler": "admin", "remark": "已处理"}

# 忽略告警
PUT /datataskmonitor/alert-records/{id}/ignore/
{"reason": "误报"}

# 获取渠道配置
GET /datataskmonitor/alert-channels/config/

# 更新渠道配置
PUT /datataskmonitor/alert-channels/config/
{"channels": [{"channel": "email", "severity": "P0", "enabled": true}]}
```

##### (3) 告警收敛与静默

**功能描述**：
- 重复告警合并：同一任务 5 分钟内多次失败仅推送 1 次
- 静默期配置：配置不推送告警的时间段（如每日 00:00-08:00 不推送 P3）
- 告警幂等：相同的告警不重复发送
- 告警聚合：相似告警自动分组

**实现方式**：
```python
class AlertDeduplicator:
    """告警去重器"""
    
    def should_alert(self, rule_id, trigger_entity):
        """判断是否应该发送告警"""
        # 1. 检查是否在静默期内
        # 2. 检查最近一小时内是否已发送相同告警
        # 3. 返回是否应该发送
        ...
    
    def aggregate_alerts(self, alerts):
        """告警聚合"""
        # 将相似告警分组，减少告警数量
        ...
```

---

### 3.4 故障复盘与审计

#### 3.4.1 功能概览
闭环故障管理：故障自动生成工单 → 根因分析 → 解决方案 → 预防措施 → 审计记录。

#### 3.4.2 核心功能

##### (1) 故障工单管理

**功能描述**：
- 故障自动生成工单：任务失败/告警升级自动创建工单
- 工单流程：新建 → 认领 → 处理 → 复盘 → 关闭
- 工单追踪：显示工单状态、处理人、处理进度
- 未结工单告警：工单超期未关闭自动提醒

**数据模型**：
```python
class FaultWorkOrder(BaseModel):
    """故障工单"""
    STATUS_CHOICES = [
        ('new', '新建'),
        ('assigned', '已认领'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
        ('closed', '已关闭'),
    ]
    
    fault_type = models.CharField(max_length=30)  # task_failure, timeout 等
    fault_entity = models.CharField(max_length=128)  # 故障实体（任务ID等）
    alert_record = models.OneToOneField(
        AlertRecord,
        on_delete=models.SET_NULL,
        null=True,
        related_name='work_order'
    )
    
    # 工单信息
    fault_time = models.DateTimeField(verbose_name='故障时间')
    fault_description = models.TextField(verbose_name='故障描述')
    impact_scope = models.TextField(verbose_name='影响范围')
    
    # 流程信息
    status = models.CharField(max_length=20, default='new')
    assigned_to = models.CharField(max_length=64, blank=True, verbose_name='认领人')
    assigned_time = models.DateTimeField(null=True, blank=True)
    resolved_time = models.DateTimeField(null=True, blank=True)
    closed_time = models.DateTimeField(null=True, blank=True)
    
    # SLA
    sla_deadline = models.DateTimeField(verbose_name='SLA截止时间')
    is_sla_breached = models.BooleanField(default=False, verbose_name='是否超期')


class FaultRCA(BaseModel):
    """根因分析"""
    RCA_METHODS = [
        ('5why', '5Why分析'),
        ('fishbone', '鱼骨图'),
        ('timeline', '时间线分析'),
    ]
    
    work_order = models.OneToOneField(FaultWorkOrder, on_delete=models.CASCADE, related_name='rca')
    
    rca_method = models.CharField(max_length=30, choices=RCA_METHODS)
    root_cause = models.TextField(verbose_name='根本原因')
    direct_cause = models.TextField(blank=True, verbose_name='直接原因')
    
    # 解决方案
    solution = models.TextField(verbose_name='解决方案')
    solution_status = models.CharField(
        max_length=20,
        choices=[('pending', '待实施'), ('implemented', '已实施'), ('verified', '已验证')],
        default='pending'
    )
    
    # 预防措施
    prevention_measures = models.TextField(verbose_name='预防措施')
    responsible_person = models.CharField(max_length=64, verbose_name='责任人')
    completion_deadline = models.DateField(verbose_name='完成期限')
    
    class Meta:
        db_table = 'dt_fault_rca'
```

**接口设计**：
```
# 获取工单列表
GET /datataskmonitor/work-orders/?status=processing&severity=P0

# 认领工单
PUT /datataskmonitor/work-orders/{id}/assign/
{"assignedTo": "user_id"}

# 更新工单状态
PUT /datataskmonitor/work-orders/{id}/
{"status": "processing", "remark": "..."}

# 创建根因分析
POST /datataskmonitor/work-orders/{id}/rca/
{
  "rcaMethod": "5why",
  "rootCause": "数据库连接超时",
  "solution": "增加连接池大小",
  "preventionMeasures": "定期巡检连接状态"
}

# 关闭工单
PUT /datataskmonitor/work-orders/{id}/close/
{"remark": "已解决"}
```

##### (2) 运维操作审计

**功能描述**：
- 全面的审计日志：记录所有运维操作（重试、停止、修改配置、修改告警规则等）
- 审计信息：操作人、操作时间、操作内容、IP 地址、操作结果
- 审计日志不可篡改：日志存入只读表，禁用 delete/update
- 审计日志查询：支持按操作人、时间、模块、操作类型查询

**数据模型**：
```python
class AuditLog(BaseModel):
    """运维操作审计日志"""
    OPERATION_TYPES = [
        ('task_create', '任务创建'),
        ('task_update', '任务修改'),
        ('task_delete', '任务删除'),
        ('task_execute', '任务执行'),
        ('task_retry', '任务重试'),
        ('task_stop', '任务停止'),
        ('rule_create', '规则创建'),
        ('rule_update', '规则修改'),
        ('rule_delete', '规则删除'),
    ]
    
    operator = models.CharField(max_length=64)  # 操作人
    operation_type = models.CharField(max_length=30, choices=OPERATION_TYPES)
    module = models.CharField(max_length=64)  # 所属模块
    entity_type = models.CharField(max_length=64)  # 实体类型（Task、AlertRule 等）
    entity_id = models.IntegerField()  # 实体ID
    
    # 操作内容
    action = models.CharField(max_length=256)  # 操作描述
    changes = models.JSONField(default=dict, verbose_name='字段变更')  # {'field': {'old': '', 'new': ''}}
    
    # 执行信息
    status = models.CharField(
        max_length=20,
        choices=[('success', '成功'), ('failed', '失败')],
        default='success'
    )
    error_message = models.TextField(blank=True)
    ip_address = models.CharField(max_length=64)
    user_agent = models.CharField(max_length=256, blank=True)
    
    # 不可修改配置
    class Meta:
        db_table = 'dt_audit_log'
        indexes = [
            models.Index(fields=['operator', 'operation_type', 'create_time']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]
    
    def delete(self, *args, **kwargs):
        """禁用删除操作"""
        raise PermissionError("审计日志不可删除")
    
    def save(self, *args, **kwargs):
        """禁用更新操作（除非是新建）"""
        if self.pk is not None:
            raise PermissionError("审计日志不可修改")
        super().save(*args, **kwargs)


@audit_log(module='datataskmonitor', entity_type='DataTask')
def create_task(request, ...):
    """创建任务（自动记录审计日志）"""
    ...
```

**装饰器设计**：
```python
def audit_log(module, entity_type):
    """审计日志装饰器"""
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            # 记录操作前的状态
            old_data = ...
            
            # 执行操作
            response = func(self, request, *args, **kwargs)
            
            # 记录操作后的状态
            new_data = ...
            
            # 创建审计日志
            AuditLog.objects.create(
                operator=request.user.username,
                operation_type=f'{entity_type.lower()}_{func.__name__}',
                module=module,
                entity_type=entity_type,
                entity_id=...,
                changes={...},
                status='success' if response.status_code < 400 else 'failed',
                ip_address=get_client_ip(request),
            )
            
            return response
        return wrapper
    return decorator
```

---

### 3.5 自动化运维（未来模块）

#### 3.5.1 功能规划
- **脚本管理**：低代码编写运维脚本
- **定时巡检**：定期检查数据源连接、任务配置
- **自动修复**：预设修复规则，自动处理常见故障
- **运维流水线**：编排多步运维操作

#### 3.5.2 数据模型预设
```python
class AutomationScript(BaseModel):
    """自动化脚本"""
    script_name = models.CharField(max_length=128)
    script_type = models.CharField(max_length=30)  # inspection, repair, deployment
    script_content = models.TextField()  # Python/Shell 代码
    execute_method = models.CharField(max_length=30)  # celery, subprocess
    execute_timeout = models.IntegerField(default=3600)  # 执行超时
    
    is_template = models.BooleanField(default=False)
    required_approvals = models.IntegerField(default=0)  # 高危脚本需审批


class AutomationRule(BaseModel):
    """自动修复规则"""
    trigger_condition = models.JSONField()  # 触发条件
    action_script = models.ForeignKey(AutomationScript, on_delete=models.CASCADE)
    max_retry_count = models.IntegerField(default=3)
    enabled = models.BooleanField(default=True)
```

---

## 四、前端架构设计

### 4.1 目录结构规划
```
frontend/src/views/datataskmonitor/
├── index.vue                          # 主入口页面
├── dashboard/
│  ├── index.vue                      # 工作台
│  ├── overview.vue                   # 概览卡片
│  ├── metrics.vue                    # 关键指标
│  └── trendChart.vue                 # 趋势图表
├── task/
│  ├── index.vue                      # 任务列表
│  ├── detail/
│  │  ├── index.vue                  # 任务详情
│  │  ├── dag.vue                    # DAG 图
│  │  ├── logs.vue                   # 执行日志
│  │  ├── version.vue                # 版本管理
│  │  └── dependency.vue             # 依赖关系
│  ├── config.vue                     # 任务配置
│  └── form.vue                       # 任务表单
├── execution/
│  ├── index.vue                      # 执行历史
│  ├── logs.vue                       # 详细日志
│  └── logDetail.vue                  # 日志详情
├── alert/
│  ├── index.vue                      # 告警列表
│  ├── rules.vue                      # 告警规则
│  ├── templates.vue                  # 告警模板
│  ├── ruleForm.vue                   # 规则配置
│  └── handling.vue                   # 告警处理
├── fault/
│  ├── index.vue                      # 故障工单
│  ├── rca.vue                        # 根因分析
│  └── audit.vue                      # 审计日志
└── components/
   ├── TaskDAG.vue                     # DAG 编辑组件
   ├── LogViewer.vue                   # 日志查看器
   ├── AlertRuleBuilder.vue            # 告警规则构造器
   └── DependencyGraph.vue             # 依赖关系图
```

### 4.2 核心路由配置
```javascript
// frontend/src/router/index.js
{
  path: '/datataskmonitor',
  component: Layout,
  meta: { title: '数据任务运维' },
  children: [
    {
      path: 'dashboard',
      component: () => import('@/views/datataskmonitor/dashboard/index.vue'),
      meta: { title: '运维工作台' }
    },
    {
      path: 'task',
      component: () => import('@/views/datataskmonitor/task/index.vue'),
      meta: { title: '任务管理' }
    },
    {
      path: 'task/:id',
      component: () => import('@/views/datataskmonitor/task/detail/index.vue'),
      meta: { title: '任务详情' }
    },
    {
      path: 'alert',
      component: () => import('@/views/datataskmonitor/alert/index.vue'),
      meta: { title: '告警管理' }
    },
    {
      path: 'fault',
      component: () => import('@/views/datataskmonitor/fault/index.vue'),
      meta: { title: '故障工单' }
    },
    {
      path: 'audit',
      component: () => import('@/views/datataskmonitor/fault/audit.vue'),
      meta: { title: '运维审计' }
    }
  ]
}
```

### 4.3 关键组件设计

#### (1) TaskDAG 组件（任务依赖关系 DAG）
```vue
<template>
  <div class="task-dag-container">
    <div class="toolbar">
      <el-button type="primary" @click="addNode">添加节点</el-button>
      <el-button @click="deleteNode">删除节点</el-button>
      <el-button @click="exportDAG">导出</el-button>
      <el-button @click="importDAG">导入</el-button>
    </div>
    <div id="dag-canvas" class="dag-canvas"></div>
  </div>
</template>

<script>
// 使用 G6（图编辑引擎）展示 DAG
// 支持拖拽、添加边、删除节点等操作
</script>
```

#### (2) LogViewer 组件（日志查看器）
```vue
<template>
  <div class="log-viewer">
    <div class="toolbar">
      <el-input v-model="searchKeyword" placeholder="搜索日志..." />
      <el-select v-model="logLevel" placeholder="日志级别">
        <el-option label="全部" value="" />
        <el-option label="INFO" value="INFO" />
        <el-option label="WARN" value="WARN" />
        <el-option label="ERROR" value="ERROR" />
      </el-select>
      <el-button @click="exportLogs">导出</el-button>
      <el-button @click="clearLogs">清空</el-button>
    </div>
    <div class="log-container">
      <div v-for="log in filteredLogs" :key="log.id" :class="['log-line', `log-${log.level}`]">
        <span class="log-time">{{ log.timestamp }}</span>
        <span class="log-level">{{ log.level }}</span>
        <span class="log-content">{{ log.message }}</span>
      </div>
    </div>
  </div>
</template>

<script>
// 支持实时日志流、搜索、过滤、导出
// 支持暗色主题
</script>
```

#### (3) AlertRuleBuilder 组件（告警规则构造器）
```vue
<template>
  <div class="alert-rule-builder">
    <el-form :model="rule" label-width="120px">
      <el-form-item label="规则名称">
        <el-input v-model="rule.ruleName" />
      </el-form-item>
      <el-form-item label="规则类型">
        <el-select v-model="rule.ruleType">
          <el-option label="任务失败" value="task_failure" />
          <el-option label="任务超时" value="task_timeout" />
          <el-option label="数据延迟" value="task_delay" />
        </el-select>
      </el-form-item>
      <el-form-item label="严重程度">
        <el-select v-model="rule.severity">
          <el-option label="P0 - 紧急" value="P0" />
          <el-option label="P1 - 重要" value="P1" />
          <el-option label="P2 - 一般" value="P2" />
          <el-option label="P3 - 提示" value="P3" />
        </el-select>
      </el-form-item>
      <el-form-item label="条件">
        <!-- 条件构造器：支持多条件组合 -->
        <el-button @click="addCondition">添加条件</el-button>
      </el-form-item>
      <el-form-item label="通知渠道">
        <el-checkbox-group v-model="rule.channels">
          <el-checkbox label="email">邮件</el-checkbox>
          <el-checkbox label="dingtalk">钉钉</el-checkbox>
          <el-checkbox label="wechat">企业微信</el-checkbox>
          <el-checkbox label="sms">短信</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>
  </div>
</template>
```

---

## 五、开发实施路线图

### 5.1 分阶段实现计划

**第一阶段（核心基础）**：2-3 周
- [ ] 数据模型定义 + 迁移
- [ ] 任务列表、详情、日志接口开发
- [ ] 告警规则、告警记录接口开发
- [ ] 基础前端页面（列表、表单）

**第二阶段（任务运维）**：2-3 周
- [ ] 任务执行器（TaskExecutor）完善
- [ ] 重试、续跑、停止接口
- [ ] 版本管理接口
- [ ] DAG 编辑、依赖关系查询

**第三阶段（告警与复盘）**：2-3 周
- [ ] 告警渠道集成（邮件、钉钉、企业微信）
- [ ] 告警收敛、升级逻辑
- [ ] 故障工单、根因分析功能
- [ ] 审计日志记录

**第四阶段（工作台与优化）**：1-2 周
- [ ] 运维工作台开发
- [ ] 关键指标聚合 + 图表
- [ ] 性能优化、缓存策略
- [ ] 全面测试、文档编写

### 5.2 关键技术点

| 技术点 | 说明 | 建议方案 |
|------|------|--------|
| 任务调度 | 定时/重复执行任务 | Celery Beat（已有基础） |
| 实时日志 | 任务执行的实时日志输出 | WebSocket + Redis 队列 |
| DAG 图编辑 | 可视化任务依赖关系 | 使用 G6 或 X6 图编辑库 |
| 告警分发 | 多渠道告警通知 | 使用第三方 SDK（钉钉、企业微信 API） |
| 权限控制 | 细粒度的操作权限 | 扩展现有 `HasRolePermission` |
| 审计日志 | 不可篡改的操作审计 | 数据库只读表 + Django 信号机制 |

---

## 六、与现有模块的整合

### 6.1 与数据源管理的关系
```
DataSource（数据源）
    ↓
    用于获取数据库信息
    ↑
DataTask（数据任务运维）
    - 任务类型：数据采集、同步等
    - 与数据源关联
```

### 6.2 与数据开发（DataStudio）的关系
```
DataStudioTask（开发任务）
    ↓
    转换为/监控为
    ↑
DataTask（运维任务）
    - source_task 字段关联
    - 禁止在运维模块创建任务
    - 任务配置从开发模块继承
```

### 6.3 与系统管理模块的关系
```
系统管理（User、Role、Permission）
    ↓
    权限控制、审计日志
    ↑
运维模块
    - 基于 RBAC 控制操作权限
    - 审计日志与系统日志表集成
```

---

## 七、数据库设计规范

### 7.1 表设计原则
- **继承 BaseModel**：所有模型继承 `BaseModel`，自动包含审计字段（create_by、update_by 等）
- **db_table 显式定义**：每个模型必须定义 `Meta.db_table`
- **索引优化**：为经常查询的字段添加索引
- **软删除**：通过 `del_flag` 字段实现软删除

### 7.2 关键表清单
```
dt_task                      # 数据任务
dt_task_log                  # 任务执行日志
dt_task_log_detail           # 任务详细日志
dt_task_execution            # 任务执行记录（支持重试追溯）
dt_task_config_version       # 任务配置版本
dt_alert_rule                # 告警规则
dt_alert_template            # 告警模板
dt_alert_record              # 告警记录
dt_alert_channel_config      # 告警渠道配置
dt_fault_work_order          # 故障工单
dt_fault_rca                 # 根因分析
dt_audit_log                 # 审计日志（只读）
```

---

## 八、API 接口清单

### 8.1 任务管理接口
```
GET    /datataskmonitor/tasks/                    # 列表
GET    /datataskmonitor/tasks/{id}/               # 详情
POST   /datataskmonitor/tasks/                    # 创建（禁用）
PUT    /datataskmonitor/tasks/{id}/               # 更新
DELETE /datataskmonitor/tasks/{id}/               # 删除
GET    /datataskmonitor/tasks/{id}/dag/           # 获取 DAG
GET    /datataskmonitor/tasks/{id}/dependencies/  # 获取依赖关系
POST   /datataskmonitor/tasks/{id}/retry/         # 重试
POST   /datataskmonitor/tasks/{id}/resume/        # 续跑
POST   /datataskmonitor/task-logs/{id}/stop/      # 停止
```

### 8.2 告警管理接口
```
GET    /datataskmonitor/alert-rules/              # 规则列表
POST   /datataskmonitor/alert-rules/              # 创建规则
PUT    /datataskmonitor/alert-rules/{id}/         # 更新规则
DELETE /datataskmonitor/alert-rules/{id}/         # 删除规则
GET    /datataskmonitor/alert-templates/          # 规则模板
GET    /datataskmonitor/alert-records/            # 告警记录
PUT    /datataskmonitor/alert-records/{id}/handle/  # 处理告警
```

### 8.3 故障工单接口
```
GET    /datataskmonitor/work-orders/              # 工单列表
GET    /datataskmonitor/work-orders/{id}/         # 工单详情
PUT    /datataskmonitor/work-orders/{id}/assign/  # 认领
PUT    /datataskmonitor/work-orders/{id}/         # 更新
POST   /datataskmonitor/work-orders/{id}/rca/     # 创建 RCA
GET    /datataskmonitor/audit-logs/               # 审计日志
```

### 8.4 工作台接口
```
GET    /datataskmonitor/dashboard/                # 工作台指标
```

---

## 九、开发规范与最佳实践

### 9.1 后端规范
- **模型继承**：所有模型继承 `BaseModel`
- **序列化器**：继承 `BaseModelSerializer`，自动支持驼峰转换
- **视图类**：继承 `BaseViewSet`，统一响应格式
- **异常处理**：使用 DRF 异常，由 `custom_exception_handler` 统一处理
- **审计日志**：使用 `@audit_log` 装饰器自动记录操作
- **权限控制**：使用 `HasRolePermission` 进行角色权限检查

### 9.2 前端规范
- **API 封装**：在 `src/api/` 目录下创建模块 API 文件
- **组件化**：可复用的组件放置在 `components/` 目录
- **路由配置**：遵循模块化路由结构
- **状态管理**：使用 Pinia（或 Vuex）管理全局状态
- **错误处理**：统一处理 API 错误，显示用户友好的错误信息

### 9.3 文档规范
- **API 文档**：使用 Swagger/OpenAPI 规范
- **数据字典**：维护数据字段说明和字典值映射
- **配置说明**：记录关键配置参数的用途和默响值

---

## 十、后续扩展方向

### 10.1 短期扩展（1-2 个月）
1. **数据资源运维**：资源监控、扩缩容、成本管理
2. **自动化运维**：脚本管理、定时巡检、自动修复
3. **高级告警**：机器学习异常检测、智能告警建议

### 10.2 中期扩展（2-3 个月）
1. **SLA 管理**：定义 SLA、SLA 达标率计算
2. **容量规划**：资源使用趋势、扩容预警
3. **多租户隔离**：基于租户的数据隔离和权限控制

### 10.3 长期演进（3-6 个月）
1. **AI 运维助手**：利用 LLM 自动诊断、建议解决方案
2. **数据治理集成**：与数据质量、血缘等模块深度融合
3. **行业标准对接**：支持与 Airflow、DolphinScheduler 等开源调度系统集成

---

## 十一、关键配置与参数

### 11.1 系统配置（settings.py）
```python
# 告警配置
ALERT_CONFIG = {
    'SILENCE_PERIOD': {
        'start_hour': 0,
        'end_hour': 8,  # 00:00-08:00 不发送 P3 告警
    },
    'ALERT_DEDUP_WINDOW': 300,  # 5 分钟内重复告警合并
    'ESCALATION_THRESHOLD': 1800,  # P1 告警 30 分钟未处理升级为 P0
}

# 任务执行配置
TASK_CONFIG = {
    'DEFAULT_TIMEOUT': 3600,  # 默认超时时间（秒）
    'DEFAULT_RETRY_COUNT': 3,
    'DEFAULT_RETRY_INTERVAL': 300,  # 重试间隔（秒）
    'CELERY_BEAT_ENABLED': True,
}

# 审计日志配置
AUDIT_CONFIG = {
    'RETENTION_DAYS': 365,  # 审计日志保留期（天）
    'INCLUDE_OPERATIONS': ['task_retry', 'task_stop', 'rule_update'],
}
```

### 11.2 告警渠道配置
```python
# 邮件告警
EMAIL_ALERT = {
    'SMTP_HOST': 'smtp.example.com',
    'SMTP_PORT': 587,
    'FROM_ADDRESS': 'ops@example.com',
}

# 钉钉告警
DINGTALK_ALERT = {
    'WEBHOOK_URL': 'https://oapi.dingtalk.com/robot/send',
    'SECRET': 'xxx',
}

# 企业微信告警
WECHAT_ALERT = {
    'CORP_ID': 'xxx',
    'CORP_SECRET': 'xxx',
}
```

---

## 十二、总结

### 核心亮点
1. **全面的监控体系**：从工作台、任务运维、告警管理到故障复盘的完整闭环
2. **灵活的扩展机制**：模块化设计，支持平滑扩展和集成
3. **自动化与智能化**：告警收敛、自动修复、智能诊断
4. **合规与可审计**：完整的审计日志、不可篡改机制
5. **用户友好**：基于 Ruoyi UI，提供一致的使用体验

### 成功关键因素
- 团队共识：确保产品、开发、运维团队理解设计理念
- 渐进式实现：按优先级逐步实现，快速交付核心价值
- 反馈迭代：基于实际使用情况持续优化
- 文档完善：维护清晰的开发文档和用户手册

