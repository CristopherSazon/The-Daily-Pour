import json
import re
import uuid

from django.conf import settings

from apps.orders.models import Order
from apps.pours.models import MenuItem
from apps.pours.modifiers import for_category, keep_known, modifier_total, money_label
from apps.pours.services import MenuService

from .models import Guest


COOKIE = 'barista_guest'
COOKIE_AGE = 60 * 60 * 24 * 180
PHONE_RE = re.compile(r'(?:\+?63|0)9\d{9}')
PICKUP_WINDOWS = {choice for choice, _label in Order.PICKUP_WINDOWS}
PREFERENCE_GROUPS = ('milk', 'sweetness', 'temperature')

REPLY_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'say': {'type': 'string'},
        'items': {
            'type': 'array',
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'slug': {'type': 'string'},
                    'reason': {'type': 'string'},
                    'modifiers': {'type': 'array', 'items': {'type': 'string'}},
                },
                'required': ['slug', 'reason', 'modifiers'],
            },
        },
        'cart': {
            'type': 'array',
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'slug': {'type': 'string'},
                    'quantity': {'type': 'integer'},
                    'modifiers': {'type': 'array', 'items': {'type': 'string'}},
                },
                'required': ['slug', 'quantity', 'modifiers'],
            },
        },
        'guest': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'name': {'type': 'string'},
                'phone': {'type': 'string'},
                'pickup': {'type': 'string'},
                'milk': {'type': 'string'},
                'sweetness': {'type': 'string'},
                'temperature': {'type': 'string'},
                'note': {'type': 'string'},
            },
            'required': ['name', 'phone', 'pickup', 'milk', 'sweetness', 'temperature', 'note'],
        },
    },
    'required': ['say', 'items', 'cart', 'guest'],
}


class BaristaError(Exception):
    pass


def normalize_phone(value):
    digits = ''.join(character for character in str(value) if character.isdigit())
    if digits.startswith('63') and len(digits) == 12:
        digits = '0' + digits[2:]
    return digits[:40]


def phones_in(text):
    found = []
    for match in PHONE_RE.findall(str(text or '')):
        phone = normalize_phone(match)
        if phone and phone not in found:
            found.append(phone)
    return found


class GuestService:
    def ensure(self, request):
        raw = request.COOKIES.get(COOKIE, '')
        try:
            token = uuid.UUID(str(raw))
        except ValueError:
            token = None
        if token is not None:
            guest = Guest.objects.filter(token=token).first()
            if guest is not None:
                guest.fresh_cookie = False
                return guest
        guest = Guest.objects.create()
        guest.fresh_cookie = True
        return guest

    def attach_cookie(self, response, guest):
        if getattr(guest, 'fresh_cookie', False):
            response.set_cookie(
                COOKIE,
                str(guest.token),
                max_age=COOKIE_AGE,
                httponly=True,
                samesite='Lax',
                path='/',
            )
        return response

    def record_order(self, guest, order):
        guest.name = order.customer_name[:120]
        guest.phone = normalize_phone(order.phone)
        guest.usuals = [
            {
                'slug': line.item.slug,
                'modifiers': list(line.modifiers or []),
                'quantity': line.quantity,
            }
            for line in order.lines.select_related('item')
        ][:6]
        guest.save()

    def find_other(self, guest, phone):
        phone = normalize_phone(phone)
        if not phone:
            return None
        return (
            Guest.objects.exclude(pk=guest.pk)
            .filter(phone=phone)
            .order_by('-updated_at')
            .first()
        )

    def apply_recall(self, guest, phone):
        other = self.find_other(guest, phone)
        if other is None:
            return False
        guest.name = other.name
        guest.phone = other.phone
        guest.milk = other.milk
        guest.sweetness = other.sweetness
        guest.temperature = other.temperature
        guest.note = other.note
        guest.usuals = other.usuals
        guest.save()
        return True


