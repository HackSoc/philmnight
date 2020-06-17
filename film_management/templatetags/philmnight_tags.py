"""Custom template tags for philmnight branding."""
from django import template
from django.utils.safestring import mark_safe

from film_management.views import get_config

register = template.Library()
FILM_CONFIG = get_config()


@register.simple_tag
def philmnight_name():
    """Return the name of the philmnight app."""
    return FILM_CONFIG.name


@register.simple_tag
def philmnight_logo():
    """Return logo of the philmnight app."""
    return mark_safe('<img id="logo" src="' + FILM_CONFIG.logo.url + '">')


@register.simple_tag
def philmnight_favicon():
    """Return logo of the philmnight app in favicon dimensions."""
    return mark_safe('<link rel="icon" type="image/png" href="' + FILM_CONFIG.logo.url + '">')


def philmnight_stylesheet():
    """Return ."""
    return False
