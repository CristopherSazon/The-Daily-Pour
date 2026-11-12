from django.db import migrations


def load_catalog(apps, schema_editor):
    pass


def unload_catalog(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pours', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_catalog, unload_catalog),
    ]
