"""Core philmnight views."""
from django.conf import settings
from django.contrib.auth import login, logout
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect


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


def login_view(request):
    """Login the given user with the provided credentials."""
    if request.method == 'POST':
        username = request.POST.get('username')
        user = User.objects.filter(username=username)
        if user.exists():
            user = user[0]
            password = request.POST.get('password')

            if user.check_password(password):
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return HttpResponseRedirect('/dashboard')
    return render(request, 'login.html')
