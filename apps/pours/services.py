from django.templatetags.static import static

from .models import Category, MenuItem


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
            'image': static(item.static_image) if item.static_image else '',
            'image_alt': item.image_alt,
            'method': item.method,
            'recipe': [line.text for line in item.recipe_lines.all()],
        }

    def home_context(self):
        featured = self.featured_items()
        return {
            'featured': featured,
            'categories': self.categories(),
            'featured_json': [self.serialize_item(item) for item in featured],
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
