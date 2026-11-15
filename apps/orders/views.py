import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.ai.barista.services import GuestService

from .services import OrderError, OrderService


@require_POST
def place_order(request):
    guests = GuestService()
    guest = guests.ensure(request)
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        response = JsonResponse({'error': 'Send the order as JSON.'}, status=400)
        return guests.attach_cookie(response, guest)
    if not isinstance(payload, dict):
        response = JsonResponse({'error': 'Send the order as JSON.'}, status=400)
        return guests.attach_cookie(response, guest)

    try:
        order = OrderService().place(
            name=payload.get('name', ''),
            phone=payload.get('phone', ''),
            pickup=payload.get('pickup', ''),
            lines=payload.get('lines'),
        )
    except OrderError as exc:
        response = JsonResponse({'error': str(exc)}, status=400)
        return guests.attach_cookie(response, guest)
    guests.record_order(guest, order)
    response = JsonResponse({'ok': True, 'id': order.id})
    return guests.attach_cookie(response, guest)
