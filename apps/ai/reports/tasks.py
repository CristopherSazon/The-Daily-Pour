from datetime import date, datetime

from django.utils import timezone

from .services import ReportService


def generate_daily_report(day=None):
    """Save the business report for one day. `day` is a date or YYYY-MM-DD."""
    return ReportService().generate(report_day(day))


def report_day(day):
    if day is None:
        return timezone.localdate()
    if isinstance(day, datetime):
        return day.date()
    if isinstance(day, date):
        return day
    try:
        return datetime.strptime(str(day), '%Y-%m-%d').date()
    except ValueError:
        raise ValueError('Use a date like 2026-11-15.') from None
