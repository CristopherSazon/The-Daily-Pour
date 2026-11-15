import json
from pathlib import Path

from django.db import migrations


def load_rows(apps, filename):
    category = apps.get_model('menu', 'Category')
    product = apps.get_model('menu', 'MenuItem')
    recipe_line = apps.get_model('menu', 'RecipeLine')
    models = {
        'menu.category': category,
        'menu.product': product,
        'menu.recipeline': recipe_line,
    }
    path = Path(__file__).resolve().parents[1] / 'fixtures' / filename
    for entry in json.loads(path.read_text()):
        model = models[entry['model']]
        fields = dict(entry['fields'])
        if model is product:
            fields['category_id'] = fields.pop('category')
            fields.setdefault('menu_number', '')
            fields.setdefault('image_index', 0)
            fields.setdefault('featured_image', '')
            fields.setdefault('notes', '')
            fields.setdefault('method', '')
        if model is recipe_line:
            fields['item_id'] = fields.pop('item')
        model.objects.create(pk=entry['pk'], **fields)


def replace_catalog(apps, schema_editor):
    apps.get_model('orders', 'OrderLine').objects.all().delete()
    apps.get_model('orders', 'Order').objects.all().delete()
    apps.get_model('menu', 'MenuItem').objects.all().delete()
    apps.get_model('menu', 'Category').objects.all().delete()
    load_rows(apps, 'menu.json')


def restore_original_catalog(apps, schema_editor):
    apps.get_model('menu', 'MenuItem').objects.all().delete()
    apps.get_model('menu', 'Category').objects.all().delete()
    load_rows(apps, 'catalog.json')


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0003_menu_sprite_fields'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(replace_catalog, restore_original_catalog),
    ]
