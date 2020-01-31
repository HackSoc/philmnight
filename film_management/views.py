import datetime
import random
import ast
import requests

from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.utils import IntegrityError

from hacksoc_filmnight.settings import TMDB_ENDPOINT, TMDB_KEY
from .models import Film, FilmConfig

FILM_TIMEOUT = 10


def is_filmweek():
    iso_date = datetime.date.today().isocalendar()
    return iso_date[1] % 2 == 0 and iso_date[2] <= 5


def get_config():
    try:
        return FilmConfig.objects.all()[0]
    except IndexError:
        return FilmConfig.objects.create(last_shortlist=datetime.datetime(1,1,1))


@login_required
def dashboard(request):
    if is_filmweek():
        if datetime.datetime.now().isocalendar()[2] == 5:
            film = Film.objects.order_by('-vote_count')[0]
            
            return HttpResponseRedirect('/films/' + str(film.tmdb_id))

        film_config = get_config()
        
        if (datetime.datetime.now() - film_config.last_shortlist).days > 7:
            available_films = Film.objects.filter(watched=False)
            film_config.shortlist.clear()
            film_config.last_shortlist = datetime.datetime.now()

            top_film = Film.objects.order_by('-vote_count')[0]
            top_film.watched = True

            for film in available_films:
                if not film.watched:
                    film.vote_count = 0 
                    film.save()

            for i in range(film_config.shortlist_length):
                chosen_film = random.choice(available_films)

                film_config.shortlist.add(chosen_film)
                available_films = available_films.exclude(id=chosen_film.id)

            film_config.save()

        current_votes = request.user.profile.current_votes.split(',')
        if current_votes == ['']:
            current_votes = []

        return render(request, 'film_management/dashboard.html', {'is_filmweek': True, 'shortlisted_films': FilmConfig.objects.all()[0].shortlist.all(), 'current_votes': current_votes})

    return render(request, 'film_management/dashboard.html', {'is_filmweek': False})


@login_required
def submit_film(request, tmdb_id):
    try:
        last_user_film = Film.objects.filter(submitting_user=request.user).order_by('-date_submitted')[0]
        last_submit_delta = (datetime.datetime.now()-last_user_film.date_submitted).seconds
        if last_submit_delta < FILM_TIMEOUT:
            messages.add_message(request, messages.ERROR, 'You are doing that too fast. Try again in ' + str(FILM_TIMEOUT-last_submit_delta) + ' seconds')
            return HttpResponseRedirect('/dashboard/')
    except IndexError:
        pass

    try:
        Film.objects.create(tmdb_id=tmdb_id, submitting_user=request.user)
        messages.add_message(request, messages.SUCCESS, 'Successfully added film')
    except IntegrityError:
        messages.add_message(request, messages.ERROR, 'Film already exists in database.')

    return HttpResponseRedirect('/dashboard/')

@login_required
def film(request, tmdb_id):
    film = Film.objects.get(tmdb_id=tmdb_id)
    return render(request, 'film_management/film.html', { 'film': film })

@user_passes_test(lambda u: u.is_superuser)
def delete_film(request, tmdb_id):
    film = Film.objects.get(tmdb_id=tmdb_id)
    film.delete()
    return HttpResponseRedirect('/films/')

@login_required
def submit_votes(request):
    user = request.user

    config = get_config()

    # Clear votes from previous weeks
    if user.profile.last_vote.isocalendar()[1] < datetime.datetime.now().isocalendar()[1]:
        user.profile.current_votes = ''
        user.save()

    success = True
    try:
        submitted_films = ast.literal_eval(request.body.decode('utf-8'))
    except ValueError:
        success = False

    if success:
        old_votes = user.profile.current_votes.split(',')

        for film in submitted_films:
            if film not in old_votes and film != '':
                film = Film.objects.get(film_id=film)
                if film not in config.shortlist.all():
                    return JsonResponse({'success': False})
                film.vote_count += 1
                film.save()

        for film in old_votes:
            if film not in submitted_films and film != '':
                film = Film.objects.get(film_id=film)
                if film not in config.shortlist.all():
                    return JsonResponse({'success': False})
                film.vote_count -= 1
                film.save()

        user.profile.last_vote = datetime.datetime.now()
        user.profile.current_votes = ','.join(submitted_films)
        user.save()

    return JsonResponse({'success': success})


@login_required
def films(request):
    return render(request, 'film_management/films.html', {'films': Film.objects.all()})


@login_required
def search_films(request):
    current_string = request.body.decode('utf-8')

    if current_string != '':
        request_path = (TMDB_ENDPOINT + 'search/movie?query=' + current_string +
            '&api_key=' + TMDB_KEY)
        response = requests.get(request_path).json()['results']
        films = []

        while len(films) < 5:
            try:
                film = response[len(films)]
            except IndexError:
                break
            #if not Film.objects.filter(tmdb_id=film['id']).exists():
            films.append([film['title'] + ' (' + film['release_date'].split('-')[0] + ')', film['id']])
            #else:
            #    response.remove(film)

        return JsonResponse({'films': films})
    return JsonResponse({'success': False})
