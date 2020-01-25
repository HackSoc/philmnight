import datetime
import random
import ast

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

from django.db.utils import IntegrityError

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


def fix_caps(string):
    # Convert to title case list
    string = string.title().split(' ')
    exceptions = ['or', 'a', 'an', 'the', 'and', 'but', 'for', 'nor', 'at', 'from']

    # Decapitalise exceptions
    for i in range(1, len(string)):
        if string[i] in exceptions:
            string[i] = string[i].lower() 

    string = ' '.join(string)
    return string


@login_required
def dashboard(request):
    if is_filmweek():
        if datetime.datetime.now().isocalendar()[2] == 5:
            top_film = Film.objects.order_by('-vote_count')[0]
            return render(request, 'film_management/dashboard.html', {'is_filmweek': True, 'top_film': top_film})

        film_config = get_config()
        
        if (datetime.datetime.now() - film_config.last_shortlist).days > 7:
            available_films = Film.objects.filter(watched=False)
            film_config.shortlist.clear()
            film_config.last_shortlist = datetime.datetime.now()

            for film in available_films:
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
def submit_film(request):
    new_film = request.POST.get('film_name', '')

    try:
        last_user_film = Film.objects.filter(submitting_user=request.user).order_by('-date_submitted')[0]
        last_submit_delta = (datetime.datetime.now()-last_user_film.date_submitted).seconds
        if last_submit_delta < FILM_TIMEOUT:
            return JsonResponse({'success': False, 'error': 2, 'time': FILM_TIMEOUT-last_submit_delta})
    except IndexError:
        pass

    context = {'success': True}

    if new_film:
        try:
            Film.objects.create(name=fix_caps(new_film), submitting_user=request.user)
        except IntegrityError:
            context['success'] = False
            context['error'] = 1
            

    return JsonResponse(context)


@user_passes_test(lambda u: u.is_superuser)
def delete_film(request, film_id):
    film = Film.objects.get(film_id=film_id)
    film.delete()
    return HttpResponseRedirect('/dashboard/films/')


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

