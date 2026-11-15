from django.contrib import admin

from .models import Guest


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'milk', 'sweetness', 'temperature', 'updated_at')
    search_fields = ('name', 'phone')
    readonly_fields = ('token', 'updated_at')
