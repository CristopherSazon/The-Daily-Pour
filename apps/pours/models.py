from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='items',
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField()
    notes = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.CharField(
        max_length=255,
        blank=True,
        help_text='Path served with the site, such as /daily-pour-signature.png.',
    )
    image_alt = models.CharField(max_length=200, blank=True)
    menu_number = models.CharField(max_length=2, blank=True)
    image_index = models.PositiveSmallIntegerField(default=0)
    featured_image = models.CharField(max_length=255, blank=True)
    method = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    featured_position = models.PositiveSmallIntegerField(null=True, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position', 'name']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gt=0),
                name='menuitem_price_positive',
            ),
            models.UniqueConstraint(
                fields=['featured_position'],
                condition=models.Q(is_featured=True),
                name='unique_featured_position',
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def number(self):
        return self.menu_number

    @property
    def price_label(self):
        amount = self.price
        if amount == amount.to_integral():
            shown = f'{int(amount)}'
        else:
            shown = f'{amount:.2f}'
        return f'₱{shown}'

    @property
    def static_image(self):
        filename = self.image.rsplit('/', 1)[-1]
        if not filename:
            return ''
        folder = 'pours/menu' if self.image.startswith('/menu/') else 'pours'
        return f'{folder}/{filename}'

    @property
    def static_featured(self):
        filename = self.featured_image.rsplit('/', 1)[-1]
        if not filename:
            return ''
        return f'pours/{filename}'


class RecipeLine(models.Model):
    item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='recipe_lines',
    )
    text = models.CharField(max_length=200)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']

    def __str__(self):
        return self.text
