from django.db import models


class Order(models.Model):
    PICKUP_WINDOWS = (
        ('As soon as possible', 'As soon as possible'),
        ('Within 30 minutes', 'Within 30 minutes'),
        ('Within 1 hour', 'Within 1 hour'),
    )

    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    pickup_window = models.CharField(max_length=40, choices=PICKUP_WINDOWS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.customer_name} · {self.pickup_window}'


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(
        'pours.MenuItem',
        on_delete=models.PROTECT,
        related_name='order_lines',
    )
    quantity = models.PositiveSmallIntegerField()
    modifiers = models.JSONField(blank=True, default=list)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='orderline_quantity_positive',
            ),
        ]

    def __str__(self):
        return f'{self.quantity} × {self.item}'
