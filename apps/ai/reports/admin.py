from django.contrib import admin

from .models import DailyReport


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('day', 'order_count', 'revenue_label', 'headline', 'updated_at')
    readonly_fields = ('day', 'order_count', 'revenue', 'facts', 'headline', 'summary', 'created_at', 'updated_at')

    @admin.display(description='Revenue')
    def revenue_label(self, report):
        return report.revenue_label
