# finance/templatetags/finance_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='filter_sponsorship')
def filter_sponsorship(queryset, sponsorship_type):
    """
    Filter a list of sponsorship objects by type.
    """
    if not queryset:
        return []
    return [item for item in queryset if item.sponsorship_type == sponsorship_type]

@register.filter
def sponsorship_type_label(sponsorship_type):
    """
    Convert sponsorship_type code to human-readable label.
    """
    labels = {
        'none': 'No Scholarship',
        'full': 'Full Scholarship',
        'partial': 'Partial Scholarship',
        'other': 'Other Scholarship'
    }
    return labels.get(sponsorship_type, sponsorship_type.title())

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary in template"""
    if not dictionary:
        return ""
    return dictionary.get(key, key)

@register.filter
def dict_get(dictionary, key):
    """Alternative name for get_item filter"""
    if not dictionary:
        return ""
    return dictionary.get(key, key)


@register.filter
def subtract(value, arg):
    """Subtract arg from value."""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError):
        try:
            return float(value) - float(arg)
        except (ValueError, TypeError):
            return value
        

@register.filter
def sum_amount(payments):
    """Sum all payment amounts"""
    return sum(payment.amount_paid for payment in payments)

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value