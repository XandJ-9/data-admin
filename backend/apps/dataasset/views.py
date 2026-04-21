import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db import transaction
from django.db.models import OuterRef, Prefetch, Q, Subquery
from django.utils import timezone
from apps.system.views.core import BaseViewSet
from apps.system.common import audit_log
from apps.system.permission import HasRolePermission
from apps.dbutils import list_tables, get_table_schema, list_tables_info, get_databases

from apps.datasource.models import DataSource
from .models import (
    AssetNamespace,
    DataAsset,
    DataAssetColumn,
    MetaTable,
    MetaColumn,
    MetaCollectionTask,
    TableLineage,
)
from .serializers import (
    AssetNamespaceSerializer,
    AssetNamespaceQuerySerializer,
    CanonicalMetaColumnSerializer,
    CanonicalMetaTableSerializer,
    DataAssetColumnQuerySerializer,
    DataAssetColumnSerializer,
    DataAssetDetailSerializer,
    DataAssetQuerySerializer,
    DataAssetSerializer,
    MetaTableSerializer, MetaTableQuerySerializer,
    MetaColumnSerializer, MetaColumnQuerySerializer,
    MetaCollectionTaskSerializer, MetaCollectionTaskCreateSerializer,
    TableLineageSerializer, TableLineageCreateSerializer, TableLineageUpdateSerializer,
    TableLineageQuerySerializer, TableLineageGraphSerializer
)
from .collectors import create_collection_task, start_collection_task, cancel_collection_task, get_task_status
from .services import collect_table_metadata, sync_standard_asset_from_meta_table
from .utils import sanitize_collection_error_message

logger = logging.getLogger(__name__)


def _parse_datetime_param(value):
    from datetime import datetime

    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).rstrip('Z'))
    except Exception:
        return None


def _filter_canonical_database(queryset, database_name, namespace_prefix='namespace__'):
    if not database_name:
        return queryset
    return queryset.filter(
        Q(**{f'{namespace_prefix}display_name__icontains': database_name})
        | Q(**{f'{namespace_prefix}catalog_name__icontains': database_name})
        | Q(**{f'{namespace_prefix}schema_name__icontains': database_name})
    )


class AssetNamespaceViewSet(BaseViewSet):
    """规范资产命名空间查询接口"""

    permission_classes = [IsAuthenticated, HasRolePermission]
    http_method_names = ['get', 'head', 'options']
    queryset = AssetNamespace.objects.filter(del_flag='0').select_related('data_source').order_by('data_source_id', 'catalog_name', 'schema_name')
    serializer_class = AssetNamespaceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        data_source_id = self.request.query_params.get('dataSourceId')
        if data_source_id:
            try:
                qs = qs.filter(data_source_id=int(data_source_id))
            except Exception:
                pass
        data_source_name = self.request.query_params.get('dataSourceName')
        if data_source_name:
            qs = qs.filter(data_source__name__icontains=data_source_name)
        environment = self.request.query_params.get('environment')
        if environment:
            qs = qs.filter(environment=environment)
        catalog_name = self.request.query_params.get('catalogName')
        if catalog_name:
            qs = qs.filter(catalog_name__icontains=catalog_name)
        schema_name = self.request.query_params.get('schemaName')
        if schema_name:
            qs = qs.filter(schema_name__icontains=schema_name)
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(
                Q(display_name__icontains=keyword)
                | Q(namespace_key__icontains=keyword)
                | Q(catalog_name__icontains=keyword)
                | Q(schema_name__icontains=keyword)
            )
        return qs


