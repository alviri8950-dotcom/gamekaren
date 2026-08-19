from django import template
from ..jalali_utils import to_jalali_string

register = template.Library()


@register.filter(name='jalali')
def jalali(value):
    return to_jalali_string(value)


@register.filter(name='commas')
def commas(value):
    """عدد رو با جداکننده‌ی هزارگان نمایش می‌ده، مثلاً 1234567 -> 1,234,567 (منفی‌ها هم درست کار می‌کنن)."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return value
    return f"{n:,}"
