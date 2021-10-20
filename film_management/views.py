"""Views for film management."""
import ast
import datetime
from enum import Enum
import random
from typing import Optional, cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.utils import IntegrityError, OperationalError
from django.http import HttpResponseRedirect, JsonResponse
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils import timezone
import requests

from core.models import User
from philmnight.settings import TMDB_ENDPOINT, TMDB_KEY

from .models import Film, FilmConfig

FILM_TIMEOUT = 10


class FilmnightPhase(Enum):
    FILMNIGHT = 0
    VOTING = 1
    SUBMISSIONS = 2


def get_phase() -> FilmnightPhase:
    """Return the current phase of voting."""
    current_time = timezone.now()

    config = get_config()
    assert config is not None

    if current_time > config.next_filmnight:
        if current_time > config.next_filmnight + datetime.timedelta(days=1):
            config.next_filmnight += config.filmnight_timedelta
            config.save()
            return get_phase()

        return FilmnightPhase.FILMNIGHT
    
    if current_time > config.next_filmnight - config.voting_period_length:
        return FilmnightPhase.VOTING

    return FilmnightPhase.SUBMISSIONS


def get_config() -> Optional[FilmConfig]:
    """Return the film config. If it doesn't exist, create it."""
    try:
        return FilmConfig.objects.all()[0]
    except IndexError:
        return FilmConfig.objects.create(last_shortlist=datetime.datetime(1, 1, 1))
    except OperationalError as e:
        print('Error supressed to allow for migrations:\nError:'+str(e))
        return


def reset_votes() -> None:
    """Reset all votes for every film to 0."""
    for user in User.objects.all():
        user.current_votes = ''
        user.save()


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """View for dashboard - split in 2 at later date."""
    film_config = get_config()
    user: User = cast(User, request.user)
    assert film_config is not None
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
                    chosen_film = random.choice(list(available_films))
                except IndexError:
                    break

                film_config.shortlist.add(chosen_film)
                available_films = available_films.exclude(id=chosen_film.id)

            film_config.save()

        current_votes = [str(i) for i in user.current_votes.split(',')]  # FIXME: Ditch Profile class to fix
        if current_votes == ['']:
            current_votes = []

        context = {
            'shortlisted_films': FilmConfig.objects.all()[0].shortlist.all(),
            'current_votes': current_votes
        }

        return render(request, 'film_management/vote.html', context)
    return render(request, 'film_management/submit.html')


@login_required
def submit_film(request: HttpRequest, tmdb_id: str) -> HttpResponse:
    """Submit the provided film ID to the filmnight database."""
    try:
        last_submission = Film.objects.filter(
            submitting_user=request.user
        ).order_by('-date_submitted')[0]
        last_submit_delta = (datetime.datetime.now()-last_submission.date_submitted).seconds
        if last_submit_delta < FILM_TIMEOUT:
            messages.add_message(
                request,
                messages.ERROR,
                f'You\'re doing that too fast. Try again in {FILM_TIMEOUT-last_submit_delta}'
                ' seconds'
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
def film(request: HttpRequest, tmdb_id: str):
    """Render information about a chosen film."""
    chosen_film = Film.objects.get(tmdb_id=tmdb_id)
    return render(request, 'film_management/film.html', {'film': chosen_film})


@user_passes_test(lambda u: u.is_superuser)
def delete_film(request: HttpRequest, tmdb_id: str) -> HttpResponse:
    """Delete a given film. Superusers only."""
    chosen_film = Film.objects.get(tmdb_id=tmdb_id)
    chosen_film.delete()
    return HttpResponseRedirect('/films/')


@login_required
def submit_votes(request: HttpRequest) -> HttpResponse:
    """Submit a vote on a film."""
    if get_phase() != 'voting':
        return JsonResponse({'success': False})

    user: User = cast(User, request.user)

    config = get_config()
    assert config is not None

    # Clear votes from previous weeks
    if user.last_vote.isocalendar()[1] < datetime.datetime.now().isocalendar()[1]:
        user.current_votes = ''
        user.save()

    try:
        submitted_films: list = ast.literal_eval(request.body.decode('utf-8'))
    except ValueError:
        return JsonResponse({'success': False})

    old_votes = user.current_votes.split(',')

    for current_film in submitted_films:
        if current_film not in old_votes and current_film != '':
            current_film = Film.objects.get(tmdb_id=current_film)
            if current_film not in config.shortlist.all():
                return JsonResponse({'success': False})

    for current_film in old_votes:
        if current_film not in submitted_films and current_film != '':
            current_film = Film.objects.get(tmdb_id=current_film)
            if current_film not in config.shortlist.all():
                return JsonResponse({'success': False})

    user.last_vote = datetime.datetime.now()
    user.current_votes = ','.join(submitted_films)
    user.save()

    return JsonResponse({'success': True})


@login_required
def films(request: HttpRequest) -> HttpResponse:
    """Return a view of all submitted films."""
    return render(request, 'film_management/films.html', {'films': Film.objects.order_by('name')})


@login_required
def search_films(request: HttpRequest) -> HttpResponse:
    """Search the TMDB database for a film."""
    current_string = request.body.decode('utf-8')

    if current_string != '':
        request_path = (TMDB_ENDPOINT + 'search/movie?query=' + current_string +
                        '&api_key=' + TMDB_KEY)
        response = requests.get(request_path).json()['results']
        potential_films = []

        while len(potential_films) < 5:
            try:
                current_film = response[len(potential_films)]
            except IndexError:
                break
            if not Film.objects.filter(tmdb_id=current_film['id']).exists():
                if current_film['release_date'] != '':
                    time = datetime.datetime.strptime(current_film['release_date'], '%Y-%m-%d')
                    if datetime.datetime.now() < time:
                        potential_films.append(
                            [current_film['title'] + ' (' +
                             current_film['release_date'].split('-')[0] + ')', current_film['id'],
                             True])
                    else:
                        potential_films.append(
                            [current_film['title'] + ' (' +
                             current_film['release_date'].split('-')[0] + ')', current_film['id'],
                             False])
                else:
                    potential_films.append(
                        [current_film['title'] + ' (' +
                         current_film['release_date'].split('-')[0] + ')', current_film['id'],
                         False])
            else:
                potential_films.append([
                    current_film['title'] + ' (' +
                    current_film['release_date'].split('-')[0] + ')', current_film['id'],
                    True])

        return JsonResponse({'films': potential_films})
    return JsonResponse({'success': False})


@user_passes_test(lambda u: u.is_superuser)
def control_panel(request: HttpRequest):
    """Unimplemented filmnight control panel."""
    genres = []
    for current_film in Film.objects.all():
        for genre in current_film.genres:
            if genre not in genres and genre.strip() != '':
                genres.append(genre)
    context = {'genres': genres}
    return render(request, 'film_management/control_panel.html', context)
