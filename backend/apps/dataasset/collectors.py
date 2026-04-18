"""
线程安全的元数据采集执行器
"""
import threading
import uuid
import logging

from django.db import IntegrityError
from django.db import transaction
from django.db import connections
from django.utils import timezone

from apps.dataasset.models import MetaCollectionTask, resolve_collection_scope
from apps.datasource.models import DataSource
from apps.dbutils import list_tables
from apps.dataasset.services import collect_table_metadata
from apps.dataasset.utils import sanitize_collection_error_message

logger = logging.getLogger(__name__)

# 线程安全任务注册表
_tasks_registry = {}
_tasks_registry_lock = threading.Lock()


class MetadataCollectionExecutor:
    """元数据采集执行器 - 线程安全"""

    def __init__(self, task_id):
        self.task_id = task_id
        self.task = None
        self.thread = None
        self._stop_event = threading.Event()

    def start(self, ds_id, database_name='', user=None):
        """启动采集线程"""
        try:
            self.task = MetaCollectionTask.objects.get(task_id=self.task_id)
        except MetaCollectionTask.DoesNotExist:
            logger.error(f"任务 {self.task_id} 不存在")
            return False

        # 检查是否已有该数据源的运行中任务
        with _tasks_registry_lock:
            for task_id, executor in _tasks_registry.items():
                if (executor.task.data_source_id == ds_id and
                    executor.task.status in ['pending', 'running']):
                    logger.warning(f"数据源 {ds_id} 已有运行中的任务")
                    return False
            _tasks_registry[self.task_id] = self

        self.thread = threading.Thread(
            target=self._run_collection,
            args=(ds_id, database_name, user),
            daemon=True
        )
        try:
            self.thread.start()
        except Exception:
            with _tasks_registry_lock:
                _tasks_registry.pop(self.task_id, None)
            raise
        return True

    def stop(self):
        """停止采集"""
        self._stop_event.set()
        if self.task:
            self.task.status = 'cancelled'
            self.task.completed_at = timezone.now()
            self.task.save(update_fields=['status', 'completed_at'])

    def _refresh_cancel_state(self):
        if not self.task:
            return False
        self.task.refresh_from_db(fields=['status'])
        if self.task.status == 'cancelled':
            self._stop_event.set()
            return True
        return self._stop_event.is_set()

    def _run_collection(self, ds_id, database_name, user):
        """采集主逻辑（在子线程中运行）"""
        thread_id = threading.get_ident()
        logger.info(f"启动采集线程 {thread_id}，任务 {self.task_id}")

        # 关闭现有连接避免线程安全问题
        connections.close_all()

        try:
            started_at = timezone.now()
            updated = MetaCollectionTask.objects.filter(pk=self.task.pk, status='pending').update(
                status='running',
                thread_id=str(thread_id),
                started_at=started_at,
            )
            self.task.refresh_from_db()
            if not updated:
                if self.task.status == 'cancelled' and not self.task.completed_at:
                    self.task.completed_at = started_at
                    self.task.save(update_fields=['completed_at'])
                return

            ds = DataSource.objects.get(pk=ds_id)
            info = self._build_info(ds)
            if database_name:
                info['database'] = database_name

            tables = list_tables(info)
            self.task.total_tables = len(tables)
            self.task.save(update_fields=['total_tables'])

            for idx, table in enumerate(tables):
                if self._refresh_cancel_state():
                    break

                self.task.current_table = table
                self.task.progress = int((idx / len(tables)) * 100)
                self.task.save(update_fields=['current_table', 'progress'])

                try:
                    self._collect_table_safe(info, ds_id, table, user)
                    self.task.collected_tables += 1
                except Exception as e:
                    logger.error(f"采集表 {table} 失败: {e}")
                    self.task.failed_tables += 1
                    self.task.error_message = '部分表采集失败，请查看服务端日志'

                if self._refresh_cancel_state():
                    break
                self.task.save(update_fields=['collected_tables', 'failed_tables', 'error_message'])

            self.task.refresh_from_db(fields=['status'])
            if self.task.status == 'cancelled':
                self.task.completed_at = timezone.now()
                self.task.save(update_fields=['completed_at'])
            else:
                self.task.status = 'completed' if self.task.failed_tables == 0 else 'failed'
                self.task.progress = 100
                self.task.completed_at = timezone.now()
                if self.task.failed_tables:
                    self.task.error_message = '部分表采集失败，请查看服务端日志'
                self.task.save(update_fields=['status', 'progress', 'completed_at', 'error_message'])

        except Exception as e:
            logger.exception(f"任务 {self.task_id} 采集失败: {e}")
            self.task.status = 'failed'
            self.task.error_message = sanitize_collection_error_message(e)
            self.task.completed_at = timezone.now()
            self.task.save(update_fields=['status', 'error_message', 'completed_at'])

        finally:
            with _tasks_registry_lock:
                _tasks_registry.pop(self.task_id, None)
            connections.close_all()

    def _collect_table_safe(self, info, ds_id, table, user):
        """安全采集单张表（独立事务）"""
        collect_table_metadata(info, ds_id, table, user=user)

    def _build_info(self, ds):
        return {
            'type': ds.db_type,
            'host': ds.host,
            'port': ds.port,
            'username': ds.username,
            'password': ds.password,
            'database': ds.db_name,
            'params': ds.params or {},
        }


