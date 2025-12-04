from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from apps.dataservice.models import QueryLog, InterfaceInfo, InterfaceField


class DataServiceQuerySerializer(serializers.Serializer):
    dataSourceId = serializers.IntegerField()
    sql = serializers.CharField()
    params = serializers.DictField(child=serializers.CharField(), required=False, allow_empty=True)
    pageSize = serializers.IntegerField(required=False, min_value=1, default=50)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)


class DataServiceQueryLogSerializer(BaseModelSerializer):
    logId = serializers.IntegerField(source='id')
    dataSourceName = serializers.CharField(source='data_source.name')
    userName = serializers.CharField(source='username')
    sqlText = serializers.CharField(source='sql_text')
    status = serializers.CharField()
    durationMs = serializers.IntegerField(source='duration_ms')
    errorMsg = serializers.CharField(source='error_msg', required=False, allow_blank=True)

    class Meta:
        model = QueryLog
        fields = ['logId', 'dataSourceName', 'userName', 'sqlText', 'status', 'durationMs', 'errorMsg', 'createTime']


class InterfaceInfoSerializer(BaseModelSerializer):
    interfaceId = serializers.IntegerField(source='id', read_only=True)
    reportId = serializers.IntegerField(source='report_id', required=False, allow_null=True)
    interfaceName = serializers.CharField(source='interface_name')
    interfaceCode = serializers.CharField(source='interface_code')
    interfaceDesc = serializers.CharField(source='interface_desc', required=False, allow_blank=True)
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
    userName = serializers.CharField(source='user_name', required=False, allow_blank=True)
    interfaceDatasource = serializers.IntegerField(source='interface_datasource', required=False, allow_null=True)

    class Meta:
        model = InterfaceInfo
        fields = [
            'interfaceId', 'reportId', 'interfaceName', 'interfaceCode', 'interfaceDesc',
            'interfaceDbType', 'interfaceDbName', 'interfaceSql', 'isTotal', 'totalSql',
            'isPaging', 'isDateOption', 'isSecondTable', 'isLoginVisit', 'alarmType',
            'userName', 'interfaceDatasource'
        ]


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
    interfaceParaDefault = serializers.CharField(source='interface_para_default', required=False, allow_blank=True)
    interfaceParaRowspan = serializers.IntegerField(source='interface_para_rowspan', required=False, allow_null=True)
    interfaceParentName = serializers.CharField(source='interface_parent_name', required=False, allow_blank=True)
    interfaceParentPosition = serializers.IntegerField(source='interface_parent_position', required=False, allow_null=True)
    interfaceParaInterfaceCode = serializers.CharField(source='interface_para_interface_code', required=False, allow_blank=True)
    interfaceCascadePara = serializers.CharField(source='interface_cascade_para', required=False, allow_blank=True)
    interfaceShowFlag = serializers.CharField(source='interface_show_flag')
    interfaceExportFlag = serializers.CharField(source='interface_export_flag')
    interfaceShowDesc = serializers.CharField(source='interface_show_desc', required=False, allow_blank=True)
    interfaceParaDesc = serializers.CharField(source='interface_para_desc', required=False, allow_blank=True)

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