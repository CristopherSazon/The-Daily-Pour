from django.contrib import admin

from .models import Category, MenuItem, RecipeLine

admin.site.site_header = 'The Daily Pour'
admin.site.site_title = 'The Daily Pour'
admin.site.index_title = 'Menu'


class RecipeLineInline(admin.TabularInline):
    model = RecipeLine
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'position')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('position',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('menu_number', 'name', 'category', 'price', 'is_featured')
    list_filter = ('category', 'is_featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [RecipeLineInline]
