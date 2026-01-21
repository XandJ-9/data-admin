"""
ETL模块序列化器 - 简化版
"""
from rest_framework import serializers
from apps.system.serializers import BaseModelSerializer
from .models import ETLTask, ETLExecution, ETLTemplate


class ETLTaskSerializer(BaseModelSerializer):
    """ETL任务序列化器"""

    scenario_display = serializers.CharField(source='get_scenario_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sync_mode_display = serializers.CharField(source='get_sync_mode_display', read_only=True)
    executor_type_display = serializers.CharField(source='get_executor_type_display', read_only=True)
    schedule_type_display = serializers.CharField(source='get_schedule_type_display', read_only=True)

    source_datasource_name = serializers.CharField(source='source_datasource.name', read_only=True)
    target_datasource_name = serializers.CharField(source='target_datasource.name', read_only=True)

    execution_count = serializers.SerializerMethodField()
    last_execution_time = serializers.SerializerMethodField()
    last_execution_status = serializers.SerializerMethodField()

    class Meta:
        model = ETLTask
        fields = [
            'id', 'name', 'scenario', 'scenario_display', 'status', 'status_display',
            'remark', 'source_datasource', 'source_datasource_name', 'source_table',
            'source_database', 'source_filter', 'target_datasource', 'target_datasource_name',
            'target_table', 'target_database', 'target_layer', 'sync_mode', 'sync_mode_display',
            'incremental_field', 'field_mappings', 'sql_script', 'transform_rules',
            'executor_type', 'executor_type_display', 'batch_size', 'concurrency',
            'schedule_type', 'schedule_type_display', 'schedule_cron', 'advanced_config',
            'execution_count', 'last_execution_time', 'last_execution_status',
            'create_by', 'create_time', 'update_by', 'update_time',
        ]
        extra_kwargs = {
            'source_datasource': {'required': False},
            'target_datasource': {'required': False},
        }

    def get_execution_count(self, obj):
        return obj.executions.count()

    def get_last_execution_time(self, obj):
        last_exec = obj.executions.first()
        return last_exec.create_time if last_exec else None

    def get_last_execution_status(self, obj):
        last_exec = obj.executions.first()
        return last_exec.status if last_exec else None

    def validate(self, data):
        """根据场景验证必填字段"""
        scenario = data.get('scenario')
        if not scenario:
            raise serializers.ValidationError({'scenario': '场景类型不能为空'})

        # 场景特定的验证规则
        if scenario == 'biz_to_stg':
            if not data.get('source_datasource'):
                raise serializers.ValidationError({'source_datasource': '请选择源数据源'})
            if not data.get('source_table'):
                raise serializers.ValidationError({'source_table': '请选择源表'})

        elif scenario == 'warehouse_transform':
            if not data.get('sql_script'):
                raise serializers.ValidationError({'sql_script': '请输入SQL脚本'})
            if not data.get('target_layer'):
                raise serializers.ValidationError({'target_layer': '请选择目标层级'})

        elif scenario == 'warehouse_to_biz':
            if not data.get('source_table'):
                raise serializers.ValidationError({'source_table': '请选择源表'})
            if not data.get('target_datasource'):
                raise serializers.ValidationError({'target_datasource': '请选择目标数据源'})
            if not data.get('target_table'):
                raise serializers.ValidationError({'target_table': '请选择目标表'})

        elif scenario in ['stg_to_ods', 'db_to_db']:
            if not data.get('source_table'):
                raise serializers.ValidationError({'source_table': '请选择源表'})
            if scenario == 'db_to_db' and not data.get('target_datasource'):
                raise serializers.ValidationError({'target_datasource': '请选择目标数据源'})

        # 增量同步时必须指定增量字段
        if data.get('sync_mode') == 'incremental' and not data.get('incremental_field'):
            raise serializers.ValidationError({'incremental_field': '增量同步时必须指定增量字段'})

        # 定时执行时必须指定cron表达式
        if data.get('schedule_type') == 'scheduled' and not data.get('schedule_cron'):
            raise serializers.ValidationError({'schedule_cron': '定时执行时必须指定Cron表达式'})

        return data


class ETLTaskCreateSerializer(BaseModelSerializer):
    """ETL任务创建序列化器 - 简化版"""

    class Meta:
        model = ETLTask
        fields = [
            'name', 'scenario', 'status', 'remark',
            'source_datasource', 'source_table', 'source_database', 'source_filter',
            'target_datasource', 'target_table', 'target_database', 'target_layer',
            'sync_mode', 'incremental_field', 'field_mappings',
            'sql_script', 'transform_rules',
            'executor_type', 'batch_size', 'concurrency',
            'schedule_type', 'schedule_cron', 'advanced_config',
        ]

    def create(self, validated_data):
        """创建任务时根据场景设置默认值"""
        scenario = validated_data.get('scenario')

        # 根据场景自动设置执行器类型
        if scenario == 'warehouse_transform':
            validated_data['executor_type'] = 'spark_sql'
        elif scenario == 'stg_to_ods':
            validated_data['executor_type'] = 'spark_sql'
            validated_data['target_layer'] = 'ods'
        elif scenario == 'biz_to_stg':
            validated_data['executor_type'] = 'datax'
            validated_data['target_layer'] = 'stg'

        return super().create(validated_data)


class ETLExecutionSerializer(BaseModelSerializer):
    """ETL执行记录序列化器"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    task_name = serializers.CharField(source='task.name', read_only=True)
    scenario_display = serializers.CharField(source='task.get_scenario_display', read_only=True)

    duration_formatted = serializers.SerializerMethodField()

    class Meta:
        model = ETLExecution
        fields = [
            'id', 'task', 'task_name', 'scenario_display', 'status', 'status_display',
            'rows_read', 'rows_written', 'rows_failed',
            'start_time', 'end_time', 'duration', 'duration_formatted',
            'progress', 'current_stage', 'logs', 'error_message',
            'create_time', 'update_time',
        ]

    def get_duration_formatted(self, obj):
        """格式化执行时长"""
        if obj.duration < 60:
            return f"{obj.duration}秒"
        elif obj.duration < 3600:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}分{seconds}秒"
        else:
            hours = obj.duration // 3600
            minutes = (obj.duration % 3600) // 60
            return f"{hours}小时{minutes}分"


class ETLExecutionListSerializer(BaseModelSerializer):
    """ETL执行记录列表序列化器"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    task_name = serializers.CharField(source='task.name', read_only=True)

    class Meta:
        model = ETLExecution
        fields = [
            'id', 'task', 'task_name', 'status', 'status_display',
            'rows_read', 'rows_written', 'duration',
            'progress', 'create_time',
        ]


class ETLTemplateSerializer(BaseModelSerializer):
    """ETL模板序列化器"""

    scenario_display = serializers.CharField(source='get_scenario_display', read_only=True)

    class Meta:
        model = ETLTemplate
        fields = [
            'id', 'scenario', 'scenario_display', 'name', 'description',
            'template_config', 'usage_count', 'is_system',
            'create_by', 'create_time', 'update_by', 'update_time',
        ]


class ScenarioConfigSerializer(serializers.Serializer):
    """场景配置序列化器 - 返回场景的默认配置"""

    scenarios = serializers.ListField(child=serializers.DictField())


class TablePreviewSerializer(serializers.Serializer):
    """表数据预览序列化器"""

    datasource_id = serializers.IntegerField(required=True)
    table = serializers.CharField(required=True)
    database = serializers.CharField(required=False, default='')
    where = serializers.CharField(required=False, default='')
    limit = serializers.IntegerField(required=False, default=10)
