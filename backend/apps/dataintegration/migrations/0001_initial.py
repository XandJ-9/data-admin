import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('datasource', '0004_phase1_snapshots_and_tasks'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataIntegrationTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('task_name', models.CharField(max_length=128, verbose_name='任务名称')),
                ('task_code', models.CharField(max_length=128, unique=True, verbose_name='任务编码')),
                ('source_database_name', models.CharField(blank=True, default='', max_length=256, verbose_name='源数据库名')),
                ('source_table_name', models.CharField(blank=True, default='', max_length=256, verbose_name='源表名')),
                ('target_schema_name', models.CharField(blank=True, default='', max_length=128, verbose_name='目标Schema')),
                ('target_table_name', models.CharField(max_length=128, verbose_name='目标表名')),
                ('load_type', models.CharField(choices=[('full', '全量'), ('incremental', '增量')], default='full', max_length=20, verbose_name='加载类型')),
                ('write_mode', models.CharField(choices=[('overwrite', '覆盖'), ('append', '追加'), ('upsert', '更新插入')], default='overwrite', max_length=20, verbose_name='写入模式')),
                ('executor_type', models.CharField(choices=[('mock', '模拟执行器'), ('datax', 'DataX执行器')], default='mock', max_length=20, verbose_name='执行器类型')),
                ('status', models.CharField(choices=[('draft', '草稿'), ('active', '启用'), ('paused', '暂停'), ('archived', '归档')], default='active', max_length=20, verbose_name='状态')),
                ('schedule_type', models.CharField(choices=[('manual', '手动触发'), ('cron', '定时调度')], default='manual', max_length=20, verbose_name='调度类型')),
                ('cron_expression', models.CharField(blank=True, default='', max_length=64, verbose_name='Cron表达式')),
                ('task_config', models.JSONField(blank=True, default=dict, verbose_name='任务配置')),
                ('owner', models.CharField(blank=True, default='', max_length=64, verbose_name='负责人')),
                ('remark', models.CharField(blank=True, default='', max_length=500, verbose_name='备注')),
                ('source_datasource', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='source_integration_tasks', to='datasource.datasource', verbose_name='源数据源')),
                ('source_table_snapshot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='integration_tasks', to='datasource.sourcetablesnapshot', verbose_name='源表快照')),
                ('target_datasource', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='target_integration_tasks', to='datasource.datasource', verbose_name='目标数据源')),
            ],
            options={
                'verbose_name': '数据集成任务',
                'verbose_name_plural': '数据集成任务',
                'db_table': 'dataintegration_task',
                'ordering': ['-update_time', '-id'],
            },
        ),
        migrations.CreateModel(
            name='DataIntegrationExecutionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('instance_id', models.CharField(max_length=64, unique=True, verbose_name='实例ID')),
                ('status', models.CharField(choices=[('pending', '等待执行'), ('running', '执行中'), ('success', '执行成功'), ('failed', '执行失败'), ('cancelled', '已取消')], default='pending', max_length=20, verbose_name='状态')),
                ('trigger_mode', models.CharField(blank=True, default='manual', max_length=32, verbose_name='触发方式')),
                ('triggered_by', models.CharField(blank=True, default='', max_length=64, verbose_name='触发人')),
                ('executor_type', models.CharField(blank=True, default='', max_length=20, verbose_name='执行器类型')),
                ('runtime_config', models.JSONField(blank=True, default=dict, verbose_name='运行时配置')),
                ('result_summary', models.JSONField(blank=True, default=dict, verbose_name='结果摘要')),
                ('error_message', models.CharField(blank=True, default='', max_length=1000, verbose_name='错误信息')),
                ('raw_output', models.TextField(blank=True, default='', verbose_name='原始输出')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='结束时间')),
                ('duration_seconds', models.IntegerField(default=0, verbose_name='耗时秒数')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='execution_logs', to='dataintegration.dataintegrationtask', verbose_name='集成任务')),
            ],
            options={
                'verbose_name': '数据集成执行日志',
                'verbose_name_plural': '数据集成执行日志',
                'db_table': 'dataintegration_execution_log',
                'ordering': ['-create_time', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='dataintegrationtask',
            index=models.Index(fields=['del_flag', 'status'], name='dataintegra_del_fla_31c6bc_idx'),
        ),
        migrations.AddIndex(
            model_name='dataintegrationtask',
            index=models.Index(fields=['source_datasource'], name='dataintegra_source__e988e9_idx'),
        ),
        migrations.AddIndex(
            model_name='dataintegrationtask',
            index=models.Index(fields=['target_datasource'], name='dataintegra_target__6e979c_idx'),
        ),
        migrations.AddIndex(
            model_name='dataintegrationtask',
            index=models.Index(fields=['executor_type'], name='dataintegra_executo_dfe167_idx'),
        ),
        migrations.AddIndex(
            model_name='dataintegrationexecutionlog',
            index=models.Index(fields=['task', 'status'], name='dataintegra_task_id_6aa420_idx'),
        ),
        migrations.AddIndex(
            model_name='dataintegrationexecutionlog',
            index=models.Index(fields=['instance_id'], name='dataintegra_instanc_11c5d8_idx'),
        ),
        migrations.AddIndex(
            model_name='dataintegrationexecutionlog',
            index=models.Index(fields=['del_flag'], name='dataintegra_del_fla_27083b_idx'),
        ),
    ]

