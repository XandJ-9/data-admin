from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datasource', '0009_delete_databaseassetsyncrun'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datasourcecollectiontask',
            name='cron_expression',
        ),
        migrations.RemoveField(
            model_name='datasourcecollectiontask',
            name='schedule_type',
        ),
        migrations.RemoveField(
            model_name='datasourcecollectiontask',
            name='task_config',
        ),
    ]