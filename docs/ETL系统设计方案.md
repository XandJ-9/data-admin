# 数据ETL系统设计方案

> **版本**: v1.0
> **日期**: 2026-03-16
> **状态**: 设计阶段

---

## 📋 目录

- [一、项目背景](#一项目背景)
- [二、系统架构设计](#二系统架构设计)
- [三、数据模型设计](#三数据模型设计)
- [四、执行任务层设计](#四执行任务层设计)
- [五、调度编排层设计](#五调度编排层设计)
- [六、实时监控设计](#六实时监控设计)
- [七、API接口设计](#七api接口设计)
- [八、实施计划](#八实施计划)
- [九、技术栈和依赖](#九技术栈和依赖)
- [十、测试和验证](#十测试和验证)
- [十一、部署和运维](#十一部署和运维)
- [十二、总结](#十二总结)

---

## 一、项目背景

### 1.1 现有痛点

当前ETL系统存在以下核心问题：

| 痛点 | 影响 | 严重程度 |
|------|------|----------|
| ❌ **任务经常失败需要手动重试** | 运维成本高，数据时效性差 | 🔴 高 |
| ❌ **无法监控任务执行进度** | 执行黑盒，问题排查困难 | 🔴 高 |
| ❌ **调度不够灵活** | 无法处理复杂依赖关系 | 🟡 中 |
| ❌ **缺乏断点续传能力** | 大数据量任务失败后需要重新开始 | 🟡 中 |

### 1.2 核心目标

按照三层架构设计全新的ETL系统：

```
┌────────────────────────────────────────┐
│         1. 定义任务层                    │
│  简化配置 | 模板化 | 版本管理            │
└────────────────────────────────────────┘
                ↓
┌────────────────────────────────────────┐
│         2. 执行任务层                    │
│  可靠执行 | 断点续传 | 实时监控          │
└────────────────────────────────────────┘
                ↓
┌────────────────────────────────────────┐
│         3. 调度编排层                    │
│  灵活调度 | 自动重试 | 依赖管理          │
└────────────────────────────────────────┘
```

### 1.3 设计原则

#### 🎯 简单性优先
- 避免过度抽象
- 直接解决问题
- 易于理解和维护

#### 🛡️ 可靠性第一
- 所有关键操作有日志
- 失败自动重试
- 状态可恢复

#### 👁️ 可观测性
- 实时进度推送
- 详细的执行日志
- 性能指标收集

### 1.4 实施约束

- ⏱️ **时间**: 1-2个月（快速迭代）
- 🎯 **优先级**: 断点续传 > 实时监控 > 灵活调度
- 🏗️ **方式**: 从零设计全新系统

---

## 二、系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                   API Layer (Django REST)                    │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 任务管理  │  │ 执行控制  │  │ 监控API   │  │ 调度API   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ TaskService  │  │ ExecutionSvc │  │ RetryService │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ MonitorSvc   │  │ ScheduleSvc  │  │ DependencySvc│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────┬──────────────────┬───────────────────┐
│   Task Definitions   │   Execution      │    Scheduling     │
│   (Database)         │   (Workers)      │    (Scheduler)    │
│                      │                  │                   │
│  - Task Config       │  - Task Workers  │  - Cron Parser    │
│  - Field Mapping     │  - Progress Rep. │  - Dependency Chk │
│  - Dependencies      │  - Checkpointing │  - Queue Mgmt     │
└──────────────────────┴──────────────────┴───────────────────┘
```

### 2.2 核心组件

| 组件 | 职责 | 技术 |
|------|------|------|
| **API Layer** | 对外接口，处理HTTP请求 | Django REST Framework |
| **Service Layer** | 业务逻辑，编排和协调 | Python Services |
| **Task Definitions** | 任务配置存储 | PostgreSQL/MySQL |
| **Execution Workers** | 任务执行，进度报告 | Python Threads/Processes |
| **Scheduler** | 任务调度，依赖管理 | Python Threading |

### 2.3 数据流

```
用户请求 → API验证 → 创建执行记录 → 获取执行器 → 执行任务
                                                        ↓
                   进度推送 ← WebSocket ← 监控服务 ← 报告进度
                                                        ↓
                   保存结果 ← 更新执行状态 ← 任务完成/失败
                                                        ↓
                   触发重试 ← 重试服务 ← 检查是否需要重试
```

---

## 三、数据模型设计

### 3.1 核心模型关系图

```
┌─────────────────┐
│  ETLTask        │
│  ───────────    │
│  id (PK)        │
│  task_name      │
│  task_code      │
│  executor_type  │
│  source_table   │
│  target_table   │
│  field_mapping  │
│  retry_times    │
│  schedule_conf  │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────┐         ┌──────────────────┐
│  ETLExecution   │         │ ETLTaskDependency│
│  ────────────   │         │ ──────────────── │
│  id (PK)        │         │ id (PK)          │
│  task_id (FK)   │◄────────┤ predecessor_id   │
│  execution_id   │  N   1  │ successor_id     │
│  status         │         └──────────────────┘
│  progress       │
│  checkpoint_data│
│  error_message  │
└─────────────────┘

┌─────────────────┐
│  ETLTaskTemplate│
│  ────────────   │
│  id (PK)        │
│  template_name  │
│  template_code  │
│  config_schema  │
│  default_config │
└─────────────────┘
```

### 3.2 ETLTask - 任务定义模型

**文件**: `backend/apps/etl/models.py`

```python
from django.db import models
from apps.system.models import BaseModel

class ETLTask(BaseModel):
    """ETL任务定义"""

    # ========== 基础信息 ==========
    task_name = models.CharField(max_length=128, verbose_name='任务名称',
                                help_text='任务显示名称')
    task_code = models.CharField(max_length=64, unique=True,
                                verbose_name='任务编码',
                                help_text='唯一标识，用于生成执行ID')
    description = models.TextField(blank=True, verbose_name='描述',
                                  help_text='任务详细说明')

    # ========== 执行器配置 ==========
    EXECUTOR_CHOICES = [
        ('datax', 'DataX'),
        ('sql', 'SQL脚本'),
        ('python', 'Python脚本'),
    ]
    executor_type = models.CharField(
        max_length=20,
        choices=EXECUTOR_CHOICES,
        default='datax',
        verbose_name='执行器类型'
    )

    # ========== 数据源配置 ==========
    source_datasource_id = models.IntegerField(
        verbose_name='源数据源ID',
        help_text='关联DataSource表'
    )
    target_datasource_id = models.IntegerField(
        verbose_name='目标数据源ID',
        help_text='关联DataSource表'
    )
    source_table = models.CharField(
        max_length=256,
        verbose_name='源表',
        help_text='源表名称'
    )
    target_table = models.CharField(
        max_length=256,
        verbose_name='目标表',
        help_text='目标表名称'
    )

    # ========== 字段映射 ==========
    field_mapping = models.JSONField(
        default=list,
        verbose_name='字段映射',
        help_text='字段映射列表，例如：[{"source":"id","target":"user_id","type":"int"}]'
    )

    # ========== 增量配置 ==========
    INCREMENT_CHOICES = [
        ('full', '全量'),
        ('timestamp', '时间戳增量'),
        ('id', '自增ID增量'),
    ]
    incremental_type = models.CharField(
        max_length=20,
        choices=INCREMENT_CHOICES,
        default='full',
        verbose_name='增量类型'
    )
    incremental_field = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='增量字段',
        help_text='用于增量抽取的字段名'
    )

    # ========== SQL配置（可选）==========
    pre_sql = models.TextField(
        blank=True,
        verbose_name='执行前SQL',
        help_text='任务执行前执行的SQL语句'
    )
    post_sql = models.TextField(
        blank=True,
        verbose_name='执行后SQL',
        help_text='任务执行后执行的SQL语句'
    )

    # ========== 执行配置 ==========
    timeout_seconds = models.IntegerField(
        default=3600,
        verbose_name='超时时间(秒)',
        help_text='任务执行超时时间'
    )
    retry_times = models.IntegerField(
        default=3,
        verbose_name='重试次数',
        help_text='失败后自动重试次数'
    )
    retry_interval_seconds = models.IntegerField(
        default=60,
        verbose_name='重试间隔(秒)',
        help_text='重试之间的等待时间'
    )
    batch_size = models.IntegerField(
        default=10000,
        verbose_name='批处理大小',
        help_text='每批处理的数据量'
    )

    # ========== 调度配置 ==========
    schedule_enabled = models.BooleanField(
        default=False,
        verbose_name='启用调度'
    )
    schedule_type = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('cron', 'Cron表达式'),
            ('interval', '固定间隔')
        ],
        verbose_name='调度类型'
    )
    schedule_conf = models.CharField(
        max_length=256,
        blank=True,
        verbose_name='调度配置',
        help_text='Cron表达式或间隔秒数'
    )

    # ========== 状态 ==========
    STATUS_CHOICES = [
        ('enabled', '启用'),
        ('disabled', '停用')
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='enabled',
        verbose_name='状态'
    )

    class Meta:
        db_table = 'etl_task'
        verbose_name = 'ETL任务'
        verbose_name_plural = 'ETL任务'
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.task_name} ({self.task_code})"
```

### 3.3 ETLExecution - 执行记录模型

```python
class ETLExecution(BaseModel):
    """ETL任务执行记录"""

    task = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name='关联任务'
    )
    execution_id = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='执行ID',
        help_text='唯一执行标识'
    )

    # ========== 执行状态 ==========
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
        ('retrying', '重试中'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='执行状态',
        db_index=True
    )

    # ========== 执行信息 ==========
    trigger_type = models.CharField(
        max_length=20,
        choices=[
            ('manual', '手动触发'),
            ('schedule', '调度触发'),
            ('retry', '重试触发')
        ],
        verbose_name='触发方式'
    )
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='开始时间',
        db_index=True
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='结束时间'
    )
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='执行时长(秒)'
    )

    # ========== 进度信息 ==========
    progress = models.FloatField(
        default=0.0,
        verbose_name='进度(0-100)',
        help_text='执行进度百分比'
    )
    current_phase = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='当前阶段',
        help_text='当前执行阶段描述'
    )

    # ========== 数据统计 ==========
    total_rows = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='总行数'
    )
    processed_rows = models.IntegerField(
        default=0,
        verbose_name='已处理行数'
    )
    success_rows = models.IntegerField(
        default=0,
        verbose_name='成功行数'
    )
    failed_rows = models.IntegerField(
        default=0,
        verbose_name='失败行数'
    )

    # ========== 断点续传 ==========
    checkpoint_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='检查点数据',
        help_text='用于断点续传的状态数据'
    )
    can_resume = models.BooleanField(
        default=False,
        verbose_name='可恢复',
        help_text='是否可以从断点恢复'
    )

    # ========== 错误信息 ==========
    error_message = models.TextField(
        blank=True,
        verbose_name='错误信息'
    )
    retry_count = models.IntegerField(
        default=0,
        verbose_name='重试次数'
    )

    class Meta:
        db_table = 'etl_execution'
        verbose_name = 'ETL执行记录'
        verbose_name_plural = 'ETL执行记录'
        ordering = ['-create_time']
        indexes = [
            models.Index(fields=['task', '-create_time']),
            models.Index(fields=['status']),
            models.Index(fields=['execution_id']),
        ]

    def __str__(self):
        return f"{self.task.task_name} - {self.execution_id} ({self.status})"
```

### 3.4 ETLTaskDependency - 任务依赖模型

```python
class ETLTaskDependency(BaseModel):
    """ETL任务依赖关系"""

    predecessor = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='successor_deps',
        verbose_name='前置任务',
        help_text='必须先执行的任务'
    )
    successor = models.ForeignKey(
        ETLTask,
        on_delete=models.CASCADE,
        related_name='predecessor_deps',
        verbose_name='后置任务',
        help_text='依赖前置任务完成后才能执行'
    )

    class Meta:
        db_table = 'etl_task_dependency'
        verbose_name = '任务依赖'
        verbose_name_plural = '任务依赖'
        unique_together = [['predecessor', 'successor']]

    def __str__(self):
        return f"{self.successor.task_name} 依赖 {self.predecessor.task_name}"
