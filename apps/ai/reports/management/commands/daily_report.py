from django.core.management.base import BaseCommand, CommandError

from apps.ai.reports.tasks import generate_daily_report


class Command(BaseCommand):
    help = 'Generate the daily business report.'

    def add_arguments(self, parser):
        parser.add_argument('--date', dest='day', help='Report date as YYYY-MM-DD. Defaults to today.')

    def handle(self, *args, **options):
        try:
            report = generate_daily_report(options['day'])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f'{report.day.isoformat()} · {report.order_count} orders · {report.revenue_label}')
        self.stdout.write(report.headline)
