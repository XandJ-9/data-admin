import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('dataasset', '0007_delete_metacollectiontask'),
        ('datasource', '0004_phase1_snapshots_and_tasks'),
        ('dataintegration', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataintegrationtask',
            name='source_asset',
        ),
        migrations.AddField(
            model_name='dataintegrationtask',
            name='source_database_name',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='源数据库名'),
        ),
        migrations.AddField(
            model_name='dataintegrationtask',
            name='source_table_name',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='源表名'),
        ),
        migrations.AddField(
            model_name='dataintegrationtask',
            name='source_table_snapshot',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='integration_tasks',
                to='datasource.sourcetablesnapshot',
                verbose_name='源表快照',
            ),
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
            model_name='dataintegrationexecutionlog',
            index=models.Index(fields=['task', 'status'], name='dataintegra_task_id_940a9f_idx'),
        ),
        migrations.AddIndex(
            model_name='dataintegrationexecutionlog',
            index=models.Index(fields=['instance_id'], name='dataintegra_instanc_d5b477_idx'),
        ),
        migrations.AddIndex(
            model_name='dataintegrationexecutionlog',
            index=models.Index(fields=['del_flag'], name='dataintegra_del_fla_f9f289_idx'),
        ),
    ]
