from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('datasource', '0002_encrypt_existing_passwords'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasource',
            name='connectivity_message',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='最近连通性说明'),
        ),
        migrations.AddField(
            model_name='datasource',
            name='connectivity_status',
            field=models.CharField(
                choices=[('unknown', '未测试'), ('success', '连通'), ('failed', '异常')],
                default='unknown',
                max_length=16,
                verbose_name='最近连通性状态',
            ),
        ),
        migrations.AddField(
            model_name='datasource',
            name='connectivity_tested_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='最近连通性测试时间'),
        ),
    ]

