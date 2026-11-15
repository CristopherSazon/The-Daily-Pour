from django.db import models

from apps.menu.modifiers import money_label


class DailyReport(models.Model):
    day = models.DateField(unique=True)
    order_count = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    facts = models.JSONField()
    headline = models.CharField(max_length=160)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-day']

    def __str__(self):
        return f'{self.day.isoformat()} · {self.order_count} orders'

    @property
    def revenue_label(self):
        return money_label(self.revenue)