class BaristaService:
    def __init__(self, complete=None):
        self.complete = complete or default_complete
        self.guests = GuestService()

    def session(self, guest):
        return self._payload(guest, say=self._greeting(guest), items=self._usual_items(guest))

    def reply(self, guest, message, history, cart, confirm_phone):
        if confirm_phone and self.guests.apply_recall(guest, confirm_phone):
            guest.refresh_from_db()
        text = str(message or '').strip()[:400]
        if not text:
            return self.session(guest)

        recall = self._recall_for(guest, phones_in(text))
        raw = self.complete(self._instructions(guest, cart), self._transcript(history, text))
        if not isinstance(raw, dict):
            raise BaristaError('The barista is away from the bar right now.')
        pickup, model_recall = self._store_guest_updates(guest, raw.get('guest'))
        if recall is None:
            recall = model_recall
        guest.refresh_from_db()
        say = str(raw.get('say') or '').strip()[:500] or "Here's what I'd pour."
        return self._payload(
            guest,
            say=say,
            items=self._suggestions(raw.get('items')),
            cart=self._cart(raw.get('cart')),
            pickup=pickup,
            recall=recall,
        )

    def _payload(self, guest, say, items, cart=None, pickup='', recall=None):
        return {
            'say': say,
            'items': items,
            'cart': cart or [],
            'recall': recall,
            'preferences': {
                'milk': guest.milk,
                'sweetness': guest.sweetness,
                'temperature': guest.temperature,
            },
            'name': guest.name,
            'phone': guest.phone,
            'pickup': pickup,
        }

    def _greeting(self, guest):
        usuals = self._usual_items(guest)
        drinks = ', '.join(item['name'] for item in usuals)
        if guest.name and drinks:
            return f'Welcome back, {guest.name}. Last time you had {drinks}.'
        if drinks:
            return f'Welcome back. Last time you had {drinks}.'
        if guest.name:
            return f'Welcome back, {guest.name}. Tell me what you are in the mood for.'
        return 'Tell me what you are in the mood for.'

    def _usual_items(self, guest):
        entries = guest.usuals if isinstance(guest.usuals, list) else []
        slugs = [
            entry.get('slug')
            for entry in entries
            if isinstance(entry, dict) and entry.get('slug')
        ]
        found = self._items(slugs)
        items = []
        for entry in entries:
            if not isinstance(entry, dict) or len(items) == 3:
                continue
            item = found.get(str(entry.get('slug', '')).strip())
            if item is None:
                continue
            modifiers = keep_known(item.category.slug, entry.get('modifiers'))
            items.append(self._present(item, 'Your usual.', modifiers))
        return items

    def _suggestions(self, raw):
        if not isinstance(raw, list):
            return []
        found = self._items(
            str(entry.get('slug', '')).strip()
            for entry in raw
            if isinstance(entry, dict)
        )
        items = []
        seen = set()
        for entry in raw:
            if not isinstance(entry, dict) or len(items) == 3:
                continue
            slug = str(entry.get('slug', '')).strip()
            item = found.get(slug)
            if item is None or slug in seen:
                continue
            seen.add(slug)
            modifiers = keep_known(item.category.slug, entry.get('modifiers'))
            reason = str(entry.get('reason') or '').strip()[:160]
            items.append(self._present(item, reason, modifiers))
        return items

    def _cart(self, raw):
        if not isinstance(raw, list):
            return []
        found = self._items(
            str(entry.get('slug', '')).strip()
            for entry in raw
            if isinstance(entry, dict)
        )
        lines = []
        for entry in raw:
            if not isinstance(entry, dict) or len(lines) == 4:
                continue
            item = found.get(str(entry.get('slug', '')).strip())
            if item is None:
                continue
            quantity = entry.get('quantity', 1)
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
                quantity = 1
            lines.append({
                'slug': item.slug,
                'quantity': min(quantity, 99),
                'modifiers': keep_known(item.category.slug, entry.get('modifiers')),
            })
        return lines

    def _present(self, item, reason, modifiers):
        payload = MenuService().serialize_item(item)
        total = item.price + modifier_total(modifiers)
        payload.update({
            'reason': reason,
            'selected_modifiers': modifiers,
            'unit_price': f'{total:.2f}',
            'unit_price_label': money_label(total),
        })
        return payload

    def _items(self, slugs):
        wanted = [slug for slug in slugs if slug]
        if not wanted:
            return {}
        return {
            item.slug: item
            for item in MenuItem.objects.select_related('category').prefetch_related('recipe_lines').filter(slug__in=wanted)
        }

    def _recall_for(self, guest, phones):
        for phone in phones:
            if phone == guest.phone:
                continue
            other = self.guests.find_other(guest, phone)
            if other is not None:
                return self._recall_payload(other)
        return None

    def _recall_payload(self, other):
        usuals = self._usual_items(other)
        drink = usuals[0]['name'] if usuals else 'a drink'
        if other.name:
            prompt = f'Are you {other.name}? Last time you had {drink}.'
        else:
            prompt = f'Use the usual saved for this number? Last time it was {drink}.'
        return {'phone': other.phone, 'prompt': prompt}

    def _store_guest_updates(self, guest, raw):
        if not isinstance(raw, dict):
            raw = {}
        allowed = {
            modifier['slug']
            for modifier in for_category('daily-classics')
        }
        by_group = {}
        for modifier in for_category('daily-classics'):
            by_group.setdefault(modifier['group'], set()).add(modifier['slug'])
        for field in PREFERENCE_GROUPS:
            value = str(raw.get(field) or '').strip()
            if value in by_group.get(field, set()) and value in allowed:
                setattr(guest, field, value)
        note = str(raw.get('note') or '').strip()
        if note:
            guest.note = note[:200]
        name = str(raw.get('name') or '').strip()
        if name:
            guest.name = name[:120]
        recall = None
        phone = normalize_phone(raw.get('phone') or '')
        if phone:
            if phone == guest.phone:
                pass
            else:
                other = self.guests.find_other(guest, phone)
                if other is not None:
                    recall = self._recall_payload(other)
                else:
                    guest.phone = phone
        pickup = str(raw.get('pickup') or '').strip()
        if pickup not in PICKUP_WINDOWS:
            pickup = ''
        guest.save()
        return pickup, recall

    def _instructions(self, guest, cart):
        menu = []
        for item in MenuService().catalog_items():
            modifiers = ', '.join(
                modifier['slug'] for modifier in for_category(item.category.slug)
            ) or 'none'
            menu.append(
                f'{item.slug} | {item.name} | {item.category.name} | {item.price_label} | '
                f'{item.description} | modifiers: {modifiers}'
            )
        prefs = []
        if guest.milk:
            prefs.append(f'milk {guest.milk}')
        if guest.sweetness:
            prefs.append(f'sweetness {guest.sweetness}')
        if guest.temperature:
            prefs.append(f'temperature {guest.temperature}')
        if guest.note:
            prefs.append(guest.note)
        return (
            'You are the barista at The Daily Pour. Suggest only items from this menu. '
            'Use each slug exactly. Modifiers must come from that item\'s list, or be empty '
            'for the house recipe. Put items in cart only when the guest asks to add or order them. '
            'Quantities are whole numbers from 1 to 99. Fill guest fields only when the guest '
            'states them, and leave the others as empty strings. pickup must be empty or one of: '
            'As soon as possible, Within 30 minutes, Within 1 hour. Keep say to two short sentences. '
            'You only know the preferences written below.\n\n'
            f'Guest name: {guest.name or "unknown"}\n'
            f'Preferences: {", ".join(prefs) or "none"}\n'
            f'Usuals: {self._usual_text(guest)}\n'
            f'Current bag: {self._bag_summary(cart)}\n\n'
            'Menu:\n' + '\n'.join(menu)
        )

    def _usual_text(self, guest):
        entries = guest.usuals if isinstance(guest.usuals, list) else []
        parts = []
        for entry in entries[:6]:
            if not isinstance(entry, dict):
                continue
            slug = str(entry.get('slug', '')).strip()
            if not slug:
                continue
            modifiers = entry.get('modifiers') if isinstance(entry.get('modifiers'), list) else []
            if modifiers:
                parts.append(slug + ' (' + ', '.join(str(modifier) for modifier in modifiers) + ')')
            else:
                parts.append(slug)
        return ', '.join(parts) or 'none'

    def _bag_summary(self, cart):
        if not isinstance(cart, list):
            return 'empty'
        found = self._items(
            str(line.get('slug', '')).strip()
            for line in cart
            if isinstance(line, dict)
        )
        parts = []
        for line in cart[:8]:
            if not isinstance(line, dict):
                continue
            item = found.get(str(line.get('slug', '')).strip())
            if item is None:
                continue
            quantity = line.get('quantity', 1)
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
                quantity = 1
            modifiers = keep_known(item.category.slug, line.get('modifiers'))
            label = item.name if not modifiers else item.name + ' (' + ', '.join(modifiers) + ')'
            parts.append(f'{min(quantity, 99)} × {label}')
        return ', '.join(parts) or 'empty'

    def _transcript(self, history, message):
        transcript = []
        if isinstance(history, list):
            for entry in history[-8:]:
                if not isinstance(entry, dict):
                    continue
                role = entry.get('role')
                content = str(entry.get('content') or '').strip()[:400]
                if role in ('user', 'assistant') and content:
                    transcript.append({'role': role, 'content': content})
        transcript.append({'role': 'user', 'content': message})
        return transcript


