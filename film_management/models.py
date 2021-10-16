"""Models relating to film management."""

import datetime
from typing import Any
import requests
from PIL import Image

from django.db import models
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from philmnight.settings import TMDB_ENDPOINT, TMDB_KEY


# pylint: disable=too-many-instance-attributes
class Film(models.Model):
    """Stores information regarding an individual film."""

    tmdb_id = models.IntegerField(default=1, null=True, unique=True)

    score = models.DecimalField(default=-1, null=True, decimal_places=1, max_digits=3)
    name = models.CharField(max_length=70, blank=False)
    description = models.TextField(default='', null=True)
    tagline = models.TextField(default='', null=True)
    watched = models.BooleanField(default=False)
    _genres = models.TextField(default='', null=True)

    poster_path = models.CharField(default='', max_length=100, null=True)
    backdrop_path = models.CharField(default='', max_length=100, null=True)

    submitting_user = models.ForeignKey(User, blank=True, null=True,
                                        on_delete=models.CASCADE)

    date_submitted = models.DateTimeField(auto_now_add=True, blank=True)
    release_date = models.DateTimeField(blank=True, auto_now_add=True)

    @property
    def genres(self) -> list[str]:
        """Return film genres as a list."""
        return self._genres.split(',')

    @property
    def votes(self) -> int:
        """Return number of voters."""
        users = User.objects.all()
        vote_count = 0
        for user in users:
            films = user.profile.current_votes.split(',')
            if str(self.tmdb_id) in films:
                vote_count += 1
        return vote_count

    @property
    def voters(self) -> list[User]:
        """Return list containing usernames of voters."""
        users = User.objects.all()
        voters_list = []
        for user in users:
            films = user.profile.current_votes.split(',')
            if str(self.tmdb_id) in films:
                voters_list.append(user.first_name + user.last_name)
        return voters_list

    def __str__(self) -> str:
        """Return a string representation of the model."""
        return self.name

    # pylint: disable=signature-differs
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save argument of film model.

        Override save argument of film model to populate film_id
        field and search TMDB for film data and appropriate poster.
        """
        request_path = (TMDB_ENDPOINT + 'movie/' + str(self.tmdb_id) + '?api_key=' + TMDB_KEY)
        film_info = requests.get(request_path).json()

        self.score = film_info.get('vote_average', -1)
        self.name = film_info.get('title', 'Unknown')
        self.description = film_info.get('overview', 'No description available')
        self.poster_path = film_info.get('poster_path', '')
        self.backdrop_path = film_info.get('backdrop_path', '')
        self.tagline = film_info.get('tagline', '')
        self._genres = ','.join([genre['name'] for genre in film_info['genres']])

        release_date = datetime.datetime.strptime(film_info['release_date'], '%Y-%m-%d')
        if datetime.datetime.now() < release_date:
            raise IntegrityError(self.name + ' has not been released yet. Released: ' +
                                 str(release_date) + '\nUnprocessed: ' +
                                 film_info['release_date'])
        self.release_date = release_date

        super(Film, self).save(*args, **kwargs)


class FilmConfig(models.Model):
    """Dynamic settings regarding how the shortlist works."""

    name = models.CharField(max_length=80, default='Philmnight')

    logo: models.ImageField  # FIXME: Temporary fix until move away from storing icon in DB
    logo = models.ImageField(upload_to='config/', default='logo/default.png')
    logo_favicon = models.ImageField(upload_to='logo/', blank=True, null=True)

    shortlist = models.ManyToManyField(Film)
    shortlist_length = models.IntegerField(default=8)
    last_shortlist = models.DateTimeField()
    odd_weeks = models.BooleanField(default=False)
    stylesheet = models.FileField(upload_to='config/', default='config/stylesheet.css')

    def __str__(self) -> str:
        """Return string representation of film config."""
        return self.name

    # pylint: disable=signature-differs
    def clean(self, *args: Any, **kwargs: Any) -> None:
        """Override clean function so shortlist can't be overpopulated."""
        if self.shortlist.count() > self.shortlist_length:
            raise ValueError('Shortlist length exceeds max')
        super().clean(*args, **kwargs)

    # pylint: disable=signature-differs
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save method of config to automatically resize images."""
        if FilmConfig.objects.filter(id=1).exists() and self.id != 1:
            raise IntegrityError('Only one instance of FilmConfig may exist in the database')

        self.id = 1  # pylint: disable=all

        image = Image.open(self.logo)
        image.save('media/logo/logo.png', format='png')
        image = image.resize((32, 32), Image.ANTIALIAS)
        image.save('media/logo/favicon.png', format='png')
        self.logo_favicon = 'logo/favicon.png'
        self.logo = 'logo/logo.png'

        super(FilmConfig, self).save(*args, **kwargs)


# FIXME: Switch to custom user class and ditch this class
class Profile(models.Model):
    """Model to extend the user model."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_votes = models.TextField(blank=True, default='')
    last_vote = models.DateTimeField(default=datetime.datetime.min)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override default save method in order to clean up votes."""
        current_votes = self.current_votes.split(',')
        for item in current_votes:
            if item == '':
                current_votes.remove(item)

        self.current_votes = ','.join(current_votes)
        super(Profile, self).save(*args, **kwargs)


# FIXME: Switch to custom user class and ditch this method
@receiver(post_save, sender=User)
def create_user_profile(_, instance, created, **_) -> None:  # type: ignore
    """Create profile when user created."""
    if created:
        Profile.objects.create(user=instance)


# FIXME: Switch to custom user class and ditch this method
@receiver(post_save, sender=User)
def save_user_profile(_, instance, **_) -> None:  # type: ignore
    """Save profile when user saved."""
    try:
        instance.profile.save()
    except AttributeError:
        Profile.objects.create(user=instance)
