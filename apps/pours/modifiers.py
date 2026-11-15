from decimal import Decimal


GROUP_ORDER = ('milk', 'sweetness', 'temperature')

DRINK_CATEGORIES = frozenset({
    'daily-classics',
    'signature-pour',
    'custom-pour',
    'matcha-edit',
})

MODIFIERS = (
    {'slug': 'whole-milk', 'label': 'Whole milk', 'group': 'milk', 'price': Decimal('0.00')},
    {'slug': 'oat-milk', 'label': 'Oat milk', 'group': 'milk', 'price': Decimal('20.00')},
    {'slug': 'almond-milk', 'label': 'Almond milk', 'group': 'milk', 'price': Decimal('20.00')},
    {'slug': 'less-sweet', 'label': 'Less sweet', 'group': 'sweetness', 'price': Decimal('0.00')},
    {'slug': 'unsweetened', 'label': 'Unsweetened', 'group': 'sweetness', 'price': Decimal('0.00')},
    {'slug': 'hot', 'label': 'Hot', 'group': 'temperature', 'price': Decimal('0.00')},
    {'slug': 'iced', 'label': 'Iced', 'group': 'temperature', 'price': Decimal('0.00')},
)


class ModifierError(Exception):
    pass


def for_category(category_slug):
    if category_slug not in DRINK_CATEGORIES:
        return []
    return list(MODIFIERS)


def _choose(category_slug, requested, strict):
    allowed = {modifier['slug']: modifier for modifier in for_category(category_slug)}
    chosen = {}
    for raw in requested:
        slug = str(raw).strip()
        modifier = allowed.get(slug)
        if modifier is None or modifier['group'] in chosen:
            if strict:
                raise ModifierError
            continue
        chosen[modifier['group']] = slug
    return [chosen[group] for group in GROUP_ORDER if group in chosen]


def clean_modifiers(category_slug, requested):
    if not isinstance(requested, list):
        raise ModifierError
    return _choose(category_slug, requested, strict=True)


def keep_known(category_slug, requested):
    if not isinstance(requested, list):
        return []
    return _choose(category_slug, requested, strict=False)


def modifier_total(slugs):
    prices = {modifier['slug']: modifier['price'] for modifier in MODIFIERS}
    return sum((prices[slug] for slug in slugs), Decimal('0.00'))


def money_label(amount):
    if amount == amount.to_integral():
        shown = f'{int(amount)}'
    else:
        shown = f'{amount:.2f}'
    return f'₱{shown}'
