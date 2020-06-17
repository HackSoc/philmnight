"""Core philmnight views."""
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test


def index(request):
    """View for index page."""
    return render(request, 'index.html', {'GOOGLE_OAUTH_KEY': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY})


def logout_view(request):
    """View for logout page."""
    logout(request)
    return render(request, 'index.html', {})


@user_passes_test(lambda u: u.is_superuser)
def config(request):
    """Page to configure Philmnight."""
    return render(request, 'config.html')
