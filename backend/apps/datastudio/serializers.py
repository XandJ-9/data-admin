from rest_framework import serializers
from .models import DataStudioTask

class DataStudioTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataStudioTask
        fields = '__all__'
        read_only_fields = ('id', 'create_time', 'update_time', 'create_by', 'update_by')