```

### 3.5 ETLTaskTemplate - 任务模板模型

```python
class ETLTaskTemplate(BaseModel):
    """ETL任务模板"""

    TEMPLATE_TYPE_CHOICES = [
        ('db_sync', '数据库同步'),
        ('file_import', '文件导入'),
        ('data_clean', '数据清洗'),
    ]

    template_name = models.CharField(
        max_length=128,
        verbose_name='模板名称'
    )
    template_code = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='模板编码'
    )
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        verbose_name='模板类型'
    )
    config_schema = models.JSONField(
        verbose_name='配置结构',
        help_text='JSON Schema定义的配置结构'
    )
    default_config = models.JSONField(
        verbose_name='默认配置',
        help_text='模板的默认配置值'
    )
    description = models.TextField(
        blank=True,
        verbose_name='描述'
    )

    class Meta:
        db_table = 'etl_task_template'
        verbose_name = '任务模板'
        verbose_name_plural = '任务模板'

    def __str__(self):
        return self.template_name
```

---

## 四、执行任务层设计

### 4.1 执行器架构

```
┌─────────────────────────────────────┐
│       BaseExecutor (抽象基类)        │
│  ────────────────────────────────   │
│  + validate(): (bool, str)          │
│  + execute(): Dict[str, Any]        │
│  + cancel(): bool                   │
│  + report_progress()                │
│  + save_checkpoint()                │
│  + load_checkpoint()                │
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────▼──────┐  ┌──────▼──────┐
│ DataXExec  │  │ SQLExecutor │
│            │  │             │
│ - 数据同步  │  │ - SQL执行   │
│ - 断点续传  │  │ - 批处理    │
└────────────┘  └─────────────┘
```

### 4.2 BaseExecutor - 执行器基类

**文件**: `backend/apps/etl/executors/base.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseExecutor(ABC):
    """
    执行器抽象基类

    所有执行器必须继承此类并实现抽象方法
    """

    def __init__(self, task: ETLTask, execution: ETLExecution):
        """
        初始化执行器

        Args:
            task: ETL任务实例
            execution: 执行记录实例
        """
        self.task = task
        self.execution = execution
        self._is_cancelled = False

    # ========== 抽象方法（子类必须实现）==========

    @abstractmethod
    def validate(self) -> tuple[bool, str]:
        """
        验证任务配置

        Returns:
            (is_valid, error_message)
            - is_valid: True表示验证通过
            - error_message: 验证失败时的错误信息
        """
        pass

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        执行任务

        Returns:
            执行结果字典：
            {
                'status': 'success' | 'failed',
                'total_rows': int,
                'processed_rows': int,
                'failed_rows': int,
                'error_message': str (optional)
            }
        """
        pass

    @abstractmethod
    def cancel(self) -> bool:
        """
        取消任务执行

        Returns:
            True表示取消成功
        """
        pass

    # ========== 辅助方法（子类可使用）==========

    def report_progress(self, progress: float, phase: str = "", message: str = ""):
        """
        报告执行进度

        Args:
            progress: 进度百分比 (0-100)
            phase: 当前阶段名称
            message: 进度消息
        """
        from ..services.monitor_service import MonitorService

        # 更新数据库
        self.execution.progress = progress
        self.execution.current_phase = phase
        self.execution.save(update_fields=['progress', 'current_phase'])

        # 推送到前端
        MonitorService.push_progress(
            execution_id=self.execution.execution_id,
            progress=progress,
            phase=phase,
            message=message
        )

        logger.info(
            f"[{self.execution.execution_id}] "
            f"Progress: {progress}% - {phase} - {message}"
        )

    def save_checkpoint(self, data: Dict[str, Any]):
        """
        保存检查点（用于断点续传）

        Args:
            data: 检查点数据
        """
        self.execution.checkpoint_data = data
        self.execution.can_resume = True
        self.execution.save(update_fields=['checkpoint_data', 'can_resume'])

        logger.info(f"[{self.execution.execution_id}] Checkpoint saved: {data}")

    def load_checkpoint(self) -> Dict[str, Any]:
        """
        加载检查点数据

        Returns:
            检查点数据字典
        """
        return self.execution.checkpoint_data or {}

    def is_cancelled(self) -> bool:
        """检查任务是否被取消"""
        return self._is_cancelled
```

### 4.3 DataXExecutor - DataX执行器

**文件**: `backend/apps/etl/executors/datax_executor.py`

```python
import json
import subprocess
import re
from typing import Dict, Any
from django.conf import settings
from .base import BaseExecutor

class DataXExecutor(BaseExecutor):
    """
    DataX执行器

    用于异构数据库之间的数据同步
    """

    def validate(self) -> tuple[bool, str]:
        """
        验证DataX环境和配置

        Returns:
            (is_valid, error_message)
        """
        # 1. 检查DataX是否安装
        if not hasattr(settings, 'DATAX_HOME'):
            return False, "未配置DATAX_HOME环境变量"

        import os
        if not os.path.exists(settings.DATAX_HOME):
            return False, f"DataX未安装: {settings.DATAX_HOME}"

        # 2. 检查数据源连接
        # TODO: 实现数据源连接验证

        # 3. 验证字段映射
        if not self.task.field_mapping:
            return False, "未配置字段映射"

        return True, ""

    def execute(self) -> Dict[str, Any]:
        """
        执行DataX任务

        流程：
        1. 生成DataX配置文件
        2. 检查是否有断点可以恢复
        3. 启动DataX进程
        4. 实时解析输出，更新进度
        5. 等待进程结束，返回结果

        Returns:
            执行结果字典
        """
        execution_id = self.execution.execution_id

        # 1. 生成DataX配置文件
        self.report_progress(0, "初始化", "正在生成DataX配置文件")
        config_path = self._generate_config()

        # 2. 检查是否有断点可以恢复
        checkpoint = self.load_checkpoint()
        if checkpoint:
            self.report_progress(
                0,
                "恢复执行",
                f"从检查点恢复: {checkpoint.get('processed_rows', 0)}行"
            )
            # TODO: 调整配置以支持断点续传

        # 3. 启动DataX进程
        self.report_progress(5, "启动DataX", "正在启动DataX进程")

        try:
            process = subprocess.Popen(
                ['python', f'{settings.DATAX_HOME}/bin/datax.py', config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 4. 实时解析输出，更新进度
            total_rows = 0
            processed_rows = 0
            last_checkpoint = 0

            for line in process.stdout:
                # 解析DataX输出，提取进度信息
                progress_info = self._parse_output(line)
                if progress_info:
                    processed_rows = progress_info.get('processed', 0)
                    total_rows = progress_info.get('total', 0)

                    if total_rows > 0:
                        progress = (processed_rows / total_rows * 100)

                        self.report_progress(
                            progress=progress,
                            phase="数据传输",
                            message=f"已处理 {processed_rows:,}/{total_rows:,} 行"
                        )

                        # 定期保存检查点（每10%）
                        if int(progress) - last_checkpoint >= 10:
                            self.save_checkpoint({
                                'processed_rows': processed_rows,
                                'total_rows': total_rows,
                                'offset': progress_info.get('offset')
                            })
                            last_checkpoint = int(progress)

            # 5. 等待进程结束
            returncode = process.wait()

            if returncode == 0:
                self.report_progress(100, "完成", "任务执行成功")
                return {
                    'status': 'success',
                    'total_rows': total_rows,
                    'processed_rows': processed_rows,
                    'failed_rows': 0
                }
            else:
                error_output = process.stderr.read()
                return {
                    'status': 'failed',
                    'error_message': error_output
                }

        except Exception as e:
            return {
                'status': 'failed',
                'error_message': f"执行异常: {str(e)}"
            }

    def cancel(self) -> bool:
        """
        取消DataX任务

        Returns:
            True表示取消成功
        """
        # TODO: 实现取消逻辑
        # 1. 终止DataX进程
        # 2. 清理临时文件
        return True

    def _generate_config(self) -> str:
        """
        生成DataX配置文件

        Returns:
            配置文件路径
        """
        # TODO: 根据task配置生成完整的DataX JSON配置
        # 这里只提供简化示例

        config = {
            "job": {
                "content": [
                    {
                        "reader": {
                            "name": "mysqlreader",
                            "parameter": {
                                "connection": [{
                                    "jdbcUrl": ["jdbc:mysql://..."],
                                    "querySql": [f"SELECT * FROM {self.task.source_table}"]
                                }],
                                "username": "...",
                                "password": "..."
                            }
                        },
                        "writer": {
                            "name": "mysqlwriter",
                            "parameter": {
                                "connection": [{
                                    "jdbcUrl": "jdbc:mysql://...",
                                    "table": [self.task.target_table]
                                }],
                                "username": "...",
                                "password": "...",
                                "column": [m['target'] for m in self.task.field_mapping],
                                "batchSize": self.task.batch_size
                            }
                        }
                    }
                ],
                "setting": {
                    "speed": {
                        "channel": 1,
                        "byte": 1048576
                    },
                    "errorLimit": {
                        "record": 0,
                        "percentage": 0.01
                    }
                }
            }
        }

        # 保存到文件
        import os
        job_dir = getattr(settings, 'DATAX_JOB_DIR', '/tmp/datax_jobs')
        os.makedirs(job_dir, exist_ok=True)

        config_path = os.path.join(job_dir, f'datax_{self.execution.execution_id}.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return config_path

    def _parse_output(self, line: str) -> Dict[str, Any]:
        """
        解析DataX输出，提取进度信息

        Args:
            line: DataX输出行

        Returns:
            进度信息字典 {'total': int, 'processed': int, 'offset': int}
        """
        # DataX输出示例:
        # 2023-01-01 12:00:00.123 [job-0] INFO  StandAloneJobCommunicator -
        # Total 100000 records, 50000/speed ...

        match = re.search(r'Total (\d+) records.*?(\d+)/speed', line)
        if match:
            return {
                'total': int(match.group(1)),
                'processed': int(match.group(2))
            }

        return {}
```

### 4.4 ExecutionService - 执行服务

**文件**: `backend/apps/etl/services/execution_service.py`

```python
import uuid
from django.utils import timezone
from django.db import transaction
from typing import Dict, Any
from ..models import ETLTask, ETLExecution
from ..executors.factory import ExecutorFactory

class ExecutionService:
    """
    执行服务

    负责任务执行的编排和管理
    """

    @staticmethod
    @transaction.atomic
    def create_execution(task_id: int, trigger_type: str = 'manual') -> ETLExecution:
        """
        创建执行记录

        Args:
            task_id: 任务ID
            trigger_type: 触发类型 (manual/schedule/retry)

        Returns:
            ETLExecution实例
        """
        task = ETLTask.objects.get(id=task_id)
        execution_id = f"{task.task_code}_{uuid.uuid4().hex[:12]}"

        execution = ETLExecution.objects.create(
            task=task,
            execution_id=execution_id,
            trigger_type=trigger_type,
            status='pending'
        )

        return execution

    @staticmethod
    def execute_task(execution_id: str) -> Dict[str, Any]:
        """
        执行任务

        Args:
            execution_id: 执行ID

        Returns:
            执行结果字典
        """
        execution = ETLExecution.objects.get(execution_id=execution_id)
        task = execution.task

        # 更新状态为运行中
        execution.status = 'running'
        execution.start_time = timezone.now()
        execution.save(update_fields=['status', 'start_time'])

        try:
            # 获取执行器
            executor = ExecutorFactory.get_executor(task, execution)

            # 验证配置
            is_valid, error_msg = executor.validate()
            if not is_valid:
                raise Exception(f"任务验证失败: {error_msg}")

            # 执行任务
            result = executor.execute()

            # 更新执行结果
            end_time = timezone.now()
            execution.end_time = end_time
            execution.duration_seconds = int(
                (end_time - execution.start_time).total_seconds()
            )
            execution.total_rows = result.get('total_rows')
            execution.processed_rows = result.get('processed_rows')
            execution.success_rows = result.get(
                'success_rows',
                result.get('processed_rows', 0)
            )
            execution.failed_rows = result.get('failed_rows', 0)
            execution.status = result['status']

            if result['status'] == 'failed':
                execution.error_message = result.get('error_message', '未知错误')

            execution.save()

            return result

        except Exception as e:
            # 异常处理
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.end_time = timezone.now()
            execution.save()

            # 触发重试
            from .retry_service import RetryService
            if RetryService.should_retry(execution):
                RetryService.schedule_retry(execution)

            raise

    @staticmethod
    def cancel_execution(execution_id: str) -> bool:
        """
        取消正在执行的任务

        Args:
            execution_id: 执行ID

        Returns:
            True表示取消成功
        """
        execution = ETLExecution.objects.get(execution_id=execution_id)

        if execution.status != 'running':
            return False

        # 获取执行器并取消
        from ..executors.factory import ExecutorFactory
        executor = ExecutorFactory.get_executor(execution.task, execution)
        success = executor.cancel()

        if success:
            execution.status = 'cancelled'
            execution.end_time = timezone.now()
            execution.save()

        return success
```

### 4.5 ExecutorFactory - 执行器工厂

**文件**: `backend/apps/etl/executors/factory.py`

```python
from typing import TYPE_CHECKING
from .datax_executor import DataXExecutor
# from .sql_executor import SQLExecutor
# from .python_executor import PythonExecutor

if TYPE_CHECKING:
    from ..models import ETLTask, ETLExecution

class ExecutorFactory:
    """
    执行器工厂

    根据任务类型创建对应的执行器实例
    """

    _executors = {
        'datax': DataXExecutor,
        # 'sql': SQLExecutor,
        # 'python': PythonExecutor,
    }

    @classmethod
    def get_executor(cls, task: 'ETLTask', execution: 'ETLExecution'):
        """
        获取执行器实例

        Args:
            task: ETL任务实例
            execution: 执行记录实例

        Returns:
            执行器实例

        Raises:
            ValueError: 如果执行器类型不存在
        """
        executor_class = cls._executors.get(task.executor_type)

        if executor_class is None:
            raise ValueError(
                f"未知的执行器类型: {task.executor_type}. "
                f"支持的类型: {list(cls._executors.keys())}"
            )

        return executor_class(task, execution)

    @classmethod
    def register_executor(cls, executor_type: str, executor_class):
        """
        注册新的执行器

        Args:
            executor_type: 执行器类型标识
            executor_class: 执行器类
        """
        cls._executors[executor_type] = executor_class
```

---

## 五、调度编排层设计

### 5.1 调度器工作流程

```
┌──────────────────────────────────────────────┐
│           ETLScheduler (调度器)               │
│  ─────────────────────────────────────────   │
│                                              │
│  1. 扫描待执行任务 (每分钟)                   │
│     ↓                                        │
│  2. 检查是否到期                              │
│     ↓                                        │
│  3. 检查依赖是否满足                          │
│     ↓                                        │
│  4. 执行任务                                  │
│     ↓                                        │
│  5. 等待下次扫描                              │
└──────────────────────────────────────────────┘
```

### 5.2 ScheduleService - 调度服务

**文件**: `backend/apps/etl/services/schedule_service.py`

```python
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from django.utils import timezone

class ScheduleService:
    """
    调度服务

    提供Cron解析、依赖检查等调度相关功能
    """

    @staticmethod
    def parse_cron(cron_expr: str) -> dict:
        """
        解析Cron表达式

        支持标准5字段格式: 分 时 日 月 周
        例如: "0 2 * * *" 表示每天凌晨2点

        Args:
            cron_expr: Cron表达式

        Returns:
            解析后的字典 {'minute': str, 'hour': str, ...}

        Raises:
            ValueError: 如果表达式格式错误
        """
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            raise ValueError(f"无效的Cron表达式: {cron_expr}")

        return {
            'minute': parts[0],
            'hour': parts[1],
            'day': parts[2],
            'month': parts[3],
            'weekday': parts[4]
        }

    @staticmethod
    def calc_next_run_time(
        schedule_type: str,
        schedule_conf: str,
        base_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        计算下次运行时间

        Args:
            schedule_type: 调度类型 (cron/interval)
            schedule_conf: 调度配置
            base_time: 基准时间，默认为当前时间

        Returns:
            下次运行时间，如果无法计算则返回None
        """
        base_time = base_time or timezone.now()

        if schedule_type == 'cron':
            return ScheduleService._calc_next_cron_time(schedule_conf, base_time)
        elif schedule_type == 'interval':
            seconds = int(schedule_conf)
            return base_time + timedelta(seconds=seconds)

        return None

    @staticmethod
    def _calc_next_cron_time(cron_expr: str, base_time: datetime) -> Optional[datetime]:
        """
        计算Cron表达式的下次执行时间

        Args:
            cron_expr: Cron表达式
            base_time: 基准时间

        Returns:
            下次执行时间
        """
        try:
            from croniter import croniter
            base = base_time.astimezone(timezone.get_current_timezone())
            cron = croniter(cron_expr, base)
            return cron.get_next(datetime)
        except ImportError:
            # 如果没有croniter库，使用简化版本
            # TODO: 实现简化的Cron计算
            pass

    @staticmethod
    def check_dependencies(task_id: int) -> Tuple[bool, List[str]]:
        """
        检查任务依赖是否满足

        Args:
            task_id: 任务ID

        Returns:
            (是否满足, 未满足的依赖说明列表)
        """
        from ..models import ETLTask, ETLTaskDependency, ETLExecution

        task = ETLTask.objects.get(id=task_id)
        dependencies = ETLTaskDependency.objects.filter(successor=task)

        if not dependencies.exists():
            return True, []

        unsatisfied = []

        for dep in dependencies:
            # 获取前置任务的最新执行记录
            latest_exec = ETLExecution.objects.filter(
                task=dep.predecessor
            ).order_by('-create_time').first()

            if not latest_exec:
                unsatisfied.append(
                    f"前置任务 {dep.predecessor.task_name} 尚未执行"
                )
            elif latest_exec.status != 'success':
                unsatisfied.append(
                    f"前置任务 {dep.predecessor.task_name} "
                    f"执行状态: {latest_exec.status}"
                )

        return len(unsatisfied) == 0, unsatisfied
