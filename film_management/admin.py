"""Admin module for films."""
from django.contrib import admin

from .models import Film, FilmConfig, Profile
# Register your models here.

admin.site.register(Film)
admin.site.register(FilmConfig)
admin.site.register(Profile)
