from django import template

register = template.Library()

@register.filter
def get_current_term(terms):
    return terms.filter(is_current=True).first()
