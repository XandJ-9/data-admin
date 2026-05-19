from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataasset', '0007_delete_metacollectiontask'),
        ('dataservice', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='interfaceinfo',
            name='asset',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='service_interfaces',
                to='dataasset.dataasset',
                verbose_name='资产锚点',
            ),
        ),
    ]