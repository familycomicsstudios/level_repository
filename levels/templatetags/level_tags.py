from django import template
from levels.models import Level

register = template.Library()

@register.simple_tag
def get_level_by_id(level_id):
    return Level.objects.get(id=level_id)
