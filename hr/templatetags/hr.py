from django import template

register = template.Library()


@register.filter
def cu(value):
    """currency"""
    return '${0:.2f}'.format(value)
