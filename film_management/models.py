import requests

from django.db import models
from django.db.utils import IntegrityError

TMDB_ENDPOINT = '***REMOVED***'
TMDB_KEY = '***REMOVED***'


class Film(models.Model):
    name = models.CharField(max_length=70, blank=False)
    film_id = models.CharField(max_length=70, unique=True, blank=True)
    vote_count = models.IntegerField(default=0)
    in_current_vote = models.BooleanField(default=False)

    poster_path = models.CharField(default='', max_length=100)

    date_submitted = models.DateTimeField(auto_now_add=True, blank=True)

    def save(self, *args, **kwargs):
        self.film_id = self.name.replace(' ', '').lower()
        try:
            film_info = requests.get(TMDB_ENDPOINT + 'search/movie?query=' + self.name + '&api_key=' + TMDB_KEY).json()['results'][0]
            self.poster_path = film_info['poster_path']
        except IndexError:
            self.poster_path = ''

        super(Film, self).save(*args, **kwargs)


class FilmConfig(models.Model):
    shortlist_length = models.IntegerField(default=8)

    def save(self, *args, **kwargs):
        try:
            self.pk = 1
            super(Film, self).save(*args, **kwargs)
        except IntegrityError:
            raise IntegrityError('Only one instance of FilmConfig may exist in the database')

