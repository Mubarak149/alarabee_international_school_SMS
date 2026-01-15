# finance/templatetags/finance_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key."""
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Add the argument to the value."""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value