```

### 5.3 ETLScheduler - 调度器

**文件**: `backend/apps/etl/scheduler.py`

```python
import time
import threading
import logging
from django.db import transaction
from django.utils import timezone
from .models import ETLTask
from .services.execution_service import ExecutionService
from .services.schedule_service import ScheduleService

logger = logging.getLogger(__name__)

class ETLScheduler:
    """
    ETL调度器

    基于线程的简单调度器，每分钟扫描一次待执行任务
    """

    def __init__(self, interval_seconds: int = 60):
        """
        初始化调度器

        Args:
            interval_seconds: 扫描间隔（秒）
        """
        self.running = False
        self.thread = None
        self.interval_seconds = interval_seconds

    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行")
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="ETLScheduler"
        )
        self.thread.start()
        logger.info("ETL调度器已启动")

    def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("ETL调度器已停止")

    def _run_loop(self):
        """主调度循环"""
        while self.running:
            try:
                logger.info("开始扫描待执行任务...")

                # 1. 获取所有启用了调度的任务
                tasks = ETLTask.objects.filter(
                    schedule_enabled=True,
                    status='enabled'
                )

                for task in tasks:
                    try:
                        # 2. 检查是否到期
                        now = timezone.now()
                        next_run = ScheduleService.calc_next_run_time(
                            task.schedule_type,
                            task.schedule_conf
                        )

                        if not next_run:
                            continue

                        # 如果下次执行时间在当前时间之前（或相差1分钟内），则执行
                        if (now - next_run).total_seconds() < 60:
                            # 3. 检查依赖
                            deps_satisfied, dep_errors = \
                                ScheduleService.check_dependencies(task.id)

                            if not deps_satisfied:
                                logger.warning(
                                    f"任务 {task.task_name} 依赖未满足: "
                                    f"{dep_errors}，跳过本次执行"
                                )
                                continue

                            # 4. 执行任务
                            logger.info(f"开始执行任务: {task.task_name}")
                            execution = ExecutionService.create_execution(
                                task.id,
                                trigger_type='schedule'
                            )

                            # 异步执行（使用线程池）
                            # 这里简化处理，直接同步执行
                            # TODO: 使用线程池或Celery异步执行
                            ExecutionService.execute_task(
                                execution.execution_id
                            )

                            logger.info(f"任务 {task.task_name} 执行完成")

                    except Exception as e:
                        logger.error(
                            f"任务 {task.task_name} 调度失败: {e}",
                            exc_info=True
                        )

            except Exception as e:
                logger.error(f"调度器异常: {e}", exc_info=True)

            # 等待下次扫描
            time.sleep(self.interval_seconds)


