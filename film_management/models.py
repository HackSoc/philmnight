"""Models relating to film management."""

import datetime
import requests

from django.db import models
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from hacksoc_filmnight.settings import TMDB_ENDPOINT, TMDB_KEY


# pylint: disable=too-many-instance-attributes
class Film(models.Model):
    """Stores information regarding an individual film."""

    tmdb_id = models.IntegerField(default=1, null=True, unique=True)

    name = models.CharField(max_length=70, blank=False)
    description = models.TextField(default='', null=True)
    tagline = models.TextField(default='', null=True)
    watched = models.BooleanField(default=False)

    @property
    def votes(self):
        users = User.objects.all()
        votes = 0
        for user in users:
            films = user.profile.current_votes.split(',')
            if str(self.tmdb_id) in films:
                votes += 1
        return votes

    poster_path = models.CharField(default='', max_length=100, null=True)
    backdrop_path = models.CharField(default='', max_length=100, null=True)

    submitting_user = models.ForeignKey(User, blank=True, null=True,
                                        on_delete=models.CASCADE)

    date_submitted = models.DateTimeField(auto_now_add=True, blank=True)
    release_date = models.DateTimeField(blank=True, auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.name

    # pylint: disable=arguments-differ
    def save(self, *args, **kwargs):
        """
        Override save argument of film model.

        Override save argument of film model to populate film_id
        field and search TMDB for film data and appropriate poster.
        """

        request_path = (TMDB_ENDPOINT + 'movie/' + str(self.tmdb_id) + '?api_key=' + TMDB_KEY)
        film_info = requests.get(request_path).json()

        self.name = film_info.get('title', 'Unknown')
        self.description = film_info.get('overview', 'No description available')
        self.poster_path = film_info.get('poster_path', '')
        self.backdrop_path = film_info.get('backdrop_path', '')
        self.tagline = film_info.get('tagline', '')
        self.tmdb_id = film_info['id']

        release_date = datetime.datetime.strptime(film_info['release_date'], '%Y-%m-%d')
        if datetime.datetime.now() < release_date:
            raise IntegrityError(self.name + ' has not been released yet. Released: ' + str(release_date) + '\nUnprocessed: ' + film_info['release_date'])
        self.release_date = release_date

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

    def save(self, *args, **kwargs):
        current_votes = self.current_votes.split(',')
        for item in current_votes:
            if item == '':
                current_votes.remove(item)

        self.current_votes = ','.join(current_votes)
        super(Profile, self).save(*args, **kwargs)


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
