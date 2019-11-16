"""Views for handling discord authorisation."""
from django.shortcuts import render
from django.http import HttpResponseRedirect

redirect_url = 'https://discordapp.com/api/oauth2/authorize?client_id=644830838462218241&redirect_uri=https%3A%2F%2Fhacksoc-film-night.herokuapp.com&response_type=code&scope=identify'


def auth(request):
    return HttpResponseRedirect(redirect_url)
