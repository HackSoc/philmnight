from datetime import date

import requests

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError

from .models import Film

TMDB_ENDPOINT = '***REMOVED***'
TMDB_KEY = '***REMOVED***'


def is_filmweek():
    return date.today().isocalendar()[1] % 2 == 0


@login_required
def dashboard(request):
    return render(request, 'film_management/dashboard.html', {'is_filmweek': is_filmweek()})


@login_required
def submit_film(request):
    new_film = request.POST.get('film_name', '')

    # Fetch top result
    film_info = requests.get(TMDB_ENDPOINT + 'search/movie?query=' + new_film + '&api_key=' + TMDB_KEY).json()['results'][0]

    context = {'success': True}

    if new_film:
        try:
            Film.objects.create(name=new_film,
                                poster_path=film_info['poster_path'])
        except IntegrityError:
            context['success'] = False
            

    return JsonResponse(context)


def films(request):
    return render(request, 'film_management/films.html', {'films': Film.objects.all()})
