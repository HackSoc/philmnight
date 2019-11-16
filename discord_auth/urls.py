from django.urls import path
from . import views

app_name = 'discord_auth'

urlpatterns = [
    path('auth/', views.auth),
]