# 全局调度器实例
scheduler = ETLScheduler()
```

### 5.4 DependencyService - 依赖管理服务

**文件**: `backend/apps/etl/services/dependency_service.py`

```python
from typing import List, Tuple
from django.db import transaction
from ..models import ETLTask, ETLTaskDependency

class DependencyService:
    """
    依赖管理服务

    提供任务依赖的添加、删除和验证功能
    """

    @staticmethod
    @transaction.atomic
    def add_dependency(
        predecessor_id: int,
        successor_id: int
    ) -> Tuple[bool, str]:
        """
        添加依赖关系

        Args:
            predecessor_id: 前置任务ID
            successor_id: 后置任务ID

        Returns:
            (是否成功, 消息)
        """
        # 1. 检查循环依赖
        has_cycle, path = DependencyService._check_cycle(
            predecessor_id,
            successor_id
        )
        if has_cycle:
            return False, f"会产生循环依赖: {' -> '.join(path)}"

        # 2. 创建依赖
        try:
            ETLTaskDependency.objects.create(
                predecessor_id=predecessor_id,
                successor_id=successor_id
            )
            return True, "依赖添加成功"
        except Exception as e:
            return False, f"添加失败: {str(e)}"

    @staticmethod
    @transaction.atomic
    def remove_dependency(
        predecessor_id: int,
        successor_id: int
    ) -> Tuple[bool, str]:
        """
        移除依赖关系

        Args:
            predecessor_id: 前置任务ID
            successor_id: 后置任务ID

        Returns:
            (是否成功, 消息)
        """
        deleted, _ = ETLTaskDependency.objects.filter(
            predecessor_id=predecessor_id,
            successor_id=successor_id
        ).delete()

        if deleted > 0:
            return True, "依赖移除成功"
        else:
            return False, "依赖关系不存在"

    @staticmethod
    def _check_cycle(
        predecessor_id: int,
        successor_id: int
    ) -> Tuple[bool, List[str]]:
        """
        检查是否会形成循环依赖（使用DFS算法）

        Args:
            predecessor_id: 前置任务ID
            successor_id: 后置任务ID

        Returns:
            (是否有循环, 循环路径)
        """
        visited = set()
        path = []

        def dfs(task_id: int, target_id: int) -> bool:
            """深度优先搜索"""
            if task_id in visited:
                return False

            visited.add(task_id)
            task = ETLTask.objects.get(id=task_id)
            path.append(task.task_name)

            if task_id == target_id:
                return True

            # 检查task_id的所有后置任务
            successors = ETLTaskDependency.objects.filter(
                predecessor_id=task_id
            )

            for dep in successors:
                if dfs(dep.successor_id, target_id):
                    return True

            path.pop()
            return False

        # 检查：successor_id 是否可以到达 predecessor_id
        # 如果可以，则添加 predecessor -> successor 会形成循环
        has_cycle = dfs(successor_id, predecessor_id)
        return has_cycle, path

    @staticmethod
    def get_dependency_graph(task_id: int) -> dict:
        """
        获取任务的依赖图（用于可视化）

        Args:
            task_id: 任务ID

        Returns:
            DAG结构: {"nodes": [...], "edges": [...]}
        """
        # TODO: 实现依赖图构建
        pass
