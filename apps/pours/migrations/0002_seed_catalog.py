import json
from pathlib import Path

from django.core.management import call_command
from django.db import migrations

FIXTURE = Path(__file__).resolve().parent.parent / 'fixtures' / 'catalog.json'


def load_catalog(apps, schema_editor):
    call_command('loaddata', 'catalog', app_label='pours')


def unload_catalog(apps, schema_editor):
    rows = json.loads(FIXTURE.read_text())
    MenuItem = apps.get_model('pours', 'MenuItem')
    Category = apps.get_model('pours', 'Category')
    MenuItem.objects.filter(
        slug__in=[row['fields']['slug'] for row in rows if row['model'] == 'pours.menuitem']
    ).delete()
    Category.objects.filter(
        slug__in=[row['fields']['slug'] for row in rows if row['model'] == 'pours.category']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pours', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_catalog, unload_catalog),
    ]
