from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db import transaction

from apps.system.views.core import BaseViewSet
from apps.system.permission import HasRolePermission
from apps.dbutils.factory import get_executor
from apps.dbutils import list_tables, get_table_schema, get_table_info, list_tables_info, get_databases
from apps.common.encrypt import decrypt_password

from .models import DataSource, MetaTable, MetaColumn, MetaCollectionTask, TableLineage
from .serializers import (
    DataSourceSerializer, DataSourceQuerySerializer, DataSourceUpdateSerializer, DataSourceCreateSerializer,
    MetaTableSerializer, MetaTableQuerySerializer,
    MetaColumnSerializer, MetaColumnQuerySerializer,
    MetaCollectionTaskSerializer, MetaCollectionTaskCreateSerializer,
    TableLineageSerializer, TableLineageCreateSerializer, TableLineageUpdateSerializer,
    TableLineageQuerySerializer, TableLineageGraphSerializer
)
from .collectors import start_collection_task, cancel_collection_task, get_task_status


# ==================== DataSource ViewSet ====================

class DataSourceViewSet(BaseViewSet):
    """数据源管理"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = DataSource.objects.all().order_by('name')
    serializer_class = DataSourceSerializer
    update_body_serializer_class = DataSourceUpdateSerializer
    update_body_id_field = 'dataSourceId'

    def get_queryset(self):
        qs = super().get_queryset()
        # 过滤条件
        s = DataSourceQuerySerializer(data=self.request.query_params)
        s.is_valid(raise_exception=False)
        vd = getattr(s, 'validated_data', {})
        if vd.get('dataSourceName'):
            qs = qs.filter(name__icontains=vd['dataSourceName'])
        if vd.get('dbType'):
            qs = qs.filter(db_type=vd['dbType'])
        if vd.get('status'):
            qs = qs.filter(status=vd['status'])
        return qs

    def create(self, request, *args, **kwargs):
        s = DataSourceCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return self.ok(msg='创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        s = DataSourceUpdateSerializer(instance, data=request.data)
        s.is_valid(raise_exception=True)
        _password = s.validated_data.get('password', None)
        if _password and decrypt_password(_password) == instance.password:
            # 新密码与旧密码相同，不更新
            s.validated_data.pop('password', None)
        s.save()
        return self.ok(msg='更新成功')

    @action(detail=True, methods=['post'], url_path='test')
    def test_by_id(self, request, pk=None):
        """测试数据源连接（按ID）"""
        obj = self.get_object()
        db_info = {
            'type': obj.db_type,
            'host': obj.host,
            'port': obj.port,
            'username': obj.username,
            'password': obj.password,
            'database': obj.db_name,
            'params': obj.params or {},
        }
        ex = get_executor(db_info)
        try:
            ex.test_connection()
        except Exception as e:
            return self.error(msg=str(e))
        finally:
            ex.close()
        return self.ok('连接成功')

    @action(detail=False, methods=['post'], url_path='test')
    def test_by_body(self, request):
        """测试数据源连接（按请求体，不落库）"""
        if 'dataSourceId' in request.data:
            instance = DataSource.objects.get(id=request.data['dataSourceId'])
            s = DataSourceUpdateSerializer(instance, request.data)
            s.is_valid(raise_exception=True)
            vd = s.validated_data
            _password = vd.get('password', None)
            if _password and decrypt_password(_password) == instance.password:
                # 新密码与旧密码相同，不更新
                vd['password'] = instance.password
        else:
            s = DataSourceCreateSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            vd = s.validated_data
        db_info = {
            'type': vd['db_type'],
            'host': vd['host'],
            'port': vd['port'],
            'username': vd['username'],
            'password': vd['password'],
            'database': vd['db_name'],
            'params': vd.get('params') or {},
        }
        ex = get_executor(db_info)
        try:
            ex.test_connection()
        except Exception as e:
            return self.error(msg=str(e))
        finally:
            ex.close()
        return self.ok('连接成功')


# ==================== MetaTable ViewSet ====================

class MetaTableViewSet(BaseViewSet):
    """元数据表管理"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = MetaTable.objects.filter(del_flag='0').order_by('table_name')
    serializer_class = MetaTableSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # 数据源过滤
        ds_name = self.request.query_params.get('dataSourceName')
        if ds_name:
            try:
                qs = qs.filter(data_source__name__icontains=ds_name)
            except Exception:
                pass
        # 表名模糊
        tname = self.request.query_params.get('tableName')
        if tname:
            qs = qs.filter(table_name__icontains=tname)
        # 数据库名模糊
        dbname = self.request.query_params.get('databaseName')
        if dbname:
            qs = qs.filter(database__icontains=dbname)
        # 创建/修改时间范围
        def _parse_dt(val):
            from datetime import datetime
            if not val:
                return None
            try:
                val = str(val).rstrip('Z')
                return datetime.fromisoformat(val)
            except Exception:
                return None
        c_start = _parse_dt(self.request.query_params.get('createTimeStart'))
        c_end = _parse_dt(self.request.query_params.get('createTimeEnd'))
        if c_start:
            qs = qs.filter(create_time__gte=c_start)
        if c_end:
            qs = qs.filter(create_time__lte=c_end)
        u_start = _parse_dt(self.request.query_params.get('updateTimeStart'))
        u_end = _parse_dt(self.request.query_params.get('updateTimeEnd'))
        if u_start:
            qs = qs.filter(update_time__gte=u_start)
        if u_end:
            qs = qs.filter(update_time__lte=u_end)
        return qs