class DataAssetViewSet(BaseViewSet):
    """规范数据资产查询接口"""

    permission_classes = [IsAuthenticated, HasRolePermission]
    http_method_names = ['get', 'head', 'options']
    queryset = DataAsset.objects.filter(del_flag='0').select_related('namespace', 'namespace__data_source').prefetch_related(
        Prefetch(
            'asset_columns',
            queryset=DataAssetColumn.objects.filter(del_flag='0').order_by('ordinal_position', 'column_name'),
        )
    ).order_by('object_name')
    serializer_class = DataAssetSerializer
    retrieve_serializer_class = DataAssetDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        data_source_id = self.request.query_params.get('dataSourceId')
        if data_source_id:
            try:
                qs = qs.filter(namespace__data_source_id=int(data_source_id))
            except Exception:
                pass
        data_source_name = self.request.query_params.get('dataSourceName')
        if data_source_name:
            qs = qs.filter(namespace__data_source__name__icontains=data_source_name)
        namespace_id = self.request.query_params.get('namespaceId')
        if namespace_id:
            try:
                qs = qs.filter(namespace_id=int(namespace_id))
            except Exception:
                pass
        asset_type = self.request.query_params.get('assetType')
        if asset_type:
            qs = qs.filter(asset_type=asset_type)
        object_name = self.request.query_params.get('objectName')
        if object_name:
            qs = qs.filter(object_name__icontains=object_name)
        database_name = self.request.query_params.get('databaseName')
        if database_name:
            qs = _filter_canonical_database(qs, database_name)
        catalog_name = self.request.query_params.get('catalogName')
        if catalog_name:
            qs = qs.filter(namespace__catalog_name__icontains=catalog_name)
        schema_name = self.request.query_params.get('schemaName')
        if schema_name:
            qs = qs.filter(namespace__schema_name__icontains=schema_name)
        asset_category = self.request.query_params.get('assetCategory')
        if asset_category:
            qs = qs.filter(asset_category=asset_category)
        warehouse_layer = self.request.query_params.get('warehouseLayer')
        if warehouse_layer:
            qs = qs.filter(warehouse_layer=warehouse_layer)
        business_domain = self.request.query_params.get('businessDomain')
        if business_domain:
            qs = qs.filter(business_domain__icontains=business_domain)
        subject_area = self.request.query_params.get('subjectArea')
        if subject_area:
            qs = qs.filter(subject_area__icontains=subject_area)
        owner = self.request.query_params.get('owner')
        if owner:
            qs = qs.filter(owner__icontains=owner)
        lifecycle_status = self.request.query_params.get('lifecycleStatus')
        if lifecycle_status:
            qs = qs.filter(lifecycle_status=lifecycle_status)
        security_level = self.request.query_params.get('securityLevel')
        if security_level:
            qs = qs.filter(security_level=security_level)
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(
                Q(object_name__icontains=keyword)
                | Q(display_name__icontains=keyword)
                | Q(comment__icontains=keyword)
                | Q(qualified_name__icontains=keyword)
            )
        return qs


class DataAssetColumnViewSet(BaseViewSet):
    """规范数据资产字段查询接口"""

    permission_classes = [IsAuthenticated, HasRolePermission]
    http_method_names = ['get', 'head', 'options']
    queryset = DataAssetColumn.objects.filter(del_flag='0').select_related(
        'asset', 'asset__namespace', 'asset__namespace__data_source'
    ).order_by('asset__object_name', 'ordinal_position', 'column_name')
    serializer_class = DataAssetColumnSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        data_source_id = self.request.query_params.get('dataSourceId')
        if data_source_id:
            try:
                qs = qs.filter(asset__namespace__data_source_id=int(data_source_id))
            except Exception:
                pass
        data_source_name = self.request.query_params.get('dataSourceName')
        if data_source_name:
            qs = qs.filter(asset__namespace__data_source__name__icontains=data_source_name)
        asset_id = self.request.query_params.get('assetId')
        if asset_id:
            try:
                qs = qs.filter(asset_id=int(asset_id))
            except Exception:
                pass
        table_id = self.request.query_params.get('tableId')
        if table_id:
            try:
                qs = qs.filter(asset__legacy_meta_table_id=int(table_id))
            except Exception:
                pass
        table_name = self.request.query_params.get('tableName')
        if table_name:
            qs = qs.filter(asset__object_name=table_name)
        database_name = self.request.query_params.get('databaseName')
        if database_name:
            qs = _filter_canonical_database(qs, database_name, namespace_prefix='asset__namespace__')
        column_name = self.request.query_params.get('columnName')
        if column_name:
            qs = qs.filter(column_name__icontains=column_name)
        column_comment = self.request.query_params.get('columnComment')
        if column_comment:
            qs = qs.filter(comment__icontains=column_comment)
        business_term = self.request.query_params.get('businessTerm')
        if business_term:
            qs = qs.filter(business_term__icontains=business_term)
        warehouse_role = self.request.query_params.get('warehouseRole')
        if warehouse_role:
            qs = qs.filter(warehouse_role=warehouse_role)
        security_level = self.request.query_params.get('securityLevel')
        if security_level:
            qs = qs.filter(security_level=security_level)
        standard_code = self.request.query_params.get('standardCode')
        if standard_code:
            qs = qs.filter(standard_code__icontains=standard_code)
        return qs


