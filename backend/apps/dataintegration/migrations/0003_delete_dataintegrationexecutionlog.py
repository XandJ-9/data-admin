from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dataintegration', '0002_align_with_datasource_snapshots'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DataIntegrationExecutionLog',
        ),
    ]
