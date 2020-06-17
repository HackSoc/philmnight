"""Views for film management."""
import random
import ast
import datetime
import requests

from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.utils import IntegrityError, OperationalError
from django.utils import timezone

from philmnight.settings import TMDB_ENDPOINT, TMDB_KEY
from .models import Film, FilmConfig

FILM_TIMEOUT = 10


def get_phase():
    """Return the current phase of voting."""
    iso_date = timezone.now().isocalendar()
    if iso_date[1] % 2 == 1 and iso_date[2] == 5:
        if timezone.now().hour >= 7:
            return 'filmnight'
        return 'voting'
    return 'submissions'


def get_config():
    """Return the film config. If it doesn't exist, create it."""
    try:
        return FilmConfig.objects.all()[0]
    except IndexError:
        return FilmConfig.objects.create(last_shortlist=datetime.datetime(1, 1, 1))
    except OperationalError:
        return False


def reset_votes():
    """Reset all votes for every film to 0."""
    for user in User.objects.all():
        user.profile.current_votes = ''
        user.save()


@login_required
def dashboard(request):
    """View for dashboard - split in 2 at later date."""
    film_config = get_config()
    phase = get_phase()

    if phase == 'filmnight':
        top_film = max([[film, film.votes] for film in Film.objects.all()], key=lambda x: x[1])[0]

        return HttpResponseRedirect('/films/' + str(top_film.tmdb_id))

    if phase == 'voting':
        if (datetime.datetime.now() - film_config.last_shortlist).days > 7:
            available_films = Film.objects.filter(watched=False)
            film_config.shortlist.clear()
            film_config.last_shortlist = datetime.datetime.now()

            top_film = max([[film, film.votes] for film in Film.objects.all()],
                           key=lambda x: x[1])[0]
            top_film.watched = True
            top_film.save()

            reset_votes()

            for _ in range(film_config.shortlist_length):
                try:
                    chosen_film = random.choice(available_films)
                except IndexError:
                    break

                film_config.shortlist.add(chosen_film)
                available_films = available_films.exclude(id=chosen_film.id)

            film_config.save()

        current_votes = [str(i) for i in request.user.profile.current_votes.split(',')]
        if current_votes == ['']:
            current_votes = []

        context = {
            'shortlisted_films': FilmConfig.objects.all()[0].shortlist.all(),
            'current_votes': current_votes
        }

        return render(request, 'film_management/vote.html', context)
    return render(request, 'film_management/submit.html')


@login_required
def submit_film(request, tmdb_id):
    """Submit the provided film ID to the filmnight database."""
    try:
        last_submission = Film.objects.filter(submitting_user=request.user).order_by('-date_submitted')[0]
        last_submit_delta = (datetime.datetime.now()-last_submission.date_submitted).seconds
        if last_submit_delta < FILM_TIMEOUT:
            messages.add_message(
                request,
                messages.ERROR,
                'You are doing that too fast. Try again in ' + str(FILM_TIMEOUT-last_submit_delta) + ' seconds'
            )
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
    """Render information about a chosen film."""
    chosen_film = Film.objects.get(tmdb_id=tmdb_id)
    return render(request, 'film_management/film.html', {'film': chosen_film})


@user_passes_test(lambda u: u.is_superuser)
def delete_film(request, tmdb_id):
    film = Film.objects.get(tmdb_id=tmdb_id)
    film.delete()
    return HttpResponseRedirect('/films/')


@login_required
def submit_votes(request):
    if get_phase() == 'voting':
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
                    film = Film.objects.get(tmdb_id=film)
                    if film not in config.shortlist.all():
                        return JsonResponse({'success': False})

            for film in old_votes:
                if film not in submitted_films and film != '':
                    film = Film.objects.get(tmdb_id=film)
                    if film not in config.shortlist.all():
                        return JsonResponse({'success': False})

            user.profile.last_vote = datetime.datetime.now()
            user.profile.current_votes = ','.join(submitted_films)
            user.save()

    return JsonResponse({'success': success})


@login_required
def films(request):
    return render(request, 'film_management/films.html', {'films': Film.objects.order_by('name')})


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
            if not Film.objects.filter(tmdb_id=film['id']).exists():
                if film['release_date'] != '':
                    if datetime.datetime.now() < datetime.datetime.strptime(film['release_date'], '%Y-%m-%d'):
                        films.append([film['title'] + ' (' + film['release_date'].split('-')[0] + ')', film['id'], True])
                    else:
                        films.append([film['title'] + ' (' + film['release_date'].split('-')[0] + ')', film['id'], False])
                else:
                    films.append([film['title'] + ' (' + film['release_date'].split('-')[0] + ')', film['id'], False])
            else:
                films.append([film['title'] + ' (' + film['release_date'].split('-')[0] + ')', film['id'], True])

        return JsonResponse({'films': films})
    return JsonResponse({'success': False})


@user_passes_test(lambda u: u.is_superuser)
def control_panel(request):
    genres = []
    for film in Film.objects.all():
        for genre in film.genres:
            if genre not in genres and genre.strip() != '':
                genres.append(genre)
    context = {'genres': genres}
    return render(request, 'film_management/control_panel.html', context)