```

### 5.5 RetryService - 重试服务

**文件**: `backend/apps/etl/services/retry_service.py`

```python
import uuid
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from typing import Dict, Any
from ..models import ETLExecution

class RetryService:
    """
    重试服务

    负责任务失败后的重试逻辑
    """

    # 不可重试的错误类型
    NON_RETRYABLE_ERRORS = [
        '配置错误',
        '权限错误',
        '语法错误',
        'table not found',
        'column not found',
        'permission denied',
        'syntax error'
    ]

    @staticmethod
    def should_retry(execution: ETLExecution) -> bool:
        """
        判断是否应该重试

        Args:
            execution: 执行记录实例

        Returns:
            True表示应该重试
        """
        task = execution.task

        # 1. 检查重试次数
        if execution.retry_count >= task.retry_times:
            return False

        # 2. 检查错误类型
        error_message = (execution.error_message or '').lower()

        for err in RetryService.NON_RETRYABLE_ERRORS:
            if err.lower() in error_message:
                return False

        return True

    @staticmethod
    @transaction.atomic
    def schedule_retry(execution: ETLExecution) -> ETLExecution:
        """
        调度重试

        Args:
            execution: 失败的执行记录

        Returns:
            新的重试执行记录
        """
        task = execution.task

        # 创建新的执行记录
        retry_execution = ETLExecution.objects.create(
            task=task,
            execution_id=f"{task.task_code}_retry_{uuid.uuid4().hex[:8]}",
            trigger_type='retry',
            status='pending',
            retry_count=execution.retry_count + 1,
            checkpoint_data=execution.checkpoint_data,  # 保留检查点
            can_resume=execution.can_resume
        )

        # 计算重试时间
        retry_time = timezone.now() + timedelta(
            seconds=task.retry_interval_seconds
        )

        # TODO: 使用延迟任务队列（如Celery）
        # 这里简化处理，更新执行记录的创建时间
        retry_execution.create_time = retry_time
        retry_execution.save()

        return retry_execution
