from django.db import transaction

from apps.pours.models import MenuItem

from .models import Order, OrderLine


class OrderError(Exception):
    pass


class OrderService:
    def place(self, name, phone, pickup, lines):
        customer_name = str(name).strip()
        customer_phone = str(phone).strip()
        pickup_window = str(pickup).strip()
        windows = {choice for choice, _label in Order.PICKUP_WINDOWS}
        if (
            not customer_name
            or len(customer_name) > 120
            or not customer_phone
            or len(customer_phone) > 40
            or pickup_window not in windows
            or not isinstance(lines, list)
            or not lines
        ):
            raise OrderError('Add your name, phone, pickup time, and at least one item.')

        quantities = {}
        for line in lines:
            if not isinstance(line, dict):
                raise OrderError('Each item needs a slug and a quantity.')
            slug = str(line.get('slug', '')).strip()
            quantity = line.get('quantity')
            if (
                not slug
                or isinstance(quantity, bool)
                or not isinstance(quantity, int)
                or quantity < 1
                or quantity > 99
            ):
                raise OrderError('Each item needs a quantity from 1 to 99.')
            quantities[slug] = quantities.get(slug, 0) + quantity
            if quantities[slug] > 99:
                raise OrderError('Each item needs a quantity from 1 to 99.')

        items = {item.slug: item for item in MenuItem.objects.filter(slug__in=quantities)}
        if set(items) != set(quantities):
            raise OrderError('One of those items is no longer on the menu.')

        with transaction.atomic():
            order = Order.objects.create(
                customer_name=customer_name,
                phone=customer_phone,
                pickup_window=pickup_window,
            )
            OrderLine.objects.bulk_create(
                [
                    OrderLine(
                        order=order,
                        item=items[slug],
                        quantity=quantity,
                        unit_price=items[slug].price,
                    )
                    for slug, quantity in quantities.items()
                ]
            )
        return order
