from datetime import date

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError

from .models import Film


def is_filmweek():
    return date.today().isocalendar()[1] % 2 == 0


@login_required
def dashboard(request):
    return render(request, 'film_management/dashboard.html', {'is_filmweek': is_filmweek()})


@login_required
def submit_film(request):
    new_film = request.POST.get('film_name', '')

    context = {'success': True}

    if new_film:
        try:
            Film.objects.create(name=new_film)
        except IntegrityError:
            context['success'] = False
            

    return JsonResponse(context)
