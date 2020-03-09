from django import template

from film_management.views import get_config

register = template.Library()
config = get_config()


@register.simple_tag
def filmnight_name():
    return config.name

