from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from apps.dataservice.models import QueryLog, InterfaceInfo, InterfaceField, ReportInfo, ReportInterfaceRelation


def _validate_total_sql_requirement(is_total_value, total_sql_value):
    if is_total_value == '1' and not str(total_sql_value or '').strip():
        raise serializers.ValidationError('启用合计时必须填写合计SQL')


def _normalize_interface_ids(interface_ids):
    normalized = []
    seen = set()
    for interface_id in interface_ids or []:
        normalized_id = int(interface_id)
        if normalized_id in seen:
            continue
        seen.add(normalized_id)
        normalized.append(normalized_id)
    return normalized


class DataServiceQuerySerializer(serializers.Serializer):
    dataSourceId = serializers.IntegerField()
    sql = serializers.CharField()
    params = serializers.DictField(child=serializers.CharField(allow_blank=True), required=False, allow_empty=True, allow_null=True)
    pageSize = serializers.IntegerField(required=False, min_value=1, default=50)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)


class InterfacePublishSerializer(serializers.Serializer):
    dataSourceId = serializers.IntegerField()
    sql = serializers.CharField()
    params = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        allow_empty=True,
        allow_null=True,
    )
    outputColumns = serializers.ListField(child=serializers.CharField(allow_blank=True), allow_empty=False)
    interfaceName = serializers.CharField(max_length=255)
    interfaceCode = serializers.RegexField(r'^[A-Za-z0-9_-]+$', max_length=255)
    interfaceDesc = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    isTotal = serializers.ChoiceField(required=False, choices=['0', '1'], default='0')
    totalSql = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    isPaging = serializers.ChoiceField(required=False, choices=['0', '1'], default='1')
    enable = serializers.ChoiceField(required=False, choices=['0', '1'], default='1')

    def validate(self, attrs):
        _validate_total_sql_requirement(attrs.get('isTotal', '0'), attrs.get('totalSql'))
        return attrs


class InterfaceChangeStatusSerializer(serializers.Serializer):
    interfaceId = serializers.IntegerField()
    enable = serializers.ChoiceField(choices=['0', '1'])


class DataServiceQueryLogSerializer(BaseModelSerializer):
    logId = serializers.IntegerField(source='id')
    dataSourceName = serializers.CharField(source='data_source.name')
    userName = serializers.CharField(source='username')
    sqlText = serializers.CharField(source='sql_text')
    status = serializers.CharField()
    durationMs = serializers.IntegerField(source='duration_ms')
    errorMsg = serializers.CharField(source='error_msg', required=False, allow_blank=True)
    queryType = serializers.CharField(source='query_type', required=False, allow_blank=True)

    class Meta:
        model = QueryLog
        fields = ['logId', 'dataSourceName', 'userName', 'sqlText', 'status', 'durationMs', 'errorMsg', 'queryType']


