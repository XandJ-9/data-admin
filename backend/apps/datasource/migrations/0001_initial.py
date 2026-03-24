"""
Move DataSource model from dataasset to datasource app.

This migration uses SeparateDatabaseAndState to register the model
in the new app without touching the existing database table.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dataasset', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='DataSource',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('create_by', models.CharField(blank=True, max_length=64)),
                        ('update_by', models.CharField(blank=True, max_length=64)),
                        ('create_time', models.DateTimeField(auto_now_add=True)),
                        ('update_time', models.DateTimeField(auto_now=True)),
                        ('del_flag', models.CharField(choices=[('0', '正常'), ('1', '删除')], default='0', max_length=1)),
                        ('name', models.CharField(max_length=64, verbose_name='数据源名称')),
                        ('db_type', models.CharField(max_length=20, verbose_name='数据库类型')),
                        ('host', models.CharField(blank=True, default='', max_length=128, verbose_name='主机')),
                        ('port', models.IntegerField(default=0, verbose_name='端口')),
                        ('db_name', models.CharField(blank=True, default='', max_length=128, verbose_name='数据库名')),
                        ('username', models.CharField(blank=True, default='', max_length=128, verbose_name='用户名')),
                        ('password', models.CharField(blank=True, default='', max_length=256, verbose_name='密码')),
                        ('params', models.TextField(blank=True, default='', verbose_name='连接参数(JSON 或 KV)')),
                        ('status', models.CharField(choices=[('0', '正常'), ('1', '停用')], default='0', max_length=1, verbose_name='状态')),
                        ('remark', models.CharField(blank=True, default='', max_length=500, verbose_name='备注')),
                    ],
                    options={
                        'verbose_name': '数据源',
                        'verbose_name_plural': '数据源',
                        'db_table': 'dataasset_datasource',
                        'indexes': [
                            models.Index(fields=['name'], name='dataasset_d_name_cc0358_idx'),
                            models.Index(fields=['db_type'], name='dataasset_d_db_type_d0e0ab_idx'),
                            models.Index(fields=['status'], name='dataasset_d_status_9cdf07_idx'),
                            models.Index(fields=['del_flag'], name='dataasset_d_del_fla_891397_idx'),
                        ],
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
