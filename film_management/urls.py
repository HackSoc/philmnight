from django.urls import path
from . import views

app_name = 'film_management'

urlpatterns = [
    path('submit_film/', views.submit_film),
    path('submit_votes/', views.submit_votes),
    path('delete_film/<str:film_id>', views.delete_film)
]


