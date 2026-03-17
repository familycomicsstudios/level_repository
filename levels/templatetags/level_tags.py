from django import template
from django.utils.safestring import mark_safe
from levels.models import Level, DIFFICULTY_SYSTEM_CHOICES
from levels.difficulty import format_difficulty, SYSTEM_LABELS

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
