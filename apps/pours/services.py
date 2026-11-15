from django.templatetags.static import static

from .models import Category, MenuItem
from .modifiers import for_category


class MenuService:
    def featured_items(self):
        return (
            MenuItem.objects.filter(is_featured=True)
            .select_related('category')
            .prefetch_related('recipe_lines')
            .order_by('featured_position')
        )

    def categories(self):
        return Category.objects.prefetch_related('items__recipe_lines', 'items__category')

    def catalog_items(self):
        return (
            MenuItem.objects.select_related('category')
            .prefetch_related('recipe_lines')
            .order_by('category__position', 'position', 'name')
        )

    def serialize_item(self, item):
        return {
            'number': item.number or None,
            'name': item.name,
            'slug': item.slug,
            'category': item.category.name,
            'category_label': item.category.name.upper(),
            'description': item.description,
            'notes': item.notes,
            'price': f'{item.price:.2f}',
            'price_label': item.price_label,
            'category_slug': item.category.slug,
            'image': static(item.static_image) if item.static_image else '',
            'image_index': item.image_index,
            'image_alt': item.image_alt,
            'featured_image': static(item.static_featured) if item.static_featured else '',
            'method': item.method,
            'recipe': [line.text for line in item.recipe_lines.all()],
            'modifiers': [
                {
                    'slug': modifier['slug'],
                    'label': modifier['label'],
                    'group': modifier['group'],
                    'price': f'{modifier["price"]:.2f}',
                }
                for modifier in for_category(item.category.slug)
            ],
        }

    def home_context(self):
        return {'featured': self.featured_items()}

    def catalog_document(self):
        categories = self.categories()
        return {
            'categories': [
                {
                    'name': category.name,
                    'slug': category.slug,
                    'count': len(category.items.all()),
                }
                for category in categories
            ],
            'items': [self.serialize_item(item) for item in self.catalog_items()],
        }

    def menu_payload(self):
        return {
            'featured': [self.serialize_item(item) for item in self.featured_items()],
            'categories': [
                {
                    'name': category.name,
                    'slug': category.slug,
                    'items': [self.serialize_item(item) for item in category.items.all()],
                }
                for category in self.categories()
            ],
        }
