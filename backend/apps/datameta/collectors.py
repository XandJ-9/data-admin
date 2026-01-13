"""
线程安全的元数据采集执行器
"""
import threading
import uuid
import logging

from django.db import transaction, connections
from django.utils import timezone

from apps.datameta.models import MetaCollectionTask, MetaTable, MetaColumn
from apps.datasource.models import DataSource
from apps.dbutils import list_tables, get_table_schema, get_table_info

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
        self.thread.start()
        return True

    def stop(self):
        """停止采集"""
        self._stop_event.set()
        if self.task:
            self.task.status = 'cancelled'
            self.task.save(update_fields=['status'])

    def _run_collection(self, ds_id, database_name, user):
        """采集主逻辑（在子线程中运行）"""
        thread_id = threading.get_ident()
        logger.info(f"启动采集线程 {thread_id}，任务 {self.task_id}")

        # 关闭现有连接避免线程安全问题
        connections.close_all()

        try:
            self.task.status = 'running'
            self.task.thread_id = str(thread_id)
            self.task.started_at = timezone.now()
            self.task.save(update_fields=['status', 'thread_id', 'started_at'])

            ds = DataSource.objects.get(pk=ds_id)
            info = self._build_info(ds)
            if database_name:
                info['database'] = database_name

            tables = list_tables(info)
            self.task.total_tables = len(tables)
            self.task.save(update_fields=['total_tables'])

            for idx, table in enumerate(tables):
                if self._stop_event.is_set():
                    self.task.status = 'cancelled'
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

                self.task.save(update_fields=['collected_tables', 'failed_tables'])

            if self.task.status != 'cancelled':
                self.task.status = 'completed'

            self.task.progress = 100
            self.task.completed_at = timezone.now()
            self.task.save(update_fields=['status', 'progress', 'completed_at'])

        except Exception as e:
            logger.exception(f"任务 {self.task_id} 采集失败: {e}")
            self.task.status = 'failed'
            self.task.error_message = str(e)
            self.task.completed_at = timezone.now()
            self.task.save(update_fields=['status', 'error_message', 'completed_at'])

        finally:
            with _tasks_registry_lock:
                _tasks_registry.pop(self.task_id, None)
            connections.close_all()

    def _collect_table_safe(self, info, ds_id, table, user):
        """安全采集单张表（独立事务）"""
        with transaction.atomic():
            tinfo = get_table_info(info, table) or {}
            comment = tinfo.get('comment') or ''
            database_name = tinfo.get('databaseName') or ''

            obj, created = MetaTable.objects.update_or_create(
                data_source_id=ds_id,
                table_name=table,
                database=database_name,
                defaults={'comment': comment, 'del_flag': '0'}
            )

            if user and hasattr(user, 'username'):
                if created:
                    obj.create_by = user.username
                    obj.save(update_fields=['create_by'])
                else:
                    obj.update_by = user.username
                    obj.save(update_fields=['update_by', 'update_time'])

            MetaColumn.objects.filter(data_source_id=ds_id, table=obj).delete()

            cols = get_table_schema(info, table)
            for c in cols:
                col, _ = MetaColumn.objects.update_or_create(
                    data_source_id=ds_id,
                    table=obj,
                    name=c.get('name'),
                    defaults={
                        'order': c.get('order') or 0,
                        'type': c.get('type') or '',
                        'notnull': bool(c.get('notnull')),
                        'default': str(c.get('default') or ''),
                        'primary': bool(c.get('primary')),
                        'comment': c.get('comment') or '',
                        'del_flag': '0'
                    }
                )
                if user and hasattr(user, 'username'):
                    if col.create_by == '':
                        col.create_by = user.username
                        col.save(update_fields=['create_by'])
                    else:
                        col.update_by = user.username
                        col.save(update_fields=['update_by', 'update_time'])

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
def start_collection_task(ds_id, database_name='', user=None):
    """创建并启动采集任务"""
    task_id = str(uuid.uuid4())

    task = MetaCollectionTask.objects.create(
        task_id=task_id,
        data_source_id=ds_id,
        database_name=database_name,
        status='pending',
        create_by=user.username if user and hasattr(user, 'username') else '',
        update_by=user.username if user and hasattr(user, 'username') else ''
    )

    executor = MetadataCollectionExecutor(task_id)
    if executor.start(ds_id, database_name, user):
        return task
    task.delete()
    return None


def cancel_collection_task(task_id):
    """取消采集任务"""
    with _tasks_registry_lock:
        executor = _tasks_registry.get(task_id)
        if executor:
            executor.stop()
            return True
    return False


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
