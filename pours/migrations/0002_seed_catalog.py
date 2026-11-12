from django.db import migrations

CATEGORIES = [
    {'name': 'The Daily Classics', 'slug': 'daily-classics', 'position': 1},
    {'name': 'The Signature Pour', 'slug': 'signature-pour', 'position': 2},
    {'name': 'The Custom Pour', 'slug': 'custom-pour', 'position': 3},
    {'name': 'The Matcha Edit', 'slug': 'matcha-edit', 'position': 4},
    {'name': 'The Daily Bites', 'slug': 'daily-bites', 'position': 5},
]

ITEMS = [
    {
        'name': 'Honey oat latte',
        'slug': 'honey-oat-latte',
        'category': 'signature-pour',
        'description': 'A little floral honey, a silky oat pour, and our house espresso.',
        'notes': 'Smooth and mellow, with a soft honey finish. Available iced or warm.',
        'price': '185.00',
        'image': '/daily-pour-signature.png',
        'image_alt': 'Iced honey oat latte on a warm wooden café table',
        'method': (
            'Stir the honey syrup into freshly pulled espresso. '
            'Pour over ice, add oat milk, and give it a gentle swirl.'
        ),
        'is_featured': True,
        'featured_position': 1,
        'position': 1,
        'recipe': [
            '2 shots espresso (about 36 ml)',
            '180 ml oat milk',
            '10 ml honey syrup',
            'Ice, to fill',
        ],
    },
    {
        'name': 'Cloud matcha',
        'slug': 'cloud-matcha',
        'category': 'matcha-edit',
        'description': 'Bright ceremonial matcha, softly whisked and finished with oat milk.',
        'notes': 'Fresh, gently grassy, and creamy. Ask for it warm instead of iced.',
        'price': '195.00',
        'image': '/daily-pour-matcha.png',
        'image_alt': 'Layered iced matcha latte in a clear glass',
        'method': (
            'Sift and whisk matcha with warm water until smooth and lightly frothy. '
            'Pour over ice and oat milk.'
        ),
        'is_featured': True,
        'featured_position': 2,
        'position': 1,
        'recipe': [
            '2 g matcha powder',
            '30 ml warm water (about 80°C)',
            '180 ml oat milk',
            'Ice, to fill',
        ],
    },
    {
        'name': 'Butter croissant',
        'slug': 'butter-croissant',
        'category': 'daily-bites',
        'description': 'Golden, flaky, and even better with your first sip of the day.',
        'notes': 'Crisp at the edges, tender inside. Contains wheat, milk, and egg.',
        'price': '145.00',
        'image': '/daily-pour-pastry.png',
        'image_alt': 'Golden butter croissant on a small ceramic plate',
        'method': (
            'Layer butter through the dough, fold and chill between turns, '
            'proof until airy, then bake until deeply golden.'
        ),
        'is_featured': True,
        'featured_position': 3,
        'position': 1,
        'recipe': [
            'Wheat flour and cultured butter',
            'Milk, yeast, sugar, and sea salt',
            'Egg wash for a glossy finish',
        ],
    },
]


def seed(apps, schema_editor):
    Category = apps.get_model('pours', 'Category')
    MenuItem = apps.get_model('pours', 'MenuItem')
    RecipeLine = apps.get_model('pours', 'RecipeLine')

    categories = {
        row['slug']: Category.objects.create(
            name=row['name'],
            slug=row['slug'],
            position=row['position'],
        )
        for row in CATEGORIES
    }

    for row in ITEMS:
        item = MenuItem.objects.create(
            category=categories[row['category']],
            name=row['name'],
            slug=row['slug'],
            description=row['description'],
            notes=row['notes'],
            price=row['price'],
            image=row['image'],
            image_alt=row['image_alt'],
            method=row['method'],
            is_featured=row['is_featured'],
            featured_position=row['featured_position'],
            position=row['position'],
        )
        RecipeLine.objects.bulk_create(
            [
                RecipeLine(item=item, text=text, position=index)
                for index, text in enumerate(row['recipe'], start=1)
            ]
        )


def unseed(apps, schema_editor):
    MenuItem = apps.get_model('pours', 'MenuItem')
    Category = apps.get_model('pours', 'Category')
    MenuItem.objects.filter(slug__in=[row['slug'] for row in ITEMS]).delete()
    Category.objects.filter(slug__in=[row['slug'] for row in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pours', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