def guest_error(exc):
    body = getattr(exc, 'body', None)
    if isinstance(body, dict) and isinstance(body.get('error'), dict):
        body = body['error']
    if not isinstance(body, dict):
        body = {}
    code = str(body.get('code') or '')
    kind = str(body.get('type') or '')
    if code in {'credit_balance_exhausted', 'rate_limit_exceeded'} or kind in {'insufficient_quota', 'rate_limit_exceeded'}:
        return BaristaError('The Groq free limit has been reached, so the barista cannot answer yet.')
    return BaristaError('The barista is away from the bar right now.')


def default_complete(instructions, transcript):
    if not settings.GROQ_API_KEY:
        raise BaristaError('The barista is away from the bar right now.')
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            timeout=20,
        )
        response = client.chat.completions.create(
            model=settings.BARISTA_MODEL,
            messages=[{'role': 'system', 'content': instructions}, *transcript],
            response_format={
                'type': 'json_schema',
                'json_schema': {
                    'name': 'barista_reply',
                    'strict': True,
                    'schema': REPLY_SCHEMA,
                },
            },
        )
        parsed = json.loads(response.choices[0].message.content or '')
    except BaristaError:
        raise
    except Exception as exc:
        raise guest_error(exc) from exc
    if not isinstance(parsed, dict):
        raise BaristaError('The barista is away from the bar right now.')
    return parsed
