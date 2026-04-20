"""
Encrypt existing plaintext passwords in DataSource table.

Passwords that already start with 'enc:' are skipped.
"""
from django.db import migrations


def encrypt_passwords(apps, schema_editor):
    DataSource = apps.get_model('datasource', 'DataSource')
    from apps.common.encrypt import encrypt_password

    for ds in DataSource.objects.exclude(password='').exclude(password__startswith='enc:'):
        ds.password = encrypt_password(ds.password)
        ds.save(update_fields=['password'])


def decrypt_passwords(apps, schema_editor):
    DataSource = apps.get_model('datasource', 'DataSource')
    from apps.common.encrypt import decrypt_password

    for ds in DataSource.objects.filter(password__startswith='enc:'):
        ds.password = decrypt_password(ds.password)
        ds.save(update_fields=['password'])


class Migration(migrations.Migration):

    dependencies = [
        ('datasource', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(encrypt_passwords, decrypt_passwords),
    ]
