from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datasource', '0008_backfill_collection_tasks_from_databaseassetsyncrun'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DatabaseAssetSyncRun',
        ),
    ]
