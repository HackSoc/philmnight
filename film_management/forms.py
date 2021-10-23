import datetime
from typing import cast

from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.forms import ModelForm

from film_management.models import Film, FilmConfig


class FilmConfigForm(ModelForm):

    class Meta:
        model = FilmConfig
        fields = ['name', 'shortlist', 'shortlist_length', 'next_filmnight',
                  'voting_length']

    def clean(self):
        """Override clean function so shortlist can't be overpopulated."""
        errors = []

        cleaned_data = super().clean()
        voting_length = cast(datetime.timedelta, cleaned_data.get('voting_length'))
        filmnight_timedelta = cast(datetime.timedelta, cleaned_data.get('filmnight_timedelta'))

        shortlist = cast(QuerySet[Film], cleaned_data.get('shortlist'))
        shortlist_length = cast(int, cleaned_data.get('shortlist_length'))

        if voting_length > filmnight_timedelta:
            errors.append(ValidationError(
                'Voting period length should be less than time between filmnights',
                code='voting_too_long'
            ))

        if shortlist.count() > shortlist_length:
            errors.append(ValidationError('Shortlist length exceeds max',
                                          code='shortlist_too_long'))

        if errors:
            raise ValidationError(errors)
