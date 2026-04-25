from django.db import migrations


def encrypt_passwords(apps, schema_editor):
    DataSource = apps.get_model('datasource', 'DataSource')
    from apps.common.encrypt import encrypt_password

    for data_source in DataSource.objects.exclude(password='').exclude(password__startswith='enc:'):
        data_source.password = encrypt_password(data_source.password)
        data_source.save(update_fields=['password'])


def decrypt_passwords(apps, schema_editor):
    DataSource = apps.get_model('datasource', 'DataSource')
    from apps.common.encrypt import decrypt_password

    for data_source in DataSource.objects.filter(password__startswith='enc:'):
        data_source.password = decrypt_password(data_source.password)
        data_source.save(update_fields=['password'])


class Migration(migrations.Migration):
    dependencies = [
        ('datasource', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(encrypt_passwords, decrypt_passwords),
    ]

