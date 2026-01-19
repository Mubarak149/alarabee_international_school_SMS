# finance/templatetags/payment_filters.py
from django import template

register = template.Library()

@register.filter
def method_color(method):
    colors = {
        'cash': 'success',
        'transfer': 'primary',
        'pos': 'info',
        'online': 'warning',
        'cheque': 'secondary',
        'mobile': 'dark',
    }
    return colors.get(method, 'secondary')

@register.filter
def method_icon(method):
    icons = {
        'cash': 'money-bill-wave',
        'transfer': 'university',
        'pos': 'credit-card',
        'online': 'globe',
        'cheque': 'file-invoice',
        'mobile': 'mobile-alt',
    }
    return icons.get(method, 'money-check')

@register.filter
def filter_status(queryset, status):
    return queryset.filter(status=status)

@register.filter
def sum_amount(queryset):
    return sum(p.amount_paid for p in queryset)

@register.filter
def percentage(value, total):
    if total and total > 0:
        return (value / total) * 100
    return 0

