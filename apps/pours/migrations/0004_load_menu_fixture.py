from django.core.management import call_command
from django.db import migrations


def replace_catalog(apps, schema_editor):
    OrderLine = apps.get_model('orders', 'OrderLine')
    Order = apps.get_model('orders', 'Order')
    MenuItem = apps.get_model('pours', 'MenuItem')
    Category = apps.get_model('pours', 'Category')
    OrderLine.objects.all().delete()
    Order.objects.all().delete()
    MenuItem.objects.all().delete()
    Category.objects.all().delete()
    call_command('loaddata', 'menu', app_label='pours')


def restore_original_catalog(apps, schema_editor):
    MenuItem = apps.get_model('pours', 'MenuItem')
    Category = apps.get_model('pours', 'Category')
    MenuItem.objects.all().delete()
    Category.objects.all().delete()
    call_command('loaddata', 'catalog', app_label='pours')


class Migration(migrations.Migration):

    dependencies = [
        ('pours', '0003_menu_sprite_fields'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(replace_catalog, restore_original_catalog),
    ]
