"""Admin module for films."""
from django.contrib import admin

from .models import Film, FilmConfig
# Register your models here.

admin.site.register(Film)
admin.site.register(FilmConfig)
