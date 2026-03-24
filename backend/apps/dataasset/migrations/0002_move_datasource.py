"""
Remove DataSource model from dataasset app (moved to datasource app).

Uses SeparateDatabaseAndState to update Django state without touching the database.
ForeignKey references are updated to point to datasource.DataSource.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataasset', '0001_initial'),
        ('datasource', '0001_initial'),
        ('dataetl', '0002_alter_etltask_source_datasource_and_more'),
        ('dataservice', '0007_alter_querylog_data_source'),
    ]

    operations = [
        # Update ForeignKey references from dataasset.DataSource to datasource.DataSource
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='metatable',
                    name='data_source',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='meta_tables',
                        to='datasource.datasource',
                    ),
                ),
                migrations.AlterField(
                    model_name='metacolumn',
                    name='data_source',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='meta_columns',
                        to='datasource.datasource',
                    ),
                ),
                migrations.AlterField(
                    model_name='metacollectiontask',
                    name='data_source',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='collection_tasks',
                        to='datasource.datasource',
                    ),
                ),
                # Remove DataSource from dataasset state
                migrations.DeleteModel(
                    name='DataSource',
                ),
            ],
            database_operations=[],
        ),
    ]
