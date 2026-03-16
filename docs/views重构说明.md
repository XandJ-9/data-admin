# views.py 重构说明

## 重构概述

将 `backend/apps/dataetl/views.py` 中的复杂业务逻辑拆分到专门的服务层，遵循单一职责原则。

## 重构前的问题

1. **视图层过于复杂**：包含大量业务逻辑
2. **代码重复**：多处重复的业务逻辑
3. **难以测试**：业务逻辑耦合在视图中
4. **可维护性差**：修改业务逻辑需要改动视图

## 重构后的架构

### 服务层职责划分

```
views.py (视图层)
    ↓ 调用
services/
    ├── task.py          - TaskService (任务管理)
    ├── execution.py      - ExecutionService (任务执行)
    ├── version.py        - VersionService (版本管理)
    ├── config.py         - ConfigService (配置管理)
    ├── quality.py        - QualityService (质量检查)
    └── monitoring.py     - MonitoringService (监控统计)
```

## 新增服务文件

### 1. ExecutionService (execution.py)

**职责**：处理ETL任务的执行生命周期

**主要方法**：
- `submit_task()` - 提交任务执行
- `_execute_async()` - 异步执行任务
- `cancel_execution()` - 取消执行
- `create_progress()` - 创建进度记录
- `update_progress()` - 更新进度

**从视图迁移的逻辑**：
- ✅ 任务提交和异步执行
- ✅ 执行进度跟踪
- ✅ 执行前/后质检集成
- ✅ 执行状态管理

**代码量**：~150行

### 2. VersionService (version.py)

**职责**：管理ETL任务版本

**主要方法**：
- `create_version()` - 创建版本快照
- `get_task_versions()` - 获取所有版本
- `rollback_version()` - 回滚到指定版本
- `get_current_version()` - 获取当前版本
- `_create_config_snapshot()` - 创建配置快照

**从视图迁移的逻辑**：
- ✅ 版本创建逻辑
- ✅ 版本回滚逻辑
- ✅ 配置快照生成

**代码量**：~120行

### 3. ConfigService (config.py)

**职责**：处理任务配置相关操作

**主要方法**：
- `validate_datax_config()` - 验证DataX配置
- `generate_datax_config()` - 生成DataX配置
- `dry_run()` - 模拟执行

**从视图迁移的逻辑**：
- ✅ DataX配置验证
- ✅ DataX配置生成
- ✅ 模拟执行逻辑

**代码量**：~80行

## 视图层简化

### 简化前（原代码）

```python
@action(detail=True, methods=['post'], url_path='execute')
def execute_task(self, request, pk=None):
    task = self.get_object()

    # 检查任务状态
    if task.status != '0':
        return Response({...})

    # 生成执行ID
    execution_id = f"ETL-{uuid.uuid4().hex[:16].upper()}"

    # 创建执行日志
    log = ETLExecutionLog.objects.create(...)

    # 异步执行任务
    thread = threading.Thread(
        target=self._execute_async,
        args=(task, log)
    )
    thread.daemon = True
    thread.start()

    return self.data({...})

def _execute_async(self, task, log):
    # 180+ 行的执行逻辑
    ...
```

### 简化后（新代码）

```python
@action(detail=True, methods=['post'], url_path='execute')
def execute_task(self, request, pk=None):
    task = self.get_object()

    try:
        executed_by = request.user.username if request.user.is_authenticated else 'system'
        execution_service = ExecutionService()
        execution_id = execution_service.submit_task(task, executed_by, 'manual')

        return self.data({
            'executionId': execution_id,
            'message': '任务已提交执行'
        })
    except ValueError as e:
        return Response({
            'code': 500,
            'msg': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'code': 500,
            'msg': f'提交任务失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## 重构收益

### 代码质量提升

| 指标 | 重构前 | 重构后 | 改进 |
|-----|-------|-------|------|
| views.py 行数 | ~950行 | ~650行 | ⬇️ 32% |
| 单个方法最大行数 | 180行 | 30行 | ⬇️ 83% |
| 业务逻辑耦合度 | 高 | 低 | ✅ |
| 代码可测试性 | 低 | 高 | ✅ |

### 架构改进

**职责清晰**：
- 视图层：请求处理、响应
- 服务层：业务逻辑

**易于测试**：
- 服务层可独立单元测试
- 视图层只需要测试请求/响应

**易于维护**：
- 业务逻辑修改不影响视图
- 视图层修改不影响业务逻辑

### 具体改进

1. **任务执行** (`ExecutionService`)
   - ✅ 执行逻辑独立
   - ✅ 进度跟踪独立
   - ✅ 质检集成独立

2. **版本管理** (`VersionService`)
   - ✅ 版本创建独立
   - ✅ 配置快照独立
   - ✅ 回滚逻辑独立

3. **配置管理** (`ConfigService`)
   - ✅ 配置验证独立
   - ✅ 配置生成独立
   - ✅ 模拟执行独立

## 代码示例对比

### 示例1：任务执行

**重构前**：
```python
# views.py - 180行的 _execute_async 方法
def _execute_async(self, task, log):
    try:
        log.status = 'running'
        log.start_time = timezone.now()
        log.save()

        executor = ExecutorFactory.create_executor(...)
        is_valid, error_message = executor.validate()
        if not is_valid:
            raise Exception(...)

        result = executor.execute()
        log.status = result.get('status', 'failed')
        ...
