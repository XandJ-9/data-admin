import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('datasource', '0003_datasource_connectivity_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasource',
            name='db_name',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='数据库名'),
        ),
        migrations.CreateModel(
            name='SourceMetadataCollectionTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('task_id', models.CharField(max_length=64, unique=True, verbose_name='任务ID')),
                ('collection_scope', models.CharField(choices=[('full', '整源采集'), ('database', '整库采集'), ('table', '单表采集')], default='full', max_length=16, verbose_name='采集范围')),
                ('run_mode', models.CharField(choices=[('sync', '同步'), ('async', '异步')], default='sync', max_length=16, verbose_name='执行模式')),
                ('status', models.CharField(choices=[('pending', '待执行'), ('running', '执行中'), ('completed', '已完成'), ('failed', '失败'), ('cancelled', '已取消')], default='pending', max_length=16, verbose_name='状态')),
                ('database_name', models.CharField(blank=True, default='', max_length=256, verbose_name='数据库名')),
                ('table_name', models.CharField(blank=True, default='', max_length=256, verbose_name='表名')),
                ('total_tables', models.IntegerField(default=0, verbose_name='总表数')),
                ('collected_tables', models.IntegerField(default=0, verbose_name='已采集表数')),
                ('current_table', models.CharField(blank=True, default='', max_length=256, verbose_name='当前表')),
                ('error_message', models.CharField(blank=True, default='', max_length=500, verbose_name='错误信息')),
                ('cancel_requested', models.BooleanField(default=False, verbose_name='是否请求取消')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('result_summary', models.JSONField(blank=True, default=dict, verbose_name='结果摘要')),
                ('data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collection_tasks', to='datasource.datasource', verbose_name='数据源')),
            ],
            options={
                'verbose_name': '源数据采集任务',
                'verbose_name_plural': '源数据采集任务',
                'db_table': 'datasource_collection_task',
            },
        ),
        migrations.CreateModel(
            name='SourceTableSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('database_name', models.CharField(blank=True, default='', max_length=256, verbose_name='数据库名')),
                ('table_name', models.CharField(max_length=256, verbose_name='表名')),
                ('table_type', models.CharField(blank=True, default='TABLE', max_length=64, verbose_name='表类型')),
                ('table_comment', models.CharField(blank=True, default='', max_length=500, verbose_name='表注释')),
                ('source_create_time', models.CharField(blank=True, default='', max_length=64, verbose_name='源创建时间')),
                ('source_update_time', models.CharField(blank=True, default='', max_length=64, verbose_name='源更新时间')),
                ('raw_payload', models.JSONField(blank=True, default=dict, verbose_name='原始载荷')),
                ('data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='table_snapshots', to='datasource.datasource', verbose_name='数据源')),
            ],
            options={
                'verbose_name': '源表快照',
                'verbose_name_plural': '源表快照',
                'db_table': 'datasource_source_table',
            },
        ),
        migrations.CreateModel(
            name='SourceColumnSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('column_name', models.CharField(max_length=256, verbose_name='字段名')),
                ('ordinal_position', models.IntegerField(default=0, verbose_name='序号')),
                ('data_type', models.CharField(blank=True, default='', max_length=128, verbose_name='数据类型')),
                ('column_type', models.CharField(blank=True, default='', max_length=255, verbose_name='完整类型')),
                ('is_nullable', models.CharField(blank=True, default='YES', max_length=8, verbose_name='是否可空')),
                ('column_default', models.CharField(blank=True, default='', max_length=255, verbose_name='默认值')),
                ('column_key', models.CharField(blank=True, default='', max_length=32, verbose_name='键类型')),
                ('column_comment', models.CharField(blank=True, default='', max_length=500, verbose_name='字段注释')),
                ('raw_payload', models.JSONField(blank=True, default=dict, verbose_name='原始载荷')),
                ('table_snapshot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='column_snapshots', to='datasource.sourcetablesnapshot', verbose_name='表快照')),
            ],
            options={
                'verbose_name': '源字段快照',
                'verbose_name_plural': '源字段快照',
                'db_table': 'datasource_source_column',
            },
        ),
        migrations.AddIndex(
            model_name='sourcemetadatacollectiontask',
            index=models.Index(fields=['task_id'], name='datasource__task_id_16d469_idx'),
        ),
        migrations.AddIndex(
            model_name='sourcemetadatacollectiontask',
            index=models.Index(fields=['data_source', 'status'], name='datasource__data_so_abaa4e_idx'),
        ),
        migrations.AddIndex(
            model_name='sourcemetadatacollectiontask',
            index=models.Index(fields=['del_flag'], name='datasource__del_fla_2565eb_idx'),
        ),
        migrations.AddConstraint(
            model_name='sourcemetadatacollectiontask',
            constraint=models.UniqueConstraint(condition=models.Q(('del_flag', '0'), ('status__in', ['pending', 'running'])), fields=('data_source',), name='uniq_datasource_active_collection_task'),
        ),
        migrations.AddIndex(
            model_name='sourcetablesnapshot',
            index=models.Index(fields=['data_source', 'database_name'], name='datasource__data_so_572420_idx'),
        ),
        migrations.AddIndex(
            model_name='sourcetablesnapshot',
            index=models.Index(fields=['data_source', 'table_name'], name='datasource__data_so_3f2a4e_idx'),
        ),
        migrations.AddIndex(
            model_name='sourcetablesnapshot',
            index=models.Index(fields=['del_flag'], name='datasource__del_fla_588cb7_idx'),
        ),
        migrations.AddConstraint(
            model_name='sourcetablesnapshot',
            constraint=models.UniqueConstraint(fields=('data_source', 'database_name', 'table_name', 'del_flag'), name='uniq_datasource_source_table_active'),
        ),
        migrations.AddIndex(
            model_name='sourcecolumnsnapshot',
            index=models.Index(fields=['table_snapshot', 'ordinal_position'], name='datasource__table_s_ca0006_idx'),
        ),
        migrations.AddIndex(
            model_name='sourcecolumnsnapshot',
            index=models.Index(fields=['table_snapshot', 'column_name'], name='datasource__table_s_c61f65_idx'),
        ),
        migrations.AddIndex(
            model_name='sourcecolumnsnapshot',
            index=models.Index(fields=['del_flag'], name='datasource__del_fla_d62300_idx'),
        ),
        migrations.AddConstraint(
            model_name='sourcecolumnsnapshot',
            constraint=models.UniqueConstraint(fields=('table_snapshot', 'column_name', 'del_flag'), name='uniq_datasource_source_column_active'),
        ),
    ]
