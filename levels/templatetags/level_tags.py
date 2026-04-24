from django import template
from django.utils.safestring import mark_safe
from levels.models import Level, DIFFICULTY_SYSTEM_CHOICES
from levels.difficulty import format_difficulty, SYSTEM_LABELS
import math

register = template.Library()

@register.simple_tag
def get_level_by_id(level_id):
    return Level.objects.get(id=level_id)


@register.filter
def display_difficulty(value, system):
    if value is None:
        return ""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return value
    return mark_safe(format_difficulty(numeric_value, system))


@register.simple_tag
def difficulty_system_choices():
    return DIFFICULTY_SYSTEM_CHOICES


@register.filter
def difficulty_system_label(system_key):
    return SYSTEM_LABELS.get(system_key, system_key)


@register.filter
def as_stars(value, max_stars=5):
    if value is None:
        return ""
    try:
        numeric_value = float(value)
        numeric_max = int(max_stars)
    except (TypeError, ValueError):
        return ""

    filled = int(math.floor(numeric_value + 0.5))
    filled = max(0, min(filled, numeric_max))
    empty = numeric_max - filled

    return mark_safe("&#9733;" * filled + "&#9734;" * empty)


@register.filter
def display_name_or_username(user):
    if not user:
        return ""

    try:
        display_name = (user.profile.display_name or "").strip()
        if display_name:
            return display_name
    except Exception:
        pass

    return user.username
