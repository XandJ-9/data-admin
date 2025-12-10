from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='IntegrationTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_by', models.CharField(blank=True, max_length=64)),
                ('update_by', models.CharField(blank=True, max_length=64)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                ('name', models.CharField(max_length=255, verbose_name='任务名称')),
                ('type', models.CharField(choices=[('single', '单表'), ('multi', '分库分表')], max_length=20, verbose_name='任务类型')),
                ('schedule', models.JSONField(default=dict, verbose_name='调度配置')),
                ('detail', models.JSONField(default=dict, verbose_name='任务详情')),
                ('status', models.CharField(choices=[('0', '正常'), ('1', '停用')], default='0', max_length=1, verbose_name='状态')),
                ('remark', models.CharField(blank=True, default='', max_length=500, verbose_name='备注')),
            ],
            options={
                'db_table': 'dataintegration_task',
                'verbose_name': '数据集成任务',
                'verbose_name_plural': '数据集成任务',
            },
        ),
        migrations.AddIndex(
            model_name='integrationtask',
            index=models.Index(fields=['name'], name='dataintegra_name_5b2a4e_idx'),
        ),
        migrations.AddIndex(
            model_name='integrationtask',
            index=models.Index(fields=['type'], name='dataintegra_type_6d3ecb_idx'),
        ),
        migrations.AddIndex(
            model_name='integrationtask',
            index=models.Index(fields=['status'], name='dataintegra_status_3e7c6f_idx'),
        ),
        migrations.AddIndex(
            model_name='integrationtask',
            index=models.Index(fields=['del_flag'], name='dataintegra_del_fla_2b69e7_idx'),
        ),
    ]

