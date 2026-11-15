from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.ai.integrations.groq import GroqClient, GroqError
from apps.menu.modifiers import money_label
from apps.orders.models import Order, OrderLine

from .models import DailyReport


REPORT_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'headline': {'type': 'string'},
        'summary': {'type': 'string'},
    },
    'required': ['headline', 'summary'],
}


class ReportService:
    def __init__(self, complete=None):
        self.complete = complete or default_complete

    def generate(self, day):
        facts = self.facts(day)
        headline, summary = self._narrative(facts)
        report, _created = DailyReport.objects.update_or_create(
            day=day,
            defaults={
                'order_count': facts['orders'],
                'revenue': Decimal(facts['revenue']),
                'facts': facts,
                'headline': headline,
                'summary': summary,
            },
        )
        return report

    def facts(self, day):
        start = timezone.make_aware(datetime.combine(day, time.min))
        orders = list(Order.objects.filter(created_at__gte=start, created_at__lt=start + timedelta(days=1)))
        lines = OrderLine.objects.filter(order__in=orders).select_related('item')
        revenue = Decimal('0.00')
        items_sold = 0
        by_item = {}
        for line in lines:
            total = line.unit_price * line.quantity
            revenue += total
            items_sold += line.quantity
            bucket = by_item.setdefault(line.item.slug, {
                'name': line.item.name,
                'slug': line.item.slug,
                'quantity': 0,
                'revenue': Decimal('0.00'),
            })
            bucket['quantity'] += line.quantity
            bucket['revenue'] += total
        order_count = len(orders)
        if order_count:
            average = (revenue / order_count).quantize(Decimal('0.01'))
        else:
            average = Decimal('0.00')
        ranked = sorted(by_item.values(), key=lambda item: (-item['quantity'], item['name']))
        top_items = [
            {
                'name': item['name'],
                'slug': item['slug'],
                'quantity': item['quantity'],
                'revenue': f'{item["revenue"]:.2f}',
            }
            for item in ranked[:5]
        ]
        pickup_counts = {}
        for order in orders:
            pickup_counts[order.pickup_window] = pickup_counts.get(order.pickup_window, 0) + 1
        pickups = [
            {'window': window, 'orders': count}
            for window, count in sorted(pickup_counts.items(), key=lambda item: (-item[1], item[0]))
        ]
        return {
            'day': day.isoformat(),
            'orders': order_count,
            'items_sold': items_sold,
            'revenue': f'{revenue:.2f}',
            'average_ticket': f'{average:.2f}',
            'top_items': top_items,
            'pickups': pickups,
        }

    def _narrative(self, facts):
        plain_headline, plain_summary = plain_narrative(facts)
        if facts['orders'] == 0:
            return plain_headline, plain_summary
        try:
            raw = self.complete(self._instructions(facts), [{'role': 'user', 'content': 'Write the daily report.'}])
        except GroqError:
            return plain_headline, plain_summary
        if not isinstance(raw, dict):
            return plain_headline, plain_summary
        headline = str(raw.get('headline') or '').strip()[:160]
        summary = str(raw.get('summary') or '').strip()[:500]
        return headline or plain_headline, summary or plain_summary

    def _instructions(self, facts):
        items = '\n'.join(
            f"{item['name']} × {item['quantity']} ({money_label(Decimal(item['revenue']))})"
            for item in facts['top_items']
        ) or 'none'
        pickups = '\n'.join(
            f"{pickup['window']}: {pickup['orders']}"
            for pickup in facts['pickups']
        ) or 'none'
        return (
            'You write the daily note for The Daily Pour. Use only the figures below. '
            'Do not invent orders, money, drinks, or hours. '
            'headline is one short line. summary is two sentences.\n\n'
            f"Day: {facts['day']}\n"
            f"Orders: {facts['orders']}\n"
            f"Items sold: {facts['items_sold']}\n"
            f"Revenue: {money_label(Decimal(facts['revenue']))}\n"
            f"Average ticket: {money_label(Decimal(facts['average_ticket']))}\n"
            f"Top items:\n{items}\n"
            f"Pickup windows:\n{pickups}"
        )


def plain_narrative(facts):
    if facts['orders'] == 0:
        return 'A quiet day', 'No orders came in.'
    lead = facts['top_items'][0]['name'] if facts['top_items'] else 'The bar'
    noun = 'order' if facts['orders'] == 1 else 'orders'
    headline = f"{facts['orders']} {noun}, {money_label(Decimal(facts['revenue']))}"
    summary = f"{lead} led the day, with {facts['items_sold']} items sold."
    return headline, summary


def default_complete(instructions, messages):
    return GroqClient().complete(
        instructions,
        messages,
        schema=REPORT_SCHEMA,
        name='daily_report',
        model=settings.BARISTA_MODEL,
    )
