"""URL paths for film_management views."""
from django.urls import include, path

from . import views

app_name = 'film_management'

film_urls = [
    path('', views.films),
    path('<str:tmdb_id>/', views.FilmView.as_view(), name='film'),
]

voting_urls = [
    path('submit/', views.views.submit_votes, name='submit'),
]

urlpatterns = [
    path('<str:filmnight_id>/control_panel/', views.control_panel, name='control_panel'),
    path('<str:filmnight_id>/dashboard/', views.dashboard, name='dashboard'),
    path('<str:filmnight_id>/films/', include(film_urls, 'films')),
    path('<str:filmnight_id>/voting/', include(voting_urls, 'voting'))
]
