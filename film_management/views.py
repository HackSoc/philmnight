from datetime import date

from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def is_filmweek():
    return date.today().isocalendar()[1] % 2 == 0


@login_required
def dashboard(request):
    return render(request, 'film_management/dashboard.html', {'is_filmweek': is_filmweek()})
