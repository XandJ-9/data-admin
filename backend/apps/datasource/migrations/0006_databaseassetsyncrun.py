from django.db import migrations, models
import django.db.models.deletion
import django.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('datasource', '0005_remove_sourcemetadatacollectiontask_data_source_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DatabaseAssetSyncRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('run_id', models.CharField(max_length=64, unique=True, verbose_name='运行ID')),
                ('database_name', models.CharField(max_length=256, verbose_name='数据库名')),
                ('status', models.CharField(choices=[('pending', '待执行'), ('running', '执行中'), ('completed', '已完成'), ('failed', '失败')], default='pending', max_length=16, verbose_name='状态')),
                ('total_tables', models.IntegerField(default=0, verbose_name='应采集表数')),
                ('successful_tables', models.IntegerField(default=0, verbose_name='成功表数')),
                ('failed_tables', models.IntegerField(default=0, verbose_name='失败表数')),
                ('skipped_tables', models.IntegerField(default=0, verbose_name='跳过对象数')),
                ('current_table', models.CharField(blank=True, default='', max_length=256, verbose_name='当前表')),
                ('error_message', models.CharField(blank=True, default='', max_length=1000, verbose_name='错误信息')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('result_summary', models.JSONField(blank=True, default=dict, verbose_name='结果摘要')),
                ('data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='database_asset_sync_runs', to='datasource.datasource', verbose_name='数据源')),
            ],
            options={
                'verbose_name': '整库资产采集实例',
                'verbose_name_plural': '整库资产采集实例',
                'db_table': 'datasource_asset_sync_run',
            },
        ),
        migrations.AddIndex(
            model_name='databaseassetsyncrun',
            index=models.Index(fields=['run_id'], name='datasource__run_id_dc0b64_idx'),
        ),
        migrations.AddIndex(
            model_name='databaseassetsyncrun',
            index=models.Index(fields=['data_source', 'database_name'], name='datasource__data_so_57f0db_idx'),
        ),
        migrations.AddIndex(
            model_name='databaseassetsyncrun',
            index=models.Index(fields=['data_source', 'status'], name='datasource__data_so_a6841a_idx'),
        ),
        migrations.AddIndex(
            model_name='databaseassetsyncrun',
            index=models.Index(fields=['del_flag'], name='datasource__del_fla_31b36a_idx'),
        ),
        migrations.AddConstraint(
            model_name='databaseassetsyncrun',
            constraint=models.UniqueConstraint(
                condition=django.db.models.Q(('del_flag', '0'), ('status__in', ['pending', 'running'])),
                fields=('data_source', 'database_name'),
                name='uniq_datasource_active_asset_sync_run',
            ),
        ),
    ]
