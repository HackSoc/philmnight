"""Models relating to film management."""

import datetime
import requests

from django.db import models
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from hacksoc_filmnight.settings import TMDB_ENDPOINT, TMDB_KEY


class Film(models.Model):
    """Stores information regarding an individual film."""

    name = models.CharField(max_length=70, blank=False)
    description = models.TextField(default='', null=True)
    tagline = models.TextField(default='', null=True)

    film_id = models.CharField(max_length=70, unique=True, blank=True)
    vote_count = models.IntegerField(default=0)
    in_current_vote = models.BooleanField(default=False)
    watched = models.BooleanField(default=False)

    poster_path = models.CharField(default='', max_length=100, null=True)
    backdrop_path = models.CharField(default='', max_length=100, null=True)

    submitting_user = models.ForeignKey(User, blank=True, null=True,
                                        on_delete=models.CASCADE)

    date_submitted = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.name

    # pylint: disable=arguments-differ
    def save(self, *args, **kwargs):
        """
        Override save argument of film model.

        Override save argument of film model to populate film_id
        field and search TMDB for film data and appropriate poster.
        """
        # pylint: disable=no-member
        self.film_id = self.name.replace(' ', '').lower()
        try:
            request_path = (TMDB_ENDPOINT + 'search/movie?query=' + self.name +
                            '&api_key=' + TMDB_KEY)
            film_id = requests.get(request_path).json()['results'][0]['id']
            request_path = (TMDB_ENDPOINT + 'movie/' + str(film_id) + '?api_key=' + TMDB_KEY)
            film_info = requests.get(request_path).json()

            self.description = film_info['summary']
            self.poster_path = film_info['poster_path']
            self.backdrop_path = film_info['backdrop_path']
            self.tagline = film_info['tagline']
        except IndexError:
            self.poster_path = ''

        super(Film, self).save(*args, **kwargs)


class FilmConfig(models.Model):
    """Dynamic settings regarding how the shortlist works."""

    shortlist = models.ManyToManyField(Film)
    shortlist_length = models.IntegerField(default=8)
    last_shortlist = models.DateTimeField()

    # pylint: disable=unused-argument
    def clean(self, *args, **kwargs):
        """Override clean function so shortlist can't be overpopulated."""
        if self.shortlist.count() > self.shortlist_length:
            raise ValueError('Shortlist length exceeds max')

    # pylint: disable=unused-argument
    def save(self, *args, **kwargs):
        try:
            self.id = 1
            super(FilmConfig, self).save(*args, **kwargs)
        except IntegrityError:
            raise IntegrityError('Only one instance of FilmConfig may exist in the database')


class Profile(models.Model):
    """Model to extend the user model."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_votes = models.TextField(blank=True, default='')
    last_vote = models.DateTimeField(default=datetime.datetime.min)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except AttributeError:
        Profile.objects.create(user=instance)