# ==================== MetaTable ViewSet ====================

class MetaTableViewSet(BaseViewSet):
    """元数据表管理"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = MetaTable.objects.filter(del_flag='0').select_related('data_source').order_by('table_name')
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
        asset_category = self.request.query_params.get('assetCategory')
        if asset_category:
            qs = qs.filter(asset_category=asset_category)
        warehouse_layer = self.request.query_params.get('warehouseLayer')
        if warehouse_layer:
            qs = qs.filter(warehouse_layer=warehouse_layer)
        business_domain = self.request.query_params.get('businessDomain')
        if business_domain:
            qs = qs.filter(business_domain__icontains=business_domain)
        subject_area = self.request.query_params.get('subjectArea')
        if subject_area:
            qs = qs.filter(subject_area__icontains=subject_area)
        owner = self.request.query_params.get('owner')
        if owner:
            qs = qs.filter(owner__icontains=owner)
        lifecycle_status = self.request.query_params.get('lifecycleStatus')
        if lifecycle_status:
            qs = qs.filter(lifecycle_status=lifecycle_status)
        security_level = self.request.query_params.get('securityLevel')
        if security_level:
            qs = qs.filter(security_level=security_level)
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

    def _get_canonical_queryset(self):
        legacy_meta_table_qs = MetaTable.objects.filter(pk=OuterRef('legacy_meta_table_id'))
        qs = DataAsset.objects.filter(del_flag='0', legacy_meta_table_id__isnull=False).select_related('namespace', 'namespace__data_source').annotate(
            legacy_create_by=Subquery(legacy_meta_table_qs.values('create_by')[:1]),
            legacy_create_time=Subquery(legacy_meta_table_qs.values('create_time')[:1]),
            legacy_update_by=Subquery(legacy_meta_table_qs.values('update_by')[:1]),
            legacy_update_time=Subquery(legacy_meta_table_qs.values('update_time')[:1]),
        ).order_by('object_name')
        data_source_id = self.request.query_params.get('dataSourceId')
        if data_source_id:
            try:
                qs = qs.filter(namespace__data_source_id=int(data_source_id))
            except Exception:
                pass
        data_source_name = self.request.query_params.get('dataSourceName')
        if data_source_name:
            qs = qs.filter(namespace__data_source__name__icontains=data_source_name)
        table_name = self.request.query_params.get('tableName')
        if table_name:
            qs = qs.filter(object_name__icontains=table_name)
        database_name = self.request.query_params.get('databaseName')
        if database_name:
            qs = _filter_canonical_database(qs, database_name)
        asset_category = self.request.query_params.get('assetCategory')
        if asset_category:
            qs = qs.filter(asset_category=asset_category)
        warehouse_layer = self.request.query_params.get('warehouseLayer')
        if warehouse_layer:
            qs = qs.filter(warehouse_layer=warehouse_layer)
        business_domain = self.request.query_params.get('businessDomain')
        if business_domain:
            qs = qs.filter(business_domain__icontains=business_domain)
        subject_area = self.request.query_params.get('subjectArea')
        if subject_area:
            qs = qs.filter(subject_area__icontains=subject_area)
        owner = self.request.query_params.get('owner')
        if owner:
            qs = qs.filter(owner__icontains=owner)
        lifecycle_status = self.request.query_params.get('lifecycleStatus')
        if lifecycle_status:
            qs = qs.filter(lifecycle_status=lifecycle_status)
        security_level = self.request.query_params.get('securityLevel')
        if security_level:
            qs = qs.filter(security_level=security_level)

        c_start = _parse_datetime_param(self.request.query_params.get('createTimeStart'))
        c_end = _parse_datetime_param(self.request.query_params.get('createTimeEnd'))
        u_start = _parse_datetime_param(self.request.query_params.get('updateTimeStart'))
        u_end = _parse_datetime_param(self.request.query_params.get('updateTimeEnd'))
        if any([c_start, c_end, u_start, u_end]):
            legacy_qs = MetaTable.objects.filter(del_flag='0')
            if c_start:
                legacy_qs = legacy_qs.filter(create_time__gte=c_start)
            if c_end:
                legacy_qs = legacy_qs.filter(create_time__lte=c_end)
            if u_start:
                legacy_qs = legacy_qs.filter(update_time__gte=u_start)
            if u_end:
                legacy_qs = legacy_qs.filter(update_time__lte=u_end)
            qs = qs.filter(legacy_meta_table_id__in=legacy_qs.values('id'))
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self._get_canonical_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CanonicalMetaTableSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CanonicalMetaTableSerializer(queryset, many=True)
        return self.raw_response({'total': len(serializer.data), 'rows': serializer.data, 'code': 200, 'msg': '操作成功'})

    def retrieve(self, request, *args, **kwargs):
        lookup_value = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field)
        queryset = self._get_canonical_queryset()
        instance = queryset.filter(legacy_meta_table_id=lookup_value).first()
        if not instance:
            return self.not_found('资源不存在')
        self.check_object_permissions(request, instance)
        serializer = CanonicalMetaTableSerializer(instance)
        return self.data(serializer.data)

    @audit_log
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = MetaTableSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            sync_standard_asset_from_meta_table(serializer.instance, user=request.user)
        return self.ok()

    @audit_log
    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = MetaTableSerializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if 'dataSourceId' in request.data:
                MetaColumn.objects.filter(table=serializer.instance).update(data_source_id=serializer.instance.data_source_id)
            sync_standard_asset_from_meta_table(serializer.instance, user=request.user)
        return self.ok()

    @audit_log
    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            legacy_ids = [obj.id for obj in instance] if isinstance(instance, list) else [instance.id]
            response = super().destroy(request, *args, **kwargs)
            DataAsset.objects.filter(legacy_meta_table_id__in=legacy_ids).delete()
        return response


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
        business_term = self.request.query_params.get('businessTerm')
        if business_term:
            qs = qs.filter(business_term__icontains=business_term)
        warehouse_role = self.request.query_params.get('warehouseRole')
        if warehouse_role:
            qs = qs.filter(warehouse_role=warehouse_role)
        security_level = self.request.query_params.get('securityLevel')
        if security_level:
            qs = qs.filter(security_level=security_level)
        standard_code = self.request.query_params.get('standardCode')
        if standard_code:
            qs = qs.filter(standard_code__icontains=standard_code)
        # 数据源名称模糊查询
        data_source_name = self.request.query_params.get('dataSourceName')
        if data_source_name:
            qs = qs.filter(data_source__name__icontains=data_source_name)
        return qs

    def list(self, request, *args, **kwargs):
        """支持大分页的列表接口"""
        queryset = self._get_canonical_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CanonicalMetaColumnSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CanonicalMetaColumnSerializer(queryset, many=True)
        return self.raw_response({'total': len(serializer.data), 'rows': serializer.data, 'code': 200, 'msg': '操作成功'})

    def _get_canonical_queryset(self):
        legacy_meta_column_qs = MetaColumn.objects.filter(pk=OuterRef('legacy_meta_column_id'))
        qs = DataAssetColumn.objects.filter(
            del_flag='0',
            legacy_meta_column_id__isnull=False,
            asset__legacy_meta_table_id__isnull=False,
        ).select_related(
            'asset', 'asset__namespace', 'asset__namespace__data_source'
        ).annotate(
            legacy_create_by=Subquery(legacy_meta_column_qs.values('create_by')[:1]),
            legacy_update_by=Subquery(legacy_meta_column_qs.values('update_by')[:1]),
        ).order_by('asset__object_name', 'ordinal_position', 'column_name')
        data_source_id = self.request.query_params.get('dataSourceId')
        if data_source_id:
            try:
                qs = qs.filter(asset__namespace__data_source_id=int(data_source_id))
            except Exception:
                pass
        table_name = self.request.query_params.get('tableName')
        if table_name:
            qs = qs.filter(asset__object_name=table_name)
        table_id = self.request.query_params.get('tableId')
        if table_id:
            try:
                qs = qs.filter(asset__legacy_meta_table_id=int(table_id))
            except Exception:
                pass
        database_name = self.request.query_params.get('databaseName')
        if database_name:
            qs = _filter_canonical_database(qs, database_name, namespace_prefix='asset__namespace__')
        column_name = self.request.query_params.get('columnName')
        if column_name:
            qs = qs.filter(column_name__icontains=column_name)
        column_comment = self.request.query_params.get('columnComment')
        if column_comment:
            qs = qs.filter(comment__icontains=column_comment)
        business_term = self.request.query_params.get('businessTerm')
        if business_term:
            qs = qs.filter(business_term__icontains=business_term)
        warehouse_role = self.request.query_params.get('warehouseRole')
        if warehouse_role:
            qs = qs.filter(warehouse_role=warehouse_role)
        security_level = self.request.query_params.get('securityLevel')
        if security_level:
            qs = qs.filter(security_level=security_level)
        standard_code = self.request.query_params.get('standardCode')
        if standard_code:
            qs = qs.filter(standard_code__icontains=standard_code)
        data_source_name = self.request.query_params.get('dataSourceName')
        if data_source_name:
            qs = qs.filter(asset__namespace__data_source__name__icontains=data_source_name)
        return qs

    def retrieve(self, request, *args, **kwargs):
        lookup_value = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field)
        queryset = self._get_canonical_queryset()
        instance = queryset.filter(legacy_meta_column_id=lookup_value).first()
        if not instance:
            return self.not_found('资源不存在')
        self.check_object_permissions(request, instance)
        serializer = CanonicalMetaColumnSerializer(instance)
        return self.data(serializer.data)

    @audit_log
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            table_id = request.data.get('tableId')
            column_name = request.data.get('columnName')
            if not table_id or not column_name:
                return self.error('缺少参数 tableId 或 columnName')
            table = MetaTable.objects.filter(pk=table_id, del_flag='0').first()
            if not table:
                return self.not_found('元数据表不存在')

            column, created = MetaColumn.objects.update_or_create(
                data_source_id=table.data_source_id,
                table=table,
                name=column_name,
                defaults={
                    'order': request.data.get('columnIndex') or 0,
                    'type': request.data.get('dataType') or '',
                    'notnull': not bool(request.data.get('isNullable')),
                    'default': str(request.data.get('defaultValue') or ''),
                    'primary': bool(request.data.get('isPrimary')),
                    'comment': request.data.get('columnComment') or '',
                    'business_term': request.data.get('businessTerm') or '',
                    'warehouse_role': request.data.get('warehouseRole') or '',
                    'security_level': request.data.get('securityLevel') or 'internal',
                    'standard_code': request.data.get('standardCode') or '',
                    'metric_unit': request.data.get('metricUnit') or '',
                    'del_flag': '0',
                },
            )
            username = request.user.username if hasattr(request.user, 'username') else ''
            if created and username:
                column.create_by = username
            if username:
                column.update_by = username
            if created and username:
                column.save(update_fields=['create_by', 'update_by'])
            elif username:
                column.save(update_fields=['update_by'])
            else:
                column.save()
            sync_standard_asset_from_meta_table(column.table, user=request.user)
        return self.ok()

    @audit_log
    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            if isinstance(instance, list):
                return self.error('字段更新仅支持单条记录')

            original_table = instance.table
            table_id = request.data.get('tableId')
            if table_id:
                table = MetaTable.objects.filter(pk=table_id, del_flag='0').first()
                if not table:
                    return self.not_found('元数据表不存在')
                instance.table = table
            instance.data_source_id = instance.table.data_source_id
            if request.data.get('columnIndex') is not None:
                instance.order = request.data.get('columnIndex') or 0
            if request.data.get('columnName'):
                instance.name = request.data.get('columnName')
            if request.data.get('dataType') is not None:
                instance.type = request.data.get('dataType') or ''
            if 'isNullable' in request.data:
                instance.notnull = not bool(request.data.get('isNullable'))
            if 'defaultValue' in request.data:
                instance.default = str(request.data.get('defaultValue') or '')
            if 'isPrimary' in request.data:
                instance.primary = bool(request.data.get('isPrimary'))
            if 'columnComment' in request.data:
                instance.comment = request.data.get('columnComment') or ''
            if 'businessTerm' in request.data:
                instance.business_term = request.data.get('businessTerm') or ''
            if 'warehouseRole' in request.data:
                instance.warehouse_role = request.data.get('warehouseRole') or ''
            if 'securityLevel' in request.data:
                instance.security_level = request.data.get('securityLevel') or 'internal'
            if 'standardCode' in request.data:
                instance.standard_code = request.data.get('standardCode') or ''
            if 'metricUnit' in request.data:
                instance.metric_unit = request.data.get('metricUnit') or ''
            if hasattr(request.user, 'username'):
                instance.update_by = request.user.username
            instance.save()
            if original_table.id != instance.table_id:
                sync_standard_asset_from_meta_table(original_table, user=request.user)
            sync_standard_asset_from_meta_table(instance.table, user=request.user)
        return self.ok()

    @audit_log
    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            table_ids = [obj.table_id for obj in instance] if isinstance(instance, list) else [instance.table_id]
            response = super().destroy(request, *args, **kwargs)
            for table_id in set(table_ids):
                meta_table = MetaTable.objects.filter(pk=table_id, del_flag='0').first()
                if meta_table:
                    sync_standard_asset_from_meta_table(meta_table, user=request.user)
        return response


# ==================== MetadataCollection ViewSet ====================

class MetadataCollectionViewSet(BaseViewSet):
    """元数据采集接口"""
    permission_classes = [IsAuthenticated, HasRolePermission]
    queryset = MetaCollectionTask.objects.filter(del_flag='0').select_related('data_source').order_by('-create_time')
    serializer_class = MetaCollectionTaskSerializer
    lookup_field = 'id'

    def _raise_if_task_cancelled(self, task):
        task.refresh_from_db(fields=['status'])
        if task.status == 'cancelled':
            raise InterruptedError('采集任务已取消')

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
        user = getattr(getattr(self, 'request', None), 'user', None)
        collect_table_metadata(info, ds_id, table, user=user)

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
            logger.exception('获取数据库列表失败: data_source_id=%s, error=%s', ds_id, e)
            return self.error(sanitize_collection_error_message(e))

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
            logger.exception('获取表列表失败: data_source_id=%s, database=%s, error=%s', ds_id, dbname or '', e)
            return self.error(sanitize_collection_error_message(e))

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
            logger.exception(
                '获取字段列表失败: data_source_id=%s, database=%s, table=%s, error=%s',
                ds_id,
                dbname or '',
                table,
                e,
            )
            return self.error(sanitize_collection_error_message(e))

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
        user = getattr(request, 'user', None)
        task = create_collection_task(ds.id, dbname or '', user)
        if not task:
            return self.error('启动采集任务失败，该数据源可能已有任务在运行')
        try:
            tbls = list_tables(info)
            updated = MetaCollectionTask.objects.filter(pk=task.pk, status='pending').update(
                status='running',
                started_at=timezone.now(),
                total_tables=len(tbls),
            )
            task.refresh_from_db(fields=['status', 'started_at', 'total_tables'])
            if not updated:
                self._raise_if_task_cancelled(task)
            for t in tbls:
                self._raise_if_task_cancelled(task)
                task.current_table = t
                try:
                    self._collect_table(info, ds.id, t)
                    task.collected_tables += 1
                except Exception as exc:
                    logger.exception(
                        '同步采集单表失败: data_source_id=%s, database=%s, table=%s, error=%s',
                        ds.id,
                        dbname or '',
                        t,
                        exc,
                    )
                    task.failed_tables += 1
                    task.error_message = '部分表采集失败，请查看服务端日志'
                self._raise_if_task_cancelled(task)
                task.progress = int((task.collected_tables / len(tbls)) * 100) if tbls else 100
                task.save(update_fields=['current_table', 'collected_tables', 'failed_tables', 'progress', 'error_message'])
            task.refresh_from_db(fields=['status'])
            if task.status != 'cancelled':
                task.status = 'completed' if task.failed_tables == 0 else 'failed'
                task.progress = 100
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'progress', 'completed_at'])
            if task.failed_tables:
                return self.error(f'采集完成，但有 {task.failed_tables} 张表失败')
            return self.ok('采集完成')
        except InterruptedError as e:
            task.completed_at = timezone.now()
            task.save(update_fields=['completed_at'])
            return self.error(str(e))
        except Exception as e:
            task.refresh_from_db(fields=['status'])
            if task.status != 'cancelled':
                task.status = 'failed'
                task.error_message = '采集失败，请查看服务端日志'
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'error_message', 'completed_at'])
            logger.exception('同步整库采集失败: data_source_id=%s, database=%s, error=%s', ds.id, dbname or '', e)
            return self.error(sanitize_collection_error_message(e))

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
        user = getattr(request, 'user', None)
        task = create_collection_task(ds.id, dbname or '', user)
        if not task:
            return self.error('启动采集任务失败，该数据源可能已有任务在运行')
        try:
            updated = MetaCollectionTask.objects.filter(pk=task.pk, status='pending').update(
                status='running',
                started_at=timezone.now(),
                total_tables=1,
                current_table=table,
            )
            task.refresh_from_db(fields=['status', 'started_at', 'total_tables', 'current_table'])
            if not updated:
                self._raise_if_task_cancelled(task)
            self._raise_if_task_cancelled(task)
            self._collect_table(info, ds.id, table)
            self._raise_if_task_cancelled(task)
            task.refresh_from_db(fields=['status'])
            if task.status != 'cancelled':
                task.status = 'completed'
                task.collected_tables = 1
                task.progress = 100
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'collected_tables', 'progress', 'completed_at'])
            return self.ok('采集完成')
        except InterruptedError as e:
            task.completed_at = timezone.now()
            task.save(update_fields=['completed_at'])
            return self.error(str(e))
        except Exception as e:
            task.refresh_from_db(fields=['status'])
            if task.status != 'cancelled':
                task.status = 'failed'
                task.error_message = '采集失败，请查看服务端日志'
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'error_message', 'completed_at'])
            logger.exception(
                '同步单表采集失败: data_source_id=%s, database=%s, table=%s, error=%s',
                ds.id,
                dbname or '',
                table,
                e,
            )
            return self.error(sanitize_collection_error_message(e))

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
