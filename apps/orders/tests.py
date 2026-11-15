from decimal import Decimal

from django.test import TestCase

from .models import Order, OrderLine


class PlaceOrderTests(TestCase):
    def test_place_order_saves_the_bag(self):
        response = self.client.post(
            '/orders/',
            data={
                'name': 'Ava Santos',
                'phone': '09171234567',
                'pickup': 'Within 30 minutes',
                'lines': [
                    {'slug': 'honey-oat-latte', 'quantity': 2},
                    {'slug': 'butter-croissant', 'quantity': 1},
                ],
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get()
        self.assertEqual(order.customer_name, 'Ava Santos')
        self.assertEqual(order.pickup_window, 'Within 30 minutes')
        lines = {line.item.slug: line for line in order.lines.select_related('item')}
        self.assertEqual(lines['honey-oat-latte'].quantity, 2)
        self.assertEqual(lines['honey-oat-latte'].unit_price, Decimal('185.00'))
        self.assertEqual(lines['butter-croissant'].quantity, 1)
        self.assertEqual(lines['honey-oat-latte'].modifiers, [])

    def test_place_order_prices_milk_and_ice(self):
        response = self.client.post(
            '/orders/',
            data={
                'name': 'Ava Santos',
                'phone': '09171234567',
                'pickup': 'As soon as possible',
                'lines': [
                    {
                        'slug': 'honey-oat-latte',
                        'quantity': 1,
                        'modifiers': ['iced', 'oat-milk'],
                    },
                ],
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        line = OrderLine.objects.get()
        self.assertEqual(line.modifiers, ['oat-milk', 'iced'])
        self.assertEqual(line.unit_price, Decimal('205.00'))

    def test_place_order_rejects_a_modifier_on_a_bite(self):
        response = self.client.post(
            '/orders/',
            data={
                'name': 'Ava Santos',
                'phone': '09171234567',
                'pickup': 'As soon as possible',
                'lines': [
                    {'slug': 'butter-croissant', 'quantity': 1, 'modifiers': ['oat-milk']},
                ],
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_place_order_rejects_an_empty_bag(self):
        response = self.client.post(
            '/orders/',
            data={'name': 'Ava', 'phone': '0917', 'pickup': 'Within 1 hour', 'lines': []},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderLine.objects.count(), 0)
