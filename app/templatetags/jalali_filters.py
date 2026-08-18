from django import template
from ..jalali_utils import to_jalali_string

register = template.Library()


@register.filter(name='jalali')
def jalali(value):
    return to_jalali_string(value)
