import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.utils import IntegrityError

from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from core.abstract_views import ProtectedView
from film_management.models import Film

FILM_TIMEOUT = 10  # PERF: Switch to django-ratelimit


class FilmView(ProtectedView):

    # TODO: Decide if filmnight IDs are strings or ints
    def post(self, request: HttpRequest, tmdb_id: str) -> HttpResponse:
        """Submit a film for the specified filmnight."""
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

        try:  # TODO: Don't ask for forgiveness
            Film.objects.create(tmdb_id=tmdb_id, submitting_user=request.user)
            messages.add_message(request, messages.SUCCESS, 'Successfully added film')
        except IntegrityError:
            messages.add_message(request, messages.ERROR, 'Film already exists in database.')

        return HttpResponseRedirect('/dashboard/')

    def get(self, request: HttpRequest, tmdb_id: str) -> HttpResponse:
        """Render information about a chosen film."""
        chosen_film = Film.objects.get(tmdb_id=tmdb_id)
        return render(request, 'film_management/film.html', {'film': chosen_film})

    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def delete(self, request: HttpRequest, tmdb_id: str) -> HttpResponse:
        """Delete a given film. Superusers only."""
        chosen_film = Film.objects.get(tmdb_id=tmdb_id)
        chosen_film.delete()
        return HttpResponseRedirect('/films/')


@login_required
def films(request: HttpRequest) -> HttpResponse:
    """Return a view of all submitted films."""
    return render(request, 'film_management/films.html', {'films': Film.objects.order_by('name')})