class InterfaceInfoSerializer(BaseModelSerializer):
    interfaceId = serializers.IntegerField(source='id', read_only=True)
    reportId = serializers.IntegerField(source='report_id', required=False, allow_null=True)
    interfaceName = serializers.CharField(source='interface_name')
    interfaceCode = serializers.CharField(source='interface_code')
    interfaceDesc = serializers.CharField(source='interface_desc', required=False, allow_blank=True, allow_null=True)
    interfaceDbType = serializers.CharField(source='interface_db_type')
    interfaceDbName = serializers.CharField(source='interface_db_name')
    interfaceSql = serializers.CharField(source='interface_sql', required=False, allow_blank=True)
    isTotal = serializers.CharField(source='is_total')
    totalSql = serializers.CharField(source='total_sql', required=False, allow_blank=True)
    isPaging = serializers.CharField(source='is_paging')
    isDateOption = serializers.CharField(source='is_date_option')
    isSecondTable = serializers.CharField(source='is_second_table')
    isLoginVisit = serializers.CharField(source='is_login_visit')
    alarmType = serializers.CharField(source='alarm_type')
    userName = serializers.CharField(source='user_name', required=False, allow_blank=True, allow_null=True)
    interfaceDatasource = serializers.IntegerField(source='interface_datasource', required=False, allow_null=True)
    reportName = serializers.CharField(source='report_name', required=False, allow_blank=True, allow_null=True)
    reportCode = serializers.CharField(source='report_code', required=False, allow_blank=True, allow_null=True)
    moduleName = serializers.CharField(source='module_name', required=False, allow_blank=True, allow_null=True)
    platformName = serializers.CharField(source='platform_name', required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = InterfaceInfo
        fields = [
            'interfaceId', 'reportId', 'interfaceName', 'interfaceCode', 'interfaceDesc',
            'interfaceDbType', 'interfaceDbName', 'interfaceSql', 'isTotal', 'totalSql',
            'isPaging', 'isDateOption', 'isSecondTable', 'isLoginVisit', 'alarmType',
            'userName', 'interfaceDatasource','enable','reportName','reportCode',
            'moduleName','platformName'
        ]

    def validate(self, attrs):
        _validate_total_sql_requirement(attrs.get('is_total', '0'), attrs.get('total_sql'))
        return attrs


class InterfaceInfoCreateSerializer(InterfaceInfoSerializer):
    pass


class InterfaceInfoUpdateSerializer(InterfaceInfoSerializer):
    interfaceId = serializers.IntegerField(source='id')


class InterfaceFieldSerializer(BaseModelSerializer):
    fieldId = serializers.IntegerField(source='id', read_only=True)
    interfaceId = serializers.IntegerField(source='interface_id')
    interfaceParaCode = serializers.CharField(source='interface_para_code')
    interfaceParaName = serializers.CharField(source='interface_para_name')
    interfaceParaPosition = serializers.IntegerField(source='interface_para_position')
    interfaceParaType = serializers.CharField(source='interface_para_type')
    interfaceDataType = serializers.CharField(source='interface_data_type')
    interfaceParaDefault = serializers.CharField(source='interface_para_default', required=False, allow_null=True, allow_blank=True)
    interfaceParaRowspan = serializers.IntegerField(source='interface_para_rowspan', required=False, allow_null=True) 
    interfaceParentName = serializers.CharField(source='interface_parent_name', required=False, allow_null=True, allow_blank=True)
    interfaceParentPosition = serializers.IntegerField(source='interface_parent_position', required=False, allow_null=True) 
    interfaceParaInterfaceCode = serializers.CharField(source='interface_para_interface_code', required=False, allow_null=True, allow_blank=True)
    interfaceCascadePara = serializers.CharField(source='interface_cascade_para', required=False, allow_null=True, allow_blank=True)
    interfaceShowFlag = serializers.CharField(source='interface_show_flag', required=False, allow_null=True, allow_blank=True)
    interfaceExportFlag = serializers.CharField(source='interface_export_flag', required=False, allow_null=True, allow_blank=True)
    interfaceShowDesc = serializers.CharField(source='interface_show_desc', required=False, allow_null=True, allow_blank=True)
    interfaceParaDesc = serializers.CharField(source='interface_para_desc', required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = InterfaceField
        fields = [
            'fieldId', 'interfaceId', 'interfaceParaCode', 'interfaceParaName', 'interfaceParaPosition',
            'interfaceParaType', 'interfaceDataType', 'interfaceParaDefault', 'interfaceParaRowspan',
            'interfaceParentName', 'interfaceParentPosition', 'interfaceParaInterfaceCode',
            'interfaceCascadePara', 'interfaceShowFlag', 'interfaceExportFlag', 'interfaceShowDesc',
            'interfaceParaDesc'
        ]


class InterfaceFieldUpdateSerializer(InterfaceFieldSerializer):
    fieldId = serializers.IntegerField(source='id')


class ReportInfoSerializer(BaseModelSerializer):
    reportId = serializers.IntegerField(source='id', read_only=True)
    reportName = serializers.CharField(source='report_name')
    reportCode = serializers.RegexField(source='report_code', regex=r'^[A-Za-z0-9_-]+$', max_length=255)
    reportDesc = serializers.CharField(source='report_desc', required=False, allow_blank=True, allow_null=True)
    userName = serializers.CharField(source='user_name', required=False, allow_blank=True, allow_null=True)
    interfaceIds = serializers.ListField(child=serializers.IntegerField(min_value=1), write_only=True, required=False, allow_empty=False)
    interfaceCount = serializers.SerializerMethodField(read_only=True)
    interfaces = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ReportInfo
        fields = [
            'reportId', 'reportName', 'reportCode', 'reportDesc', 'userName',
            'interfaceIds', 'interfaceCount', 'interfaces'
        ]

    def validate_interfaceIds(self, value):
        interface_ids = _normalize_interface_ids(value)
        valid_count = InterfaceInfo.objects.filter(id__in=interface_ids, del_flag='0').count()
        if valid_count != len(interface_ids):
            raise serializers.ValidationError('存在已删除或不存在的接口，请重新选择')
        return interface_ids

    def validate(self, attrs):
        if self.instance is None and not attrs.get('interfaceIds'):
            raise serializers.ValidationError('请至少选择一个接口')
        return attrs

    def get_interfaceCount(self, obj):
        return len(self._get_active_relations(obj))

    def get_interfaces(self, obj):
        interfaces = []
        for relation in self._get_active_relations(obj):
            interface = relation.interface
            if interface.del_flag != '0':
                continue
            interfaces.append({
                'interfaceId': interface.id,
                'interfaceName': interface.interface_name,
                'interfaceCode': interface.interface_code,
                'interfaceDesc': interface.interface_desc or '',
                'userName': interface.user_name or '',
                'enable': interface.enable,
            })
        return interfaces

    def create(self, validated_data):
        interface_ids = validated_data.pop('interfaceIds', [])
        with transaction.atomic():
            report = ReportInfo.objects.create(**validated_data)
            self._sync_interfaces(report, interface_ids)
        return report

    def update(self, instance, validated_data):
        interface_ids = validated_data.pop('interfaceIds', None)
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            if interface_ids is not None:
                self._sync_interfaces(instance, interface_ids)
        return instance

    def _sync_interfaces(self, report, interface_ids):
        username = getattr(getattr(self.context.get('request'), 'user', None), 'username', '') or ''
        ReportInterfaceRelation.objects.filter(report=report, del_flag='1').delete()
        ReportInterfaceRelation.objects.filter(report=report, del_flag='0').update(
            del_flag='1',
            update_by=username,
            update_time=timezone.now(),
        )
        relations = []
        for index, interface_id in enumerate(interface_ids, start=1):
            relations.append(ReportInterfaceRelation(
                report=report,
                interface_id=interface_id,
                interface_position=index,
                create_by=username,
                update_by=username,
            ))
        ReportInterfaceRelation.objects.bulk_create(relations)

    def _get_active_relations(self, obj):
        prefetched = getattr(obj, 'prefetched_active_relations', None)
        if prefetched is not None:
            return prefetched
        return list(
            obj.report_interfaces.select_related('interface')
            .filter(del_flag='0', interface__del_flag='0')
            .order_by('interface_position', 'id')
        )


class ReportInfoUpdateSerializer(ReportInfoSerializer):
    reportId = serializers.IntegerField(source='id')
