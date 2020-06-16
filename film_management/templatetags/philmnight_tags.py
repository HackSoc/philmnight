"""Custom template tags for philmnight branding."""
from django import template
from django.utils.safestring import mark_safe

from film_management.views import get_config

register = template.Library()


@register.simple_tag
def filmnight_name():
    """Return the name of the philmnight app."""
    config = get_config()
    return config.name


@register.simple_tag
def filmnight_logo():
    """Return branding of the philmnight app."""
    config = get_config()
    return mark_safe('<img id="logo" src="' + config.logo.url + '">')


@register.simple_tag
def filmnight_favicon():
    """Return branding of the philmnight app in favicon dimensions."""
    config = get_config()
    return mark_safe('<link rel="icon" type="image/png" href="' + config.logo.url + '">')