```

---

## 六、实时监控设计

### 6.1 监控架构

```
┌────────────────┐
│ Task Executor  │
│  - 执行任务     │
│  - 报告进度     │
└────────┬───────┘
         │
         ↓ report_progress()
┌────────────────┐
│ MonitorService │
│  - 更新数据库   │
│  - WebSocket推送│
└────────┬───────┘
         │
         ↓ WebSocket
┌────────────────┐
│  Frontend      │
│  - 实时进度条   │
│  - 日志展示     │
└────────────────┘
```

### 6.2 MonitorService - 监控服务

**文件**: `backend/apps/etl/services/monitor_service.py`

```python
import logging
from typing import Dict, Any
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

logger = logging.getLogger(__name__)

class MonitorService:
    """
    监控服务

    提供进度推送和统计信息查询功能
    """

    @staticmethod
    def push_progress(
        execution_id: str,
        progress: float,
        phase: str = "",
        message: str = ""
    ):
        """
        推送进度到前端（使用WebSocket）

        Args:
            execution_id: 执行ID
            progress: 进度百分比 (0-100)
            phase: 当前阶段
            message: 进度消息
        """
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'etl_progress',
                {
                    'type': 'etl_progress_update',
                    'execution_id': execution_id,
                    'progress': progress,
                    'phase': phase,
                    'message': message,
                    'timestamp': str(timezone.now())
                }
            )
        except Exception as e:
            logger.error(f"推送进度失败: {e}")

    @staticmethod
    def get_execution_stats(execution_id: str) -> Dict[str, Any]:
        """
        获取执行统计信息

        Args:
            execution_id: 执行ID

        Returns:
            统计信息字典
        """
        from ..models import ETLExecution

        execution = ETLExecution.objects.get(execution_id=execution_id)

        return {
            'execution_id': execution.execution_id,
            'task_name': execution.task.task_name,
            'task_code': execution.task.task_code,
            'status': execution.status,
            'trigger_type': execution.trigger_type,
            'progress': execution.progress,
            'current_phase': execution.current_phase,
            'start_time': execution.start_time.isoformat()
            if execution.start_time else None,
            'end_time': execution.end_time.isoformat()
            if execution.end_time else None,
            'duration_seconds': execution.duration_seconds,
            'total_rows': execution.total_rows,
            'processed_rows': execution.processed_rows,
            'success_rows': execution.success_rows,
            'failed_rows': execution.failed_rows,
            'error_message': execution.error_message,
            'can_resume': execution.can_resume,
            'retry_count': execution.retry_count
        }

    @staticmethod
    def get_recent_executions(limit: int = 50) -> list:
        """
        获取最近的执行记录

        Args:
            limit: 返回记录数量

        Returns:
            执行记录列表
        """
        from ..models import ETLExecution

        executions = ETLExecution.objects.select_related(
            'task'
        ).order_by('-create_time')[:limit]

        return [
            {
                'execution_id': e.execution_id,
                'task_name': e.task.task_name,
                'status': e.status,
                'progress': e.progress,
                'start_time': e.start_time.isoformat()
                if e.start_time else None,
                'duration_seconds': e.duration_seconds
            }
            for e in executions
        ]
```

### 6.3 WebSocket Consumer

**文件**: `backend/apps/etl/consumers.py`

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ETLProgressConsumer(AsyncWebsocketConsumer):
    """
    ETL进度推送Consumer

    实时向前端推送任务执行进度
    """

    async def connect(self):
        """WebSocket连接时加入进度组"""
        await self.channel_layer.group_add(
            'etl_progress',
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """WebSocket断开时离开进度组"""
        await self.channel_layer.group_discard(
            'etl_progress',
            self.channel_name
        )

    async def etl_progress_update(self, event):
        """
        接收进度更新事件并推送到前端

        Args:
            event: 事件字典，包含progress、phase、message等
        """
        await self.send(text_data=json.dumps({
            'type': 'progress_update',
            'data': {
                'execution_id': event['execution_id'],
                'progress': event['progress'],
                'phase': event['phase'],
                'message': event['message'],
                'timestamp': event['timestamp']
            }
        }))
```

---

## 七、API接口设计

### 7.1 RESTful API列表

| 端点 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `/api/etl/tasks/` | GET | 获取任务列表 | 查询 |
| `/api/etl/tasks/` | POST | 创建任务 | 创建 |
| `/api/etl/tasks/{id}/` | GET | 获取任务详情 | 查询 |
| `/api/etl/tasks/{id}/` | PUT/PATCH | 更新任务 | 更新 |
| `/api/etl/tasks/{id}/` | DELETE | 删除任务 | 删除 |
| `/api/etl/tasks/{id}/execute/` | POST | 手动执行任务 | 执行 |
| `/api/etl/tasks/{id}/cancel/` | POST | 取消正在执行的任务 | 执行 |
| `/api/etl/tasks/templates/` | GET | 获取任务模板列表 | 查询 |
| `/api/etl/executions/` | GET | 获取执行记录列表 | 查询 |
| `/api/etl/executions/{id}/` | GET | 获取执行记录详情 | 查询 |
| `/api/etl/executions/{id}/retry/` | POST | 重试失败的任务 | 执行 |
| `/api/etl/executions/{id}/progress/` | GET | 获取任务执行进度 | 查询 |
| `/api/etl/dependencies/` | GET | 获取依赖关系列表 | 查询 |
| `/api/etl/dependencies/` | POST | 添加依赖关系 | 更新 |
| `/api/etl/dependencies/{id}/` | DELETE | 删除依赖关系 | 更新 |

### 7.2 Views实现

