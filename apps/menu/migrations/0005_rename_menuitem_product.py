from django.db import migrations


def rename_legacy_tables(apps, schema_editor):
    existing = set(schema_editor.connection.introspection.table_names())
    with schema_editor.connection.cursor() as cursor:
        for old, new in (
            ('pours_category', 'menu_category'),
            ('pours_menuitem', 'menu_menuitem'),
            ('pours_recipeline', 'menu_recipeline'),
        ):
            if old in existing and new not in existing:
                cursor.execute(f'ALTER TABLE {old} RENAME TO {new}')


def retarget_permissions(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "UPDATE django_content_type SET app_label = 'menu' WHERE app_label = 'pours'"
        )
        cursor.execute(
            "UPDATE django_content_type SET model = 'product' "
            "WHERE app_label = 'menu' AND model = 'menuitem'"
        )
        cursor.execute(
            "UPDATE auth_permission SET codename = replace(codename, 'menuitem', 'product') "
            "WHERE codename LIKE '%%menuitem%%'"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0004_load_menu_fixture'),
    ]

    operations = [
        migrations.RunPython(rename_legacy_tables, migrations.RunPython.noop),
        migrations.RenameModel('MenuItem', 'Product'),
        migrations.RunPython(retarget_permissions, migrations.RunPython.noop),
    ]
