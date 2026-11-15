from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.ai.integrations.groq import GroqError
from apps.ai.reports.models import DailyReport
from apps.ai.reports.services import ReportService
from apps.ai.reports.tasks import generate_daily_report
from apps.menu.models import Product
from apps.orders.models import Order, OrderLine


def at(day, hour=12):
    return timezone.make_aware(datetime.combine(day, time(hour, 0)))


def order_on(day, product, quantity, unit_price, pickup='As soon as possible'):
    order = Order.objects.create(
        customer_name='Ava Santos',
        phone='09171234567',
        pickup_window=pickup,
    )
    order.created_at = at(day)
    order.save(update_fields=['created_at'])
    OrderLine.objects.create(
        order=order,
        item=product,
        quantity=quantity,
        modifiers=[],
        unit_price=unit_price,
    )
    return order


class DailyReportTests(TestCase):
    def test_report_totals_only_that_day(self):
        day = date(2026, 11, 15)
        latte = Product.objects.get(slug='honey-oat-latte')
        croissant = Product.objects.get(slug='butter-croissant')
        order_on(day, latte, 2, Decimal('185.00'), 'Within 30 minutes')
        order_on(day, croissant, 1, Decimal('145.00'), 'As soon as possible')
        order_on(day - timedelta(days=1), latte, 4, Decimal('185.00'))
        seen = {}

        def complete(instructions, messages):
            seen['instructions'] = instructions
            return {'headline': 'The latte led', 'summary': 'Two orders, and the honey oat latte was the favorite.'}

        report = ReportService(complete=complete).generate(day)

        self.assertEqual(report.order_count, 2)
        self.assertEqual(report.revenue, Decimal('515.00'))
        self.assertEqual(report.facts['items_sold'], 3)
        self.assertEqual(report.facts['average_ticket'], '257.50')
        self.assertEqual(report.facts['top_items'][0]['slug'], 'honey-oat-latte')
        self.assertEqual(report.headline, 'The latte led')
        self.assertIn('₱515', seen['instructions'])
        self.assertEqual(report.facts['top_items'][0]['quantity'], 2)

    def test_quiet_day_skips_the_model(self):
        def complete(instructions, messages):
            raise AssertionError('A quiet day does not need the model.')

        report = ReportService(complete=complete).generate(date(2026, 11, 15))

        self.assertEqual(report.order_count, 0)
        self.assertEqual(report.revenue, Decimal('0.00'))
        self.assertEqual(report.headline, 'A quiet day')
        self.assertEqual(report.summary, 'No orders came in.')

    def test_a_failed_model_still_saves_the_numbers(self):
        day = date(2026, 11, 15)
        latte = Product.objects.get(slug='honey-oat-latte')
        order_on(day, latte, 1, Decimal('185.00'))

        def complete(instructions, messages):
            raise GroqError('rate_limit')

        report = ReportService(complete=complete).generate(day)

        self.assertEqual(report.order_count, 1)
        self.assertEqual(report.revenue, Decimal('185.00'))
        self.assertEqual(report.headline, '1 order, ₱185')
        self.assertIn('Honey oat latte', report.summary)

    def test_running_again_updates_the_same_day(self):
        day = date(2026, 11, 15)
        first = ReportService(complete=lambda instructions, messages: {
            'headline': 'First',
            'summary': 'First note.',
        }).generate(day)
        latte = Product.objects.get(slug='honey-oat-latte')
        order_on(day, latte, 1, Decimal('185.00'))
        second = ReportService(complete=lambda instructions, messages: {
            'headline': 'Second',
            'summary': 'Second note.',
        }).generate(day)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(DailyReport.objects.count(), 1)
        self.assertEqual(second.order_count, 1)
        self.assertEqual(second.headline, 'Second')

    def test_task_reads_a_date_string(self):
        report = generate_daily_report('2026-11-15')

        self.assertEqual(report.day, date(2026, 11, 15))
        self.assertEqual(DailyReport.objects.get().headline, 'A quiet day')

    @override_settings(GROQ_API_KEY='')
    def test_missing_key_still_saves_the_report(self):
        day = date(2026, 11, 15)
        latte = Product.objects.get(slug='honey-oat-latte')
        order_on(day, latte, 1, Decimal('185.00'))

        report = ReportService().generate(day)

        self.assertEqual(report.revenue, Decimal('185.00'))
        self.assertEqual(report.headline, '1 order, ₱185')


class DailyReportCommandTests(TestCase):
    def test_command_writes_the_saved_report(self):
        output = StringIO()
        call_command('daily_report', day='2026-11-15', stdout=output)

        self.assertIn('2026-11-15 · 0 orders · ₱0', output.getvalue())
        self.assertIn('A quiet day', output.getvalue())
        self.assertEqual(DailyReport.objects.get().day, date(2026, 11, 15))

    def test_command_rejects_a_bad_date(self):
        with self.assertRaises(CommandError):
            call_command('daily_report', day='tomorrow')