# ==================== MetaColumn ViewSet ====================

class MetaColumnViewSet(BaseViewSet):
    """元数据字段管理"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = MetaColumn.objects.filter(del_flag='0').select_related('table', 'data_source').order_by('table__table_name', 'order')
    serializer_class = MetaColumnSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        ds_id = self.request.query_params.get('dataSourceId')
        if ds_id:
            try:
                qs = qs.filter(data_source_id=int(ds_id))
            except Exception:
                pass
        table = self.request.query_params.get('tableName')
        if table:
            qs = qs.filter(table__table_name=table)
        database = self.request.query_params.get('databaseName')
        if database:
            qs = qs.filter(table__database=database)
        # 字段名模糊查询
        column_name = self.request.query_params.get('columnName')
        if column_name:
            qs = qs.filter(name__icontains=column_name)
        # 字段描述模糊查询
        column_comment = self.request.query_params.get('columnComment')
        if column_comment:
            qs = qs.filter(comment__icontains=column_comment)
        # 数据源名称模糊查询
        data_source_name = self.request.query_params.get('dataSourceName')
        if data_source_name:
            qs = qs.filter(data_source__name__icontains=data_source_name)
        return qs

    def list(self, request, *args, **kwargs):
        """支持大分页的列表接口"""
        # 字段查找模式可能需要返回所有数据，允许更大的 pageSize
        page_size = int(request.query_params.get('pageSize') or 10000)
        if page_size > 10000:
            page_size = 10000
        return super().list(request, *args, **kwargs)


# ==================== MetadataCollection ViewSet ====================

class MetadataCollectionViewSet(BaseViewSet):
    """元数据采集接口"""
    permission_classes = [IsAuthenticated, HasRolePermission]

    def _load_ds(self, ds_id):
        try:
            return DataSource.objects.get(pk=int(ds_id), del_flag='0')
        except Exception:
            return None

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

    def _collect_table(self, info, ds_id, table):
        # 获取表级详细信息
        tinfo = get_table_info(info, table) or {}
        comment = tinfo.get('comment') or ''
        database_name = tinfo.get('databaseName') or ''

        obj, created = MetaTable.objects.update_or_create(
            data_source_id=ds_id,
            table_name=table,
            database=database_name,
            defaults={'comment': comment, 'del_flag': '0'}
        )

        user = getattr(getattr(self, 'request', None), 'user', None)
        if user and getattr(user, 'username', None):
            if created:
                obj.create_by = user.username
                obj.save(update_fields=['create_by'])
            else:
                obj.update_by = user.username
                obj.save(update_fields=['update_by', 'update_time'])

        MetaColumn.objects.filter(data_source_id=ds_id, table=obj).delete()

        cols = get_table_schema(info, table)
        for c in cols:
            col, c_created = MetaColumn.objects.update_or_create(
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
            if user and getattr(user, 'username', None):
                if c_created:
                    col.create_by = user.username
                    col.save(update_fields=['create_by'])
                else:
                    col.update_by = user.username
                    col.save(update_fields=['update_by', 'update_time'])

    @action(detail=False, methods=['post'], url_path='databases')
    def databases(self, request):
        """获取数据库列表"""
        ds_id = request.data.get('dataSourceId')
        if not ds_id:
            return self.error('缺少参数 dataSourceId')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        try:
            dbs = get_databases(info)
            return self.raw_response({'data': dbs})
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['post'], url_path='tables')
    def tables(self, request):
        """获取数据源表列表"""
        ds_id = request.data.get('dataSourceId')
        dbname = request.data.get('databaseName')
        if not ds_id:
            return self.error('缺少参数 dataSourceId')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        if dbname:
            info['database'] = dbname
        try:
            rows = list_tables_info(info)
            return self.raw_response({'rows': rows, 'total': len(rows)})
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['post'], url_path='columns')
    def columns(self, request):
        """获取表字段列表"""
        ds_id = request.data.get('dataSourceId')
        table = request.data.get('tableName')
        dbname = request.data.get('databaseName')
        if not ds_id or not table:
            return self.error('缺少参数 dataSourceId 或 tableName')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        if dbname:
            info['database'] = dbname
        try:
            cols = get_table_schema(info, table)
            rows = [
                {
                    'order': c.get('order') or 0,
                    'name': c.get('name'),
                    'type': c.get('type') or '',
                    'notnull': bool(c.get('notnull')),
                    'default': str(c.get('default') or ''),
                    'primary': bool(c.get('primary')),
                    'comment': c.get('comment') or '',
                }
                for c in cols
            ]
            return self.raw_response({'rows': rows, 'total': len(rows)})
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['post'], url_path='collect')
    def collect(self, request):
        """同步整库采集"""
        ds_id = request.data.get('dataSourceId')
        dbname = request.data.get('databaseName')
        if not ds_id:
            return self.error('缺少参数 dataSourceId')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        if dbname:
            info['database'] = dbname
        try:
            tbls = list_tables(info)
            with transaction.atomic():
                for t in tbls:
                    self._collect_table(info, ds.id, t)
            return self.ok('采集完成')
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['post'], url_path='collect-table')
    def collect_table(self, request):
        """单表采集"""
        ds_id = request.data.get('dataSourceId')
        dbname = request.data.get('databaseName')
        table = request.data.get('tableName')
        if not ds_id or not table:
            return self.error('缺少参数 dataSourceId 或 tableName')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        info = self._build_info(ds)
        if dbname:
            info['database'] = dbname
        try:
            with transaction.atomic():
                self._collect_table(info, ds.id, table)
            return self.ok('采集完成')
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['post'], url_path='collect-async')
    def collect_async(self, request):
        """异步整库采集"""
        ds_id = request.data.get('dataSourceId')
        dbname = request.data.get('databaseName')
        if not ds_id:
            return self.error('缺少参数 dataSourceId')
        ds = self._load_ds(ds_id)
        if not ds:
            return self.not_found('数据源不存在')
        user = getattr(request, 'user', None)
        task = start_collection_task(ds_id, dbname or '', user)
        if not task:
            return self.error('启动采集任务失败，该数据源可能已有任务在运行')
        return self.data({
            'taskId': task.task_id,
            'message': '采集任务已启动'
        }, msg='任务已启动')

    @action(detail=False, methods=['get'], url_path='collect-status')
    def collect_status(self, request):
        """查询采集任务状态"""
        task_id = request.query_params.get('taskId')
        if not task_id:
            return self.error('缺少参数 taskId')
        status = get_task_status(task_id)
        if not status:
            return self.not_found('任务不存在')
        return self.data(status)

    @action(detail=False, methods=['post'], url_path='collect-cancel')
    def collect_cancel(self, request):
        """取消采集任务"""
        task_id = request.data.get('taskId')
        if not task_id:
            return self.error('缺少参数 taskId')
        success = cancel_collection_task(task_id)
        if not success:
            return self.error('任务不存在或未在运行')
        return self.ok('任务已取消')


# ==================== TableLineage ViewSet ====================

class TableLineageViewSet(BaseViewSet):
    """表血缘管理"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = TableLineage.objects.filter(del_flag='0').select_related('source_table', 'target_table').order_by('-create_time')
    serializer_class = TableLineageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        source_table_id = self.request.query_params.get('sourceTableId')
        if source_table_id:
            qs = qs.filter(source_table_id=source_table_id)
        target_table_id = self.request.query_params.get('targetTableId')
        if target_table_id:
            qs = qs.filter(target_table_id=target_table_id)
        source_table_name = self.request.query_params.get('sourceTableName')
        if source_table_name:
            qs = qs.filter(source_table__table_name__icontains=source_table_name)
        target_table_name = self.request.query_params.get('targetTableName')
        if target_table_name:
            qs = qs.filter(target_table__table_name__icontains=target_table_name)
        lineage_type = self.request.query_params.get('lineageType')
        if lineage_type:
            qs = qs.filter(lineage_type=lineage_type)
        return qs

    def create(self, request, *args, **kwargs):
        s = TableLineageCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd = s.validated_data

        # 验证表存在
        try:
            source_table = MetaTable.objects.get(id=vd['sourceTableId'], del_flag='0')
            target_table = MetaTable.objects.get(id=vd['targetTableId'], del_flag='0')
        except MetaTable.DoesNotExist:
            return self.error('源表或目标表不存在')

        # 检查是否已存在相同关系
        existing = TableLineage.objects.filter(
            source_table=source_table,
            target_table=target_table,
            lineage_type=vd.get('lineageType', 'upstream'),
            del_flag='0'
        ).first()
        if existing:
            return self.error('该血缘关系已存在')

        lineage = TableLineage.objects.create(
            source_table=source_table,
            target_table=target_table,
            lineage_type=vd.get('lineageType', 'upstream'),
            description=vd.get('description', ''),
            create_by=request.user.username if hasattr(request.user, 'username') else '',
            update_by=request.user.username if hasattr(request.user, 'username') else ''
        )
        return self.data({'id': lineage.id}, msg='创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        s = TableLineageUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        vd = s.validated_data

        if 'sourceTableId' in vd:
            try:
                instance.source_table = MetaTable.objects.get(id=vd['sourceTableId'], del_flag='0')
            except MetaTable.DoesNotExist:
                return self.error('源表不存在')

        if 'targetTableId' in vd:
            try:
                instance.target_table = MetaTable.objects.get(id=vd['targetTableId'], del_flag='0')
            except MetaTable.DoesNotExist:
                return self.error('目标表不存在')

        if 'lineageType' in vd:
            instance.lineage_type = vd['lineageType']

        if 'description' in vd:
            instance.description = vd['description']

        instance.update_by = request.user.username if hasattr(request.user, 'username') else ''
        instance.save()

        return self.ok(msg='更新成功')

    @action(detail=False, methods=['get'], url_path='upstream')
    def upstream(self, request):
        """查询表的上游血缘"""
        table_id = request.query_params.get('tableId')
        table_name = request.query_params.get('tableName')
        depth = int(request.query_params.get('depth', 1))

        if not table_id and not table_name:
            return self.error('缺少参数 tableId 或 tableName')

        try:
            if table_id:
                table = MetaTable.objects.get(id=table_id, del_flag='0')
            else:
                table = MetaTable.objects.filter(table_name=table_name, del_flag='0').first()
                if not table:
                    return self.error('表不存在')

            result = self._get_upstream_lineage(table, depth)
            return self.data(result)
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['get'], url_path='downstream')
    def downstream(self, request):
        """查询表的下游血缘"""
        table_id = request.query_params.get('tableId')
        table_name = request.query_params.get('tableName')
        depth = int(request.query_params.get('depth', 1))

        if not table_id and not table_name:
            return self.error('缺少参数 tableId 或 tableName')

        try:
            if table_id:
                table = MetaTable.objects.get(id=table_id, del_flag='0')
            else:
                table = MetaTable.objects.filter(table_name=table_name, del_flag='0').first()
                if not table:
                    return self.error('表不存在')

            result = self._get_downstream_lineage(table, depth)
            return self.data(result)
        except Exception as e:
            return self.error(str(e))

    @action(detail=False, methods=['get'], url_path='graph')
    def graph(self, request):
        """生成血缘关系图"""
        table_id = request.query_params.get('tableId')
        table_name = request.query_params.get('tableName')
        depth = int(request.query_params.get('depth', 2))

        if not table_id and not table_name:
            return self.error('缺少参数 tableId 或 tableName')

        try:
            if table_id:
                table = MetaTable.objects.get(id=table_id, del_flag='0')
            else:
                table = MetaTable.objects.filter(table_name=table_name, del_flag='0').first()
                if not table:
                    return self.error('表不存在')

            nodes, edges = self._build_lineage_graph(table, depth)
            return self.data({'nodes': nodes, 'edges': edges})
        except Exception as e:
            return self.error(str(e))

    def _get_upstream_lineage(self, table, depth, visited=None):
        """递归获取上游血缘"""
        if visited is None:
            visited = set()
        if depth <= 0 or table.id in visited:
            return []

        visited.add(table.id)
        result = []

        # 查找所有以该表为目标表的上游关系
        upstreams = TableLineage.objects.filter(
            target_table=table,
            lineage_type='upstream',
            del_flag='0'
        ).select_related('source_table')

        for lineage in upstreams:
            source_table = lineage.source_table
            result.append({
                'tableId': source_table.id,
                'tableName': source_table.table_name,
                'databaseName': source_table.database,
                'dataSourceId': source_table.data_source_id,
                'description': lineage.description,
                'level': depth
            })
            # 递归查找更上游
            result.extend(self._get_upstream_lineage(source_table, depth - 1, visited))

        return result

    def _get_downstream_lineage(self, table, depth, visited=None):
        """递归获取下游血缘"""
        if visited is None:
            visited = set()
        if depth <= 0 or table.id in visited:
            return []

        visited.add(table.id)
        result = []

        # 查找所有以该表为源表的下游关系
        downstreams = TableLineage.objects.filter(
            source_table=table,
            lineage_type='downstream',
            del_flag='0'
        ).select_related('target_table')

        for lineage in downstreams:
            target_table = lineage.target_table
            result.append({
                'tableId': target_table.id,
                'tableName': target_table.table_name,
                'databaseName': target_table.database,
                'dataSourceId': target_table.data_source_id,
                'description': lineage.description,
                'level': depth
            })
            # 递归查找更下游
            result.extend(self._get_downstream_lineage(target_table, depth - 1, visited))

        return result

    def _build_lineage_graph(self, table, depth):
        """构建血缘关系图"""
        nodes = {}
        edges = []
        visited = set()

        def add_node(t):
            if t.id not in nodes:
                nodes[t.id] = {
                    'id': t.id,
                    'tableName': t.table_name,
                    'databaseName': t.database,
                    'dataSourceId': t.data_source_id,
                    'comment': t.comment
                }

        def traverse(t, current_depth):
            if current_depth <= 0 or t.id in visited:
                return
            visited.add(t.id)
            add_node(t)

            # 上游
            upstreams = TableLineage.objects.filter(
                target_table=t,
                lineage_type='upstream',
                del_flag='0'
            ).select_related('source_table')

            for lineage in upstreams:
                source_table = lineage.source_table
                add_node(source_table)
                edges.append({
                    'source': source_table.id,
                    'target': t.id,
                    'type': 'upstream',
                    'description': lineage.description
                })
                traverse(source_table, current_depth - 1)

            # 下游
            downstreams = TableLineage.objects.filter(
                source_table=t,
                lineage_type='downstream',
                del_flag='0'
            ).select_related('target_table')

            for lineage in downstreams:
                target_table = lineage.target_table
                add_node(target_table)
                edges.append({
                    'source': t.id,
                    'target': target_table.id,
                    'type': 'downstream',
                    'description': lineage.description
                })
                traverse(target_table, current_depth - 1)

        traverse(table, depth)

        return list(nodes.values()), edges
