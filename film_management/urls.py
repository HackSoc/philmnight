from django.urls import path
from . import views

app_name = 'film_management'

urlpatterns = [
    path('submit_film/', views.submit_film),
]


