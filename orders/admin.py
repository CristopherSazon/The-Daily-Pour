from django.contrib import admin

from .models import Order, OrderLine


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'phone', 'pickup_window', 'created_at')
    list_filter = ('pickup_window',)
    search_fields = ('customer_name', 'phone')
    readonly_fields = ('created_at',)
    inlines = [OrderLineInline]
