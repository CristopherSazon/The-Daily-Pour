from django.test import TestCase, override_settings

from apps.ai.barista.models import Guest
from apps.ai.barista.services import BaristaError, BaristaService, GuestService, guest_error
from apps.orders.models import Order


def reply_for(**overrides):
    payload = {
        'say': 'The honey oat latte is a soft place to land.',
        'items': [
            {
                'slug': 'honey-oat-latte',
                'reason': 'Floral and warm.',
                'modifiers': ['oat-milk', 'not-a-real-change'],
            },
            {'slug': 'not-on-the-menu', 'reason': 'Invented.', 'modifiers': []},
        ],
        'cart': [
            {'slug': 'cloud-matcha', 'quantity': 2, 'modifiers': ['iced']},
            {'slug': 'missing-drink', 'quantity': 1, 'modifiers': []},
        ],
        'guest': {
            'name': 'Ava',
            'phone': '',
            'pickup': 'Within 30 minutes',
            'milk': 'oat-milk',
            'sweetness': 'syrup',
            'temperature': 'iced',
            'note': 'Skips pastries.',
        },
    }
    payload.update(overrides)
    return payload


class BaristaServiceTests(TestCase):
    def test_reply_keeps_only_real_drinks_and_changes(self):
        guest = Guest.objects.create()
        seen = {}

        def complete(instructions, transcript):
            seen['instructions'] = instructions
            seen['transcript'] = transcript
            return reply_for()

        payload = BaristaService(complete=complete).reply(
            guest,
            message='Something warm, and add an iced matcha.',
            history=[{'role': 'user', 'content': 'Hi'}],
            cart=[],
            confirm_phone='',
        )

        self.assertEqual([item['slug'] for item in payload['items']], ['honey-oat-latte'])
        self.assertEqual(payload['items'][0]['selected_modifiers'], ['oat-milk'])
        self.assertEqual(payload['items'][0]['unit_price'], '205.00')
        self.assertEqual(payload['cart'], [
            {'slug': 'cloud-matcha', 'quantity': 2, 'modifiers': ['iced']},
        ])
        self.assertEqual(payload['pickup'], 'Within 30 minutes')
        guest.refresh_from_db()
        self.assertEqual(guest.name, 'Ava')
        self.assertEqual(guest.milk, 'oat-milk')
        self.assertEqual(guest.sweetness, '')
        self.assertEqual(guest.temperature, 'iced')
        self.assertEqual(guest.note, 'Skips pastries.')
        self.assertIn('honey-oat-latte', seen['instructions'])
        self.assertNotIn('not-on-the-menu', payload['say'])

    def test_empty_message_does_not_call_the_model(self):
        guest = Guest.objects.create(name='Ava')

        def complete(instructions, transcript):
            raise AssertionError('The model should stay quiet.')

        payload = BaristaService(complete=complete).reply(
            guest,
            message='   ',
            history=[],
            cart=[],
            confirm_phone='',
        )

        self.assertIn('Ava', payload['say'])

    def test_phone_recall_waits_for_confirmation(self):
        original = Guest.objects.create(
            name='Ava Santos',
            phone='09171234567',
            milk='oat-milk',
            usuals=[{'slug': 'honey-oat-latte', 'modifiers': ['iced'], 'quantity': 1}],
        )
        guest = Guest.objects.create()

        def complete(instructions, transcript):
            self.assertNotIn('honey-oat-latte (iced)', instructions.split('Usuals:')[1].split('Current bag:')[0])
            return reply_for(guest={
                'name': '',
                'phone': '09171234567',
                'pickup': '',
                'milk': '',
                'sweetness': '',
                'temperature': '',
                'note': '',
            })

        payload = BaristaService(complete=complete).reply(
            guest,
            message='My number is 09171234567.',
            history=[],
            cart=[],
            confirm_phone='',
        )

        guest.refresh_from_db()
        self.assertEqual(guest.usuals, [])
        self.assertEqual(guest.phone, '')
        self.assertEqual(payload['recall']['phone'], '09171234567')
        self.assertIn('Ava Santos', payload['recall']['prompt'])

        confirmed = BaristaService(complete=complete).reply(
            guest,
            message='',
            history=[],
            cart=[],
            confirm_phone='09171234567',
        )
        guest.refresh_from_db()
        original.refresh_from_db()
        self.assertEqual(guest.name, 'Ava Santos')
        self.assertEqual(guest.milk, 'oat-milk')
        self.assertEqual(guest.usuals, original.usuals)
        self.assertEqual(confirmed['items'][0]['slug'], 'honey-oat-latte')
        self.assertEqual(confirmed['items'][0]['selected_modifiers'], ['iced'])

    def test_no_credits_is_explained(self):
        class NoCredits(Exception):
            body = {'code': 'rate_limit_exceeded', 'type': 'rate_limit_exceeded'}

        self.assertIn('Groq free limit', str(guest_error(NoCredits())))

    def test_missing_key_tells_the_guest_the_barista_is_away(self):
        guest = Guest.objects.create()
        with override_settings(GROQ_API_KEY=''):
            with self.assertRaises(BaristaError):
                BaristaService().reply(guest, 'Something warm', [], [], '')


class BaristaViewTests(TestCase):
    def test_session_sets_a_guest_cookie(self):
        response = self.client.get('/barista/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('mood', response.json()['say'])
        self.assertIn('barista_guest', response.cookies)
        self.assertEqual(Guest.objects.count(), 1)

    def test_view_returns_a_checked_reply(self):
        def complete(instructions, transcript):
            return reply_for()

        service = BaristaService(complete=complete)
        with self.settings():
            from apps.ai.barista import views

            original = views.BaristaService
            views.BaristaService = lambda: service
            try:
                response = self.client.post(
                    '/barista/',
                    data={'message': 'Something warm'},
                    content_type='application/json',
                )
            finally:
                views.BaristaService = original

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['items'][0]['slug'], 'honey-oat-latte')

    def test_order_remembers_the_usual_for_this_browser(self):
        self.client.get('/barista/')
        response = self.client.post(
            '/orders/',
            data={
                'name': 'Ava Santos',
                'phone': '+63 917 123 4567',
                'pickup': 'Within 1 hour',
                'lines': [
                    {'slug': 'honey-oat-latte', 'quantity': 1, 'modifiers': ['oat-milk']},
                ],
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        guest = Guest.objects.get()
        self.assertEqual(guest.name, 'Ava Santos')
        self.assertEqual(guest.phone, '09171234567')
        self.assertEqual(guest.usuals, [
            {'slug': 'honey-oat-latte', 'modifiers': ['oat-milk'], 'quantity': 1},
        ])
        self.assertEqual(Order.objects.get().phone, '+63 917 123 4567')


class GuestServiceTests(TestCase):
    def test_same_cookie_returns_the_same_guest(self):
        request = self.client.get('/barista/').wsgi_request
        first = GuestService().ensure(request)
        request.COOKIES['barista_guest'] = str(first.token)
        second = GuestService().ensure(request)
        self.assertEqual(first.pk, second.pk)
