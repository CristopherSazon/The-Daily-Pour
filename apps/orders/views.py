import json

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.pours.models import MenuItem

from .models import Order, OrderLine


@require_POST
def place_order(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Send the order as JSON.'}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({'error': 'Send the order as JSON.'}, status=400)

    name = str(payload.get('name', '')).strip()
    phone = str(payload.get('phone', '')).strip()
    pickup = str(payload.get('pickup', '')).strip()
    raw_lines = payload.get('lines')
    windows = {choice for choice, _label in Order.PICKUP_WINDOWS}
    if (
        not name
        or len(name) > 120
        or not phone
        or len(phone) > 40
        or pickup not in windows
        or not isinstance(raw_lines, list)
        or not raw_lines
    ):
        return JsonResponse(
            {'error': 'Add your name, phone, pickup time, and at least one item.'},
            status=400,
        )

    quantities = {}
    for line in raw_lines:
        if not isinstance(line, dict):
            return JsonResponse({'error': 'Each item needs a slug and a quantity.'}, status=400)
        slug = str(line.get('slug', '')).strip()
        quantity = line.get('quantity')
        if (
            not slug
            or isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity < 1
            or quantity > 99
        ):
            return JsonResponse({'error': 'Each item needs a quantity from 1 to 99.'}, status=400)
        quantities[slug] = quantities.get(slug, 0) + quantity
        if quantities[slug] > 99:
            return JsonResponse({'error': 'Each item needs a quantity from 1 to 99.'}, status=400)

    items = {item.slug: item for item in MenuItem.objects.filter(slug__in=quantities)}
    if set(items) != set(quantities):
        return JsonResponse({'error': 'One of those items is no longer on the menu.'}, status=400)

    with transaction.atomic():
        order = Order.objects.create(
            customer_name=name,
            phone=phone,
            pickup_window=pickup,
        )
        OrderLine.objects.bulk_create(
            [
                OrderLine(
                    order=order,
                    item=items[slug],
                    quantity=quantity,
                    unit_price=items[slug].price,
                )
                for slug, quantity in quantities.items()
            ]
        )
    return JsonResponse({'ok': True, 'id': order.id})