```

**重构后**：
```python
# views.py - 简化的视图方法
@action(detail=True, methods=['post'], url_path='execute')
def execute_task(self, request, pk=None):
    task = self.get_object()
    execution_service = ExecutionService()
    execution_id = execution_service.submit_task(task, executed_by, 'manual')
    return self.data({'executionId': execution_id})

# services/execution.py - 完整的执行逻辑
class ExecutionService:
    def submit_task(self, task, executed_by, trigger_type):
        ...
        thread = threading.Thread(target=self._execute_async, args=(task, log))
        thread.start()
        ...

    def _execute_async(self, task, log):
        progress = ETLExecutionProgress.objects.create(...)
        quality_passed, quality_errors = self.quality_service.run_pre_check(task)
        ...
```

### 示例2：版本回滚

**重构前**：
```python
# views.py - 50+行的回滚逻辑
@action(detail=True, methods=['post'], url_path='rollback')
def rollback_version(self, request, pk=None):
    task = self.get_object()
    version_number = request.data.get('versionNumber')

    try:
        version = ETLTaskVersion.objects.get(task=task, version_number=version_number)
    except ETLTaskVersion.DoesNotExist:
        return Response({...})

    snapshot = version.config_snapshot
    task.task_name = snapshot.get('taskName', task.task_name)
    task.description = snapshot.get('description', task.description)
    # ... 20+行赋值语句
    task.save()

    return self.data({'message': f'已回滚到版本 {version_number}'})
```

**重构后**：
```python
# views.py - 简化的视图方法
@action(detail=True, methods=['post'], url_path='rollback')
def rollback_version(self, request, pk=None):
    task = self.get_object()
    version_number = request.data.get('versionNumber')

    try:
        VersionService.rollback_version(task, version_number)
        return self.data({'message': f'已回滚到版本 {version_number}'})
    except ValueError as e:
        return Response({...})

# services/version.py - 完整的回滚逻辑
class VersionService:
    @staticmethod
    @transaction.atomic
    def rollback_version(task, version_number):
        version = ETLTaskVersion.objects.get(task=task, version_number=version_number)
        snapshot = version.config_snapshot
        # 配置恢复逻辑
        task.save()
        return True
```

## 测试友好

### 重构前：难以测试

```python
# 需要模拟整个HTTP请求
def test_execute_task(self):
    response = self.client.post('/api/etl/tasks/1/execute')
    self.assertEqual(response.status_code, 200)
```

### 重构后：易于单元测试

```python
# 可以直接测试服务层
def test_submit_task(self):
    service = ExecutionService()
    execution_id = service.submit_task(task, 'test_user', 'manual')
    self.assertIsNotNone(execution_id)

def test_execute_async(self):
    service = ExecutionService()
    # 测试异步执行逻辑
    ...
```

## 向后兼容

✅ **API接口保持不变**
- 所有端点路径不变
- 请求/响应格式不变
- 前端无需修改

✅ **功能完全保留**
- 所有原有功能正常工作
- 新增的服务层只是内部重构

## 迁移指南

### 对于开发者

1. **业务逻辑修改**
   - ❌ 旧：修改 views.py
   - ✅ 新：修改 services/ 下的对应服务

2. **单元测试**
   - ❌ 旧：测试视图（复杂）
   - ✅ 新：测试服务（简单）

3. **新增功能**
   - ✅ 在服务层实现业务逻辑
   - ✅ 在视图层调用服务方法

## 文件清单

**新增文件**（3个）：
- `backend/apps/dataetl/services/execution.py`
- `backend/apps/dataetl/services/version.py`
- `backend/apps/dataetl/services/config.py`

**修改文件**（2个）：
- `backend/apps/dataetl/views.py` - 简化，移除业务逻辑
- `backend/apps/dataetl/services/__init__.py` - 添加新服务导出

## 总结

通过这次重构：
- ✅ 代码组织更清晰
- ✅ 职责划分更明确
- ✅ 更易于测试
- ✅ 更易于维护
- ✅ 向后兼容

**符合设计原则**：
- 单一职责原则 (SRP)
- 开闭原则 (OCP)
- 依赖倒置原则 (DIP)

---

**文档版本**：v1.0
**编写日期**：2026-03-16
