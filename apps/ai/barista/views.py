import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .services import BaristaError, BaristaService, GuestService


@require_http_methods(['GET', 'POST'])
def barista(request):
    guests = GuestService()
    guest = guests.ensure(request)
    try:
        if request.method == 'GET':
            payload = BaristaService().session(guest)
        else:
            try:
                body = json.loads(request.body or b'{}')
            except json.JSONDecodeError:
                response = JsonResponse({'error': 'Send the message as JSON.'}, status=400)
                return guests.attach_cookie(response, guest)
            if not isinstance(body, dict):
                response = JsonResponse({'error': 'Send the message as JSON.'}, status=400)
                return guests.attach_cookie(response, guest)
            payload = BaristaService().reply(
                guest,
                message=body.get('message', ''),
                history=body.get('history', []),
                cart=body.get('cart', []),
                confirm_phone=body.get('confirm_phone', ''),
            )
    except BaristaError as exc:
        response = JsonResponse({'error': str(exc)}, status=503)
        return guests.attach_cookie(response, guest)
    response = JsonResponse(payload)
    return guests.attach_cookie(response, guest)
