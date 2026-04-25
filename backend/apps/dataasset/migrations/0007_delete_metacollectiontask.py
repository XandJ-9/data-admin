from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('dataasset', '0006_dataasset_asset_category_dataasset_business_domain_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MetaCollectionTask',
        ),
    ]
