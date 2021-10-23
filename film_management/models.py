"""Models relating to film management."""
from __future__ import annotations
import datetime
from enum import Enum
from typing import Any

from PIL import Image
from django.db import models
from django.db.utils import IntegrityError
from django.utils import timezone
import requests

from core.models import User
from philmnight.settings import TMDB_ENDPOINT, TMDB_KEY


# pylint: disable=too-many-instance-attributes
class Film(models.Model):
    """Stores information regarding an individual film."""

    # TODO: Film for associated filmnight.

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

    class Phase(Enum):
        FILMNIGHT = 0
        VOTING = 1
        SUBMISSIONS = 2

    name = models.CharField(max_length=80, default='Philmnight')

    logo: models.ImageField  # FIXME: Temporary fix until move away from storing icon in DB
    logo = models.ImageField(upload_to='config/', default='logo/default.png')
    logo_favicon = models.ImageField(upload_to='logo/', blank=True, null=True)

    shortlist = models.ManyToManyField(Film, blank=True)
    shortlist_length = models.IntegerField(default=8)
    last_shortlist = models.DateTimeField()
    stylesheet = models.FileField(upload_to='config/', default='config/stylesheet.css')

    next_filmnight = models.DateTimeField()
    filmnight_timedelta = models.DurationField()
    voting_length = models.DurationField()

    def get_phase(self) -> FilmConfig.Phase:
        """Return the current phase of voting."""
        current_time = timezone.now()

        if current_time > self.next_filmnight:
            if current_time > self.next_filmnight + datetime.timedelta(days=1):
                while current_time > self.next_filmnight + datetime.timedelta(days=1):
                    self.next_filmnight += self.filmnight_timedelta

                self.save()
                return self.get_phase()

            return FilmConfig.Phase.FILMNIGHT

        if current_time > self.next_filmnight - self.voting_length:
            return FilmConfig.Phase.VOTING

        return FilmConfig.Phase.SUBMISSIONS

    def __str__(self) -> str:
        """Return string representation of film config."""
        return self.name

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
