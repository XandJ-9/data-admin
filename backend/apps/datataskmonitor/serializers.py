from rest_framework import serializers
from .models import DataTask, TaskLog, AlertRule, AlertRecord

class DataTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataTask
        fields = '__all__'

class TaskLogSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    class Meta:
        model = TaskLog
        fields = '__all__'

class AlertRuleSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    class Meta:
        model = AlertRule
        fields = '__all__'

class AlertRecordSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.rule_name', read_only=True)
    class Meta:
        model = AlertRecord
        fields = '__all__'
