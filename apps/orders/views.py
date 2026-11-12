import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services import OrderError, OrderService


@require_POST
def place_order(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Send the order as JSON.'}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({'error': 'Send the order as JSON.'}, status=400)

    try:
        order = OrderService().place(
            name=payload.get('name', ''),
            phone=payload.get('phone', ''),
            pickup=payload.get('pickup', ''),
            lines=payload.get('lines'),
        )
    except OrderError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    return JsonResponse({'ok': True, 'id': order.id})
