import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasource', '0006_databaseassetsyncrun'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSourceCollectionTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('task_name', models.CharField(max_length=128, verbose_name='任务名称')),
                ('task_code', models.CharField(max_length=128, unique=True, verbose_name='任务编码')),
                ('collection_scope', models.CharField(choices=[('table', '单表采集'), ('database', '整库采集')], default='table', max_length=16, verbose_name='采集范围')),
                ('database_name', models.CharField(blank=True, default='', max_length=256, verbose_name='数据库名')),
                ('table_name', models.CharField(blank=True, default='', max_length=256, verbose_name='表名')),
                ('continue_on_error', models.BooleanField(default=True, verbose_name='遇错继续')),
                ('status', models.CharField(choices=[('draft', '草稿'), ('active', '启用'), ('paused', '暂停'), ('archived', '归档')], default='active', max_length=20, verbose_name='状态')),
                ('schedule_type', models.CharField(choices=[('manual', '手动触发'), ('cron', '定时调度')], default='manual', max_length=20, verbose_name='调度类型')),
                ('cron_expression', models.CharField(blank=True, default='', max_length=64, verbose_name='Cron表达式')),
                ('owner', models.CharField(blank=True, default='', max_length=64, verbose_name='负责人')),
                ('task_config', models.JSONField(blank=True, default=dict, verbose_name='任务配置')),
                ('remark', models.CharField(blank=True, default='', max_length=500, verbose_name='备注')),
                ('data_source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='collection_tasks', to='datasource.datasource', verbose_name='数据源')),
            ],
            options={
                'verbose_name': '源数据采集任务',
                'verbose_name_plural': '源数据采集任务',
                'db_table': 'datasource_collection_task',
                'ordering': ['-update_time', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='datasourcecollectiontask',
            index=models.Index(fields=['del_flag', 'status'], name='datasource__del_fla_18ba76_idx'),
        ),
        migrations.AddIndex(
            model_name='datasourcecollectiontask',
            index=models.Index(fields=['data_source'], name='datasource__data_so_1b17f1_idx'),
        ),
        migrations.AddIndex(
            model_name='datasourcecollectiontask',
            index=models.Index(fields=['collection_scope'], name='datasource__collect_6622b0_idx'),
        ),
        migrations.AddIndex(
            model_name='datasourcecollectiontask',
            index=models.Index(fields=['owner'], name='datasource__owner_518bfd_idx'),
        ),
        migrations.AddConstraint(
            model_name='datasourcecollectiontask',
            constraint=models.UniqueConstraint(condition=models.Q(('del_flag', '0')), fields=('data_source', 'collection_scope', 'database_name', 'table_name'), name='uniq_datasource_live_collection_task'),
        ),
    ]
