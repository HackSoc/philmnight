from django.urls import path
from . import views

app_name = 'film_management'

urlpatterns = [
    path('submit_film/<int:tmdb_id>', views.submit_film),
    path('submit_votes/', views.submit_votes),
    path('search_films/', views.search_films),
    path('delete_film/<str:tmdb_id>', views.delete_film),
]


