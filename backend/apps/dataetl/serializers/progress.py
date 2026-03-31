from rest_framework import serializers
from ..models import ETLExecutionProgress


class ETLExecutionProgressSerializer(serializers.ModelSerializer):
    progressId = serializers.IntegerField(source='id', read_only=True)
    executionId = serializers.CharField(source='execution.execution_id', read_only=True)
    currentStage = serializers.CharField(source='current_stage')
    progressPercentage = serializers.IntegerField(source='progress_percentage')
    processedRows = serializers.IntegerField(source='processed_rows')
    totalRows = serializers.IntegerField(source='total_rows')
    speedRowsPerSec = serializers.FloatField(source='speed_rows_per_sec')
    estimatedRemainingSeconds = serializers.IntegerField(source='estimated_remaining_seconds')
    checkpointData = serializers.JSONField(source='checkpoint_data', allow_null=True, required=False)
    heartbeatTime = serializers.DateTimeField(source='heartbeat_time', read_only=True)

    class Meta:
        model = ETLExecutionProgress
        fields = [
            'progressId', 'executionId', 'currentStage', 'progressPercentage',
            'processedRows', 'totalRows', 'speedRowsPerSec', 'estimatedRemainingSeconds',
            'checkpointData', 'heartbeatTime',
        ]
