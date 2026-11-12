from decimal import Decimal

from django.test import TestCase

from .models import MenuItem


class MenuApiTests(TestCase):
    def test_menu_lists_the_house_favorites(self):
        response = self.client.get('/api/menu/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            [item['name'] for item in payload['featured']],
            ['Honey oat latte', 'Cloud matcha', 'Butter croissant'],
        )

        honey = payload['featured'][0]
        self.assertEqual(honey['number'], '01')
        self.assertEqual(honey['category'], 'The Signature Pour')
        self.assertEqual(honey['category_label'], 'THE SIGNATURE POUR')
        self.assertEqual(honey['price'], '185.00')
        self.assertEqual(honey['price_label'], '₱185')
        self.assertEqual(honey['recipe'][0], '2 shots espresso (about 36 ml)')
        self.assertIn('honey syrup', honey['method'])

        self.assertEqual(
            [category['name'] for category in payload['categories']],
            [
                'The Daily Classics',
                'The Signature Pour',
                'The Custom Pour',
                'The Matcha Edit',
                'The Daily Bites',
            ],
        )
        slugs = {
            category['slug']: [item['slug'] for item in category['items']]
            for category in payload['categories']
        }
        self.assertEqual(
            slugs['daily-classics'],
            ['house-espresso', 'morning-americano', 'cafe-au-lait'],
        )
        self.assertEqual(
            slugs['signature-pour'],
            ['honey-oat-latte', 'brown-sugar-latte', 'orange-blossom-americano'],
        )
        self.assertEqual(
            slugs['custom-pour'],
            ['oat-cortado', 'extra-shot-cappuccino', 'half-sweet-mocha'],
        )
        self.assertEqual(
            slugs['matcha-edit'],
            ['cloud-matcha', 'warm-hojicha-latte', 'yuzu-matcha'],
        )
        self.assertEqual(
            slugs['daily-bites'],
            ['butter-croissant', 'almond-financier', 'banana-loaf'],
        )

    def test_home_renders_the_design(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Coffee for')
        self.assertContains(response, 'everyday <em>moments.</em>', html=False)
        self.assertContains(response, 'Honey oat latte')
        self.assertContains(response, 'Cloud matcha')
        self.assertContains(response, 'Butter croissant')
        self.assertContains(response, 'The Daily Classics')
        self.assertContains(response, 'Come by')
        self.assertContains(response, 'pours/site.css')
        self.assertContains(response, 'Your order')
        self.assertContains(response, 'Add to order')
        self.assertContains(response, 'As soon as possible')

    def test_price_label_keeps_centavos(self):
        item = MenuItem.objects.get(slug='cloud-matcha')
        item.price = Decimal('195.50')
        self.assertEqual(item.price_label, '₱195.50')
