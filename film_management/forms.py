from django.forms import ModelForm

from film_management.models import FilmConfig


class FilmConfigForm(ModelForm):

    class Meta:
        model = FilmConfig
        fields = ['name', 'shortlist', 'shortlist_length', 'next_filmnight',
                  'voting_length']
