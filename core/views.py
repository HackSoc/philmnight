"""Core philmnight views."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from core.abstract_views import SuperuserView
from film_management.forms import FilmConfigForm
from film_management.models import FilmConfig


def index(request: HttpRequest) -> HttpResponse:
    """View for index page."""
    context = {
        'GOOGLE_OAUTH_KEY': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
    }
    return render(request, 'index.html', context)


def logout_view(request: HttpRequest) -> HttpResponse:
    """View for logout page."""
    logout(request)
    return render(request, 'index.html', {})


class ConfigView(SuperuserView):
    template_name = 'config.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            'config_form': FilmConfigForm(instance=FilmConfig.objects.get(pk=1))
        }
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest) -> HttpResponse:
        config_form = FilmConfigForm(request.POST, request.FILES)

        if config_form.is_valid():
            messages.add_message(request, messages.SUCCESS, 'Config updated successfully')
            config_form.save()
            return HttpResponseRedirect(reverse('config'))

        return render(request, self.template_name, {'config_form': config_form})


def login_view(request: HttpRequest) -> HttpResponse:
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