**文件**: `backend/apps/etl/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import ETLTask, ETLExecution, ETLTaskDependency
from .serializers import (
    ETLTaskSerializer,
    ETLExecutionSerializer,
    ETLTaskDependencySerializer
)

class ETLTaskViewSet(viewsets.ModelViewSet):
    """ETL任务管理API"""

    queryset = ETLTask.objects.all()
    serializer_class = ETLTaskSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        手动执行任务

        POST /api/etl/tasks/{id}/execute/
        """
        from ..services.execution_service import ExecutionService
        from ..services.schedule_service import ScheduleService

        task = self.get_object()

        # 检查依赖
        deps_satisfied, dep_errors = ScheduleService.check_dependencies(task.id)

        if not deps_satisfied:
            return Response({
                'success': False,
                'message': '依赖未满足',
                'errors': dep_errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # 创建并执行任务
        execution = ExecutionService.create_execution(
            task.id,
            trigger_type='manual'
        )

        # TODO: 异步执行（使用Celery或线程池）

        return Response({
            'success': True,
            'execution_id': execution.execution_id,
            'message': '任务已提交执行'
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        取消正在执行的任务

        POST /api/etl/tasks/{id}/cancel/
        """
        from ..services.execution_service import ExecutionService

        task = self.get_object()
        running_exec = ETLExecution.objects.filter(
            task=task,
            status='running'
        ).first()

        if not running_exec:
            return Response({
                'success': False,
                'message': '没有正在执行的任务'
            }, status=status.HTTP_400_BAD_REQUEST)

        success = ExecutionService.cancel_execution(running_exec.execution_id)

        return Response({
            'success': success,
            'message': '任务已取消' if success else '取消失败'
        })

    @action(detail=False, methods=['get'])
    def templates(self, request):
        """
        获取任务模板列表

        GET /api/etl/tasks/templates/
        """
        from ..models import ETLTaskTemplate

        templates = ETLTaskTemplate.objects.all()
        data = [{
            'template_code': t.template_code,
            'template_name': t.template_name,
            'template_type': t.template_type,
            'default_config': t.default_config,
            'description': t.description
        } for t in templates]

        return Response(data)


class ETLExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """执行记录查询API（只读）"""

    queryset = ETLExecution.objects.select_related('task').all()
    serializer_class = ETLExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """支持筛选参数"""
        queryset = super().get_queryset()

        # 按任务筛选
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        # 按状态筛选
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """
        重试失败的任务

        POST /api/etl/executions/{id}/retry/
        """
        from ..services.retry_service import RetryService

        execution = self.get_object()

        if execution.status != 'failed':
            return Response({
                'success': False,
                'message': '只能重试失败的任务'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not RetryService.should_retry(execution):
            return Response({
                'success': False,
                'message': '不满足重试条件'
            }, status=status.HTTP_400_BAD_REQUEST)

        retry_exec = RetryService.schedule_retry(execution)

        return Response({
            'success': True,
            'retry_execution_id': retry_exec.execution_id,
            'message': '已创建重试任务'
        })

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        获取任务执行进度

        GET /api/etl/executions/{id}/progress/
        """
        from ..services.monitor_service import MonitorService

        execution = self.get_object()
        stats = MonitorService.get_execution_stats(execution.execution_id)

        return Response(stats)


class ETLTaskDependencyViewSet(viewsets.ModelViewSet):
    """任务依赖关系API"""

    queryset = ETLTaskDependency.objects.select_related(
        'predecessor',
        'successor'
    ).all()
    serializer_class = ETLTaskDependencySerializer
    permission_classes = [IsAuthenticated]
```

---

## 八、实施计划

### 8.1 总体时间线（8周）

```
Week 1-2:  基础框架搭建  ████████████
Week 3-4:  执行引擎开发  ████████████
Week 5-6:  重试和监控    ████████████
Week 7-8:  调度和依赖    ████████████
```

### 8.2 第一阶段：基础框架搭建（Week 1-2）

**目标**: 完成核心数据模型和基础框架

| 任务 | 工作量 | 产出 |
|------|--------|------|
| 创建ETL Django app | 0.5天 | app目录结构 |
| 定义数据模型 | 2天 | models.py |
| 创建数据库迁移 | 0.5天 | migrations |
| 编写Serializers | 1天 | serializers.py |
| 搭建基础API框架 | 1天 | views.py, urls.py |

**关键文件**:
- `backend/apps/etl/models.py`
- `backend/apps/etl/serializers.py`
- `backend/apps/etl/views.py`
- `backend/apps/etl/urls.py`

### 8.3 第二阶段：执行引擎开发（Week 3-4）

**目标**: 实现核心执行功能和断点续传

| 任务 | 工作量 | 产出 |
|------|--------|------|
| 实现BaseExecutor抽象基类 | 1天 | executors/base.py |
| 实现DataXExecutor | 3天 | executors/datax_executor.py |
| 实现ExecutorFactory | 0.5天 | executors/factory.py |
| 实现ExecutionService | 1天 | services/execution_service.py |
| 实现断点续传机制 | 2天 | checkpoint功能 |
| 实现进度报告功能 | 1天 | progress reporting |

**关键文件**:
- `backend/apps/etl/executors/base.py`
- `backend/apps/etl/executors/datax_executor.py`
- `backend/apps/etl/services/execution_service.py`

### 8.4 第三阶段：重试和监控（Week 5-6）

**目标**: 实现自动重试和实时监控

| 任务 | 工作量 | 产出 |
|------|--------|------|
| 实现RetryService | 1天 | services/retry_service.py |
| 实现MonitorService | 1天 | services/monitor_service.py |
| 配置WebSocket（Channels） | 1天 | routing.py |
| 实现进度推送Consumer | 1天 | consumers.py |
| 前端进度展示（可选） | 2天 | 前端组件 |

**关键文件**:
- `backend/apps/etl/services/retry_service.py`
- `backend/apps/etl/services/monitor_service.py`
- `backend/apps/etl/consumers.py`

### 8.5 第四阶段：调度和依赖（Week 7-8）

**目标**: 实现灵活调度和依赖管理

| 任务 | 工作量 | 产出 |
|------|--------|------|
| 实现ScheduleService | 1天 | services/schedule_service.py |
| 实现ETLScheduler | 2天 | scheduler.py |
| 实现DependencyService | 1天 | services/dependency_service.py |
| 启动调度器（management command） | 0.5天 | commands/start_etl_scheduler.py |
| 单元测试 | 2天 | tests/ |
| 集成测试 | 1.5天 | tests/integration/ |

**关键文件**:
- `backend/apps/etl/services/schedule_service.py`
- `backend/apps/etl/scheduler.py`
- `backend/apps/etl/services/dependency_service.py`
- `backend/apps/etl/management/commands/start_etl_scheduler.py`

---

## 九、技术栈和依赖

### 9.1 核心依赖

```txt
# requirements.txt

# Cron表达式解析
croniter==2.0.1

# WebSocket（实时监控）
channels==4.0.0
channels-redis==4.1.0
daphne==4.0.0

# 数据库连接
pymysql==1.1.0
psycopg2-binary==2.9.9

# 日志和监控
structlog==23.2.0

# Django REST Framework
djangorestframework==3.14.0

# 异步任务队列（可选）
# celery==5.3.0
# redis==5.0.0
```

### 9.2 环境变量配置

```python
# settings.py

import os

# ========== DataX配置 ==========
DATAX_HOME = os.environ.get('DATAX_HOME', '/opt/datax')
DATAX_JOB_DIR = os.environ.get('DATAX_JOB_DIR', '/tmp/datax_jobs')
DATAX_PYTHON = os.environ.get('DATAX_PYTHON', 'python3')

# ========== Redis配置 ==========
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')

# ========== ETL配置 ==========
ETL_MAX_CONCURRENT_TASKS = int(os.environ.get('ETL_MAX_CONCURRENT_TASKS', 5))
ETL_CHECKPOINT_INTERVAL = int(os.environ.get('ETL_CHECKPOINT_INTERVAL', 10))
ETL_SCHEDULER_INTERVAL = int(os.environ.get('ETL_SCHEDULER_INTERVAL', 60))

# ========== 日志配置 ==========
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_DIR = os.environ.get('LOG_DIR', '/var/log/etl')
```

### 9.3 数据库配置

```sql
-- 索引优化建议
CREATE INDEX idx_etl_execution_task_time ON etl_execution(task_id, create_time DESC);
CREATE INDEX idx_etl_execution_status ON etl_execution(status);
CREATE INDEX idx_etl_execution_execution_id ON etl_execution(execution_id);
```

