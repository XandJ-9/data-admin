from django.contrib import admin

from .models import Task, TaskDependency, TaskInstance


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'task_name',
        'task_code',
        'task_type',
        'status',
        'schedule_type',
        'owner',
        'last_instance_status',
        'last_instance_at',
    ]
    list_filter = ['task_type', 'status', 'schedule_type', 'del_flag']
    search_fields = ['task_name', 'task_code', 'source_module']


@admin.register(TaskDependency)
class TaskDependencyAdmin(admin.ModelAdmin):
    list_display = ['id', 'upstream_task', 'downstream_task', 'trigger_condition', 'lag_seconds']
    list_filter = ['trigger_condition', 'del_flag']
    search_fields = ['upstream_task__task_code', 'downstream_task__task_code']


@admin.register(TaskInstance)
class TaskInstanceAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'task',
        'instance_id',
        'status',
        'trigger_mode',
        'executor_type',
        'triggered_by',
        'create_time',
    ]
    list_filter = ['status', 'trigger_mode', 'executor_type']
    search_fields = ['instance_id', 'task__task_code', 'task__task_name']
