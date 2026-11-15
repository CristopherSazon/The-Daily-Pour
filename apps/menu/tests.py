from decimal import Decimal

from django.test import TestCase

from .models import Product


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
        self.assertEqual(honey['recipe'][0], '2 shots espresso')
        self.assertIn('honey', honey['method'])

        self.assertEqual(
            [category['name'] for category in payload['categories']],
            [
                'Daily Classics',
                'The Signature Pour',
                'The Custom Pour',
                'The Matcha Edit',
                'The Daily Bites',
            ],
        )
        self.assertEqual(
            [len(category['items']) for category in payload['categories']],
            [6, 6, 6, 6, 6],
        )
        self.assertEqual(payload['categories'][0]['items'][0]['slug'], 'double-espresso')
        self.assertEqual(payload['categories'][1]['items'][0]['slug'], 'honey-oat-latte')
        honey_modifiers = [modifier['slug'] for modifier in payload['categories'][1]['items'][0]['modifiers']]
        self.assertIn('oat-milk', honey_modifiers)
        self.assertEqual(payload['categories'][4]['items'][-1]['modifiers'], [])

    def test_home_renders_the_design(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Coffee for')
        self.assertContains(response, 'everyday <em>moments.</em>', html=False)
        self.assertContains(response, 'Honey oat latte')
        self.assertContains(response, 'Cloud matcha')
        self.assertContains(response, 'Butter croissant')
        self.assertContains(response, 'Explore all 30 favorites')
        self.assertContains(response, 'VIEW THE FULL MENU')
        self.assertContains(response, 'href="/menu/"')
        self.assertContains(response, 'Come by')
        self.assertContains(response, 'menu/site.css')
        self.assertContains(response, 'Ask the barista')

    def test_menu_page_lists_every_collection(self):
        response = self.client.get('/menu/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Find your')
        self.assertContains(response, 'everyday.</em>', html=False)
        self.assertContains(response, 'Daily Classics')
        self.assertContains(response, 'Double espresso')
        self.assertContains(response, 'Pandan cream cold brew')
        self.assertContains(response, 'Dirty matcha')
        self.assertContains(response, 'Chocolate chunk cookie')
        self.assertContains(response, 'Find a favorite')
        self.assertContains(response, 'Your order')
        self.assertContains(response, 'Ask the barista')

    def test_price_label_keeps_centavos(self):
        item = Product.objects.get(slug='cloud-matcha')
        item.price = Decimal('195.50')
        self.assertEqual(item.price_label, '₱195.50')