# 任务管理函数
def create_collection_task(ds_id, database_name='', user=None):
    """创建采集任务并占用数据源执行槽位"""
    task_id = str(uuid.uuid4())
    with transaction.atomic():
        data_source = DataSource.objects.select_for_update().only('id', 'db_type').get(pk=ds_id)
        if MetaCollectionTask.objects.select_for_update().filter(data_source_id=ds_id, status__in=['pending', 'running']).exists():
            logger.warning(f"数据源 {ds_id} 已有数据库层面未结束的采集任务")
            return None
        scope_level, scope_catalog_name, scope_schema_name = resolve_collection_scope(
            data_source.db_type,
            database_name,
        )
        try:
            return MetaCollectionTask.objects.create(
                task_id=task_id,
                data_source_id=ds_id,
                database_name=database_name,
                scope_level=scope_level,
                scope_catalog_name=scope_catalog_name,
                scope_schema_name=scope_schema_name,
                scope_asset_name='',
                run_mode='full',
                status='pending',
                create_by=user.username if user and hasattr(user, 'username') else '',
                update_by=user.username if user and hasattr(user, 'username') else ''
            )
        except IntegrityError:
            logger.warning(f"数据源 {ds_id} 已有数据库唯一约束保护的活动任务")
            return None


def start_collection_task(ds_id, database_name='', user=None):
    """创建并启动采集任务"""
    def _start_executor(created_task):
        try:
            executor = MetadataCollectionExecutor(created_task.task_id)
            if executor.start(ds_id, database_name, user):
                return
            error_message = '启动采集线程失败'
        except Exception as exc:
            logger.exception(f"任务 {created_task.task_id} 启动失败: {exc}")
            with _tasks_registry_lock:
                _tasks_registry.pop(created_task.task_id, None)
            error_message = str(exc)
        MetaCollectionTask.objects.filter(pk=created_task.pk, status='pending').update(
            status='failed',
            error_message=sanitize_collection_error_message(error_message),
            completed_at=timezone.now(),
            update_by=user.username if user and hasattr(user, 'username') else '',
        )

    task = None
    with transaction.atomic():
        task = create_collection_task(ds_id, database_name, user)
        if not task:
            return None
        transaction.on_commit(lambda: _start_executor(task))

    task.refresh_from_db(fields=['status'])
    if not task:
        return None
    if task.status == 'failed':
        return None
    return task


def cancel_collection_task(task_id):
    """取消采集任务"""
    with _tasks_registry_lock:
        executor = _tasks_registry.get(task_id)
        if executor:
            executor.stop()
            return True
    updated = MetaCollectionTask.objects.filter(
        task_id=task_id,
        status__in=['pending', 'running'],
    ).update(
        status='cancelled',
        completed_at=timezone.now(),
        error_message='任务已取消',
    )
    return bool(updated)


def get_task_status(task_id):
    """获取任务状态"""
    try:
        task = MetaCollectionTask.objects.get(task_id=task_id)
        return {
            'taskId': task.task_id,
            'status': task.status,
            'progress': task.progress,
            'currentTable': task.current_table,
            'totalTables': task.total_tables,
            'collectedTables': task.collected_tables,
            'failedTables': task.failed_tables,
            'errorMessage': task.error_message,
            'startedAt': task.started_at.isoformat() if task.started_at else None,
            'completedAt': task.completed_at.isoformat() if task.completed_at else None,
        }
    except MetaCollectionTask.DoesNotExist:
        return None
