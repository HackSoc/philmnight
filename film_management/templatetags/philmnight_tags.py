"""Custom template tags for philmnight branding."""
from django import template
from django.utils.safestring import SafeString, mark_safe

from film_management.views import get_config

register = template.Library()
FILM_CONFIG = get_config()


@register.simple_tag
def philmnight_name() -> str:
    """Return the name of the philmnight app."""
    assert FILM_CONFIG is not None
    return FILM_CONFIG.name


@register.simple_tag
def philmnight_logo() -> SafeString:
    """Return logo of the philmnight app."""
    assert FILM_CONFIG is not None
    return mark_safe('<img id="logo" src="' + FILM_CONFIG.logo.url + '">')


@register.simple_tag
def philmnight_favicon() -> SafeString:
    """Return logo of the philmnight app in favicon dimensions."""
    assert FILM_CONFIG is not None
    return mark_safe('<link rel="icon" type="image/png" href="' + FILM_CONFIG.logo.url + '">')


def philmnight_stylesheet():
    """Return ."""
    return False