---

## 十、测试和验证

### 10.1 单元测试

```python
# backend/apps/etl/tests/test_executors.py
from django.test import TestCase
from ..executors.datax_executor import DataXExecutor

class TestDataXExecutor(TestCase):
    """DataX执行器测试"""

    def test_validate_with_valid_config(self):
        """测试配置验证 - 有效配置"""
        pass

    def test_validate_with_invalid_config(self):
        """测试配置验证 - 无效配置"""
        pass

    def test_execute_success(self):
        """测试执行成功"""
        pass

    def test_execute_failure(self):
        """测试执行失败"""
        pass


# backend/apps/etl/tests/test_retry_service.py
class TestRetryService(TestCase):
    """重试服务测试"""

    def test_should_retry_with_retriable_error(self):
        """测试可重试错误"""
        pass

    def test_should_not_retry_with_non_retriable_error(self):
        """测试不可重试错误"""
        pass

    def test_should_not_retry_when_max_reached(self):
        """测试达到最大重试次数"""
        pass


# backend/apps/etl/tests/test_dependency_service.py
class TestDependencyService(TestCase):
    """依赖服务测试"""

    def test_add_dependency_success(self):
        """测试添加依赖成功"""
        pass

    def test_add_dependency_cyclic(self):
        """测试添加循环依赖"""
        pass

    def test_check_cycle_simple(self):
        """测试简单循环检测"""
        pass

    def test_check_cycle_complex(self):
        """测试复杂循环检测"""
        pass
```

### 10.2 集成测试场景

#### 场景1：基本执行流程

```python
def test_basic_execution_flow():
    """
    测试基本执行流程

    1. 创建任务
    2. 手动执行
    3. 查看进度
    4. 检查结果
    """
    # 1. 创建任务
    task = ETLTask.objects.create(
        task_name='测试任务',
        task_code='test_task',
        executor_type='datax',
        source_table='source_users',
        target_table='target_users',
        field_mapping=[
            {"source": "id", "target": "user_id"},
            {"source": "name", "target": "username"}
        ]
    )

    # 2. 手动执行
    execution = ExecutionService.create_execution(task.id)
    result = ExecutionService.execute_task(execution.execution_id)

    # 3. 检查结果
    assert result['status'] == 'success'
    assert result['processed_rows'] > 0
```

#### 场景2：断点续传

```python
def test_checkpoint_resume():
    """
    测试断点续传

    1. 执行任务
    2. 手动中断
    3. 从检查点恢复
    4. 验证数据完整性
    """
    # TODO: 实现测试逻辑
    pass
```

#### 场景3：自动重试

```python
def test_auto_retry():
    """
    测试自动重试

    1. 配置失败场景
    2. 触发任务
    3. 验证自动重试
    """
    # TODO: 实现测试逻辑
    pass
```

#### 场景4：依赖调度

```python
def test_dependency_scheduling():
    """
    测试依赖调度

    1. 创建任务A和B（B依赖A）
    2. 调度A和B
    3. 验证执行顺序
    """
    # TODO: 实现测试逻辑
    pass
```

#### 场景5：实时监控

```python
def test_realtime_monitoring():
    """
    测试实时监控

    1. 执行任务
    2. WebSocket连接
    3. 接收进度更新
    """
    # TODO: 实现测试逻辑
    pass
```

---

## 十一、部署和运维

### 11.1 启动调度器

#### 使用Django Management Command

```bash
# 启动调度器
python manage.py start_etl_scheduler

# 后台运行
nohup python manage.py start_etl_scheduler > /var/log/etl/scheduler.log 2>&1 &
```

#### 使用Systemd

```ini
# /etc/systemd/system/etl-scheduler.service
[Unit]
Description=ETL Scheduler
After=network.target

[Service]
Type=simple
User=django
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python manage.py start_etl_scheduler
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl start etl-scheduler

# 查看状态
sudo systemctl status etl-scheduler

# 开机自启
sudo systemctl enable etl-scheduler
```

### 11.2 监控告警

#### 任务失败告警

```python
# backend/apps/etl/services/alert_service.py
class AlertService:
    """告警服务"""

    @staticmethod
    def send_failure_alert(execution: ETLExecution):
        """
        发送任务失败告警

        支持多种渠道：邮件、钉钉、企业微信
        """
        task = execution.task

        message = f"""
        ETL任务执行失败

        任务名称: {task.task_name}
        任务编码: {task.task_code}
        执行ID: {execution.execution_id}
        失败原因: {execution.error_message}
        开始时间: {execution.start_time}
        结束时间: {execution.end_time}
        执行时长: {execution.duration_seconds}秒
        """

        # 发送邮件
        # send_email(...)

        # 发送钉钉
        # send_dingtalk(...)

        # 发送企业微信
        # send_wechat(...)
```

#### 任务超时告警

```python
# 检查超时任务
from datetime import timedelta

timeout_threshold = timezone.now() - timedelta(hours=1)

timeout_executions = ETLExecution.objects.filter(
    status='running',
    start_time__lt=timeout_threshold
)

for exec in timeout_executions:
    AlertService.send_timeout_alert(exec)
```

### 11.3 日志管理

#### 日志配置

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/etl/etl.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/etl/etl_error.log',
            'maxBytes': 1024 * 1024 * 100,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.etl': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 11.4 性能优化

#### 数据库连接池

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'CONN_MAX_AGE': 600,  # 连接池
        'OPTIONS': {
            'pool_size': 10,
            'max_overflow': 20,
        }
    }
}
```

#### 异步执行

```python
# 使用线程池执行任务
from concurrent.futures import ThreadPoolExecutor

executor_pool = ThreadPoolExecutor(max_workers=5)

def execute_task_async(execution_id: str):
    executor_pool.submit(ExecutionService.execute_task, execution_id)
```

---

## 十二、总结

### 12.1 核心特性

✅ **断点续传**
- 任务可中断恢复
- 定期保存检查点
- 支持从断点继续执行

✅ **自动重试**
- 失败自动重试
- 可配置重试次数和间隔
- 智能识别不可重试错误

✅ **实时监控**
- WebSocket推送进度
- 详细的执行日志
- 性能指标收集

✅ **灵活调度**
- 支持Cron表达式
- 任务依赖管理
- 循环依赖检测

### 12.2 架构优势

| 优势 | 说明 |
|------|------|
| **简单清晰** | 避免过度设计，代码结构清晰 |
| **模块化** | 执行器、服务、调度器解耦 |
| **可扩展** | 易于添加新的执行器类型 |
| **可维护** | 代码易于理解和维护 |
| **可测试** | 完善的单元测试和集成测试 |

### 12.3 后续扩展方向

#### 短期（3-6个月）

- [ ] 支持更多执行器（Spark、Flink）
- [ ] 完善任务模板库
- [ ] 数据质量检查集成
- [ ] 任务编排可视化

#### 中期（6-12个月）

- [ ] 分布式调度（多节点）
- [ ] 工作流引擎（复杂DAG）
- [ ] 数据血缘自动追踪
- [ ] 性能监控大盘

#### 长期（1年以上）

- [ ] 智能调度（基于资源使用）
- [ ] 自适应重试策略
- [ ] 机器学习优化
- [ ] 多租户隔离

---

## 附录

### A. 参考资料

- [DataX官方文档](https://github.com/alibaba/DataX)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Channels](https://channels.readthedocs.io/)
- [Cron表达式详解](https://crontab.guru/)

### B. 联系方式

如有问题或建议，请联系开发团队。

---

**文档结束**
