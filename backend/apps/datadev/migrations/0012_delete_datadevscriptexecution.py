from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datadev', '0011_backfill_taskinstances_from_scriptexecution'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DataDevScriptExecution',
        ),
    ]
