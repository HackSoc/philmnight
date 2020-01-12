"""Views for handling discord authorisation."""
import random
import string

import requests
from requests_oauthlib import OAuth2Session

from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db import IntegrityError

DISCORD_REDIRECT_URI = ('https://discordapp.com/api/oauth2/authorize?client_id'
                        '=644830838462218241&redirect_uri=https%3A%2F%2Fhackso'
                        'c-film-night.herokuapp.com%2Fdiscord%2Fverify&respons'
                        'e_type=code&scope=identify%20guilds')

API_ENDPOINT = 'https://discordapp.com/api/v6'
CLIENT_ID = '644830838462218241'
CLIENT_SECRET = 'rIdG5AnCCWu-eap5-Myasd7BFnXHr6L9'
REDIRECT_URI = 'https://hacksoc-film-night.herokuapp.com/discord/verify'

COMPSCI_YORK_ID = '615499539218169866'


def make_session(token=None, state=None, scope=None):
    """Create an OAuth2Session with discord's api."""
    return OAuth2Session(
        client_id=CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=REDIRECT_URI)


def auth(request):
    """Redirect a user to discord's auth page."""
    # Skip auth process if user already logged in
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    return HttpResponseRedirect(DISCORD_REDIRECT_URI)


def verify(request):
    """Verify a provided code against discord's servers."""
    # Skip verification process if user already logged in
    if not request.user.is_authenticated:
        code = request.GET.get('code', None)

        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'scope': 'identify email connections'
        }

        # Required headers for discord api request
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        token_request = requests.post('%s/oauth2/token' % API_ENDPOINT,
                                      data=data, headers=headers)

        discord = make_session(token=token_request.json())

        user_data = discord.get(API_ENDPOINT+'/users/@me').json()
        user_guilds = discord.get(API_ENDPOINT+'/users/@me/guilds').json()
        print(user_data)
        compsci_discord = False
        for guild in user_guilds:
            if guild['id'] == COMPSCI_YORK_ID:
                compsci_discord = True

            if compsci_discord:
                try:
                    username = (user_data['username'] +
                                '#' + user_data['discriminator'])
                    password = ''.join([random.choice(
                        string.ascii_letters+string.digits) for n in range(32)]
                                      )
                    user = User.objects.create_user(username,
                                                    password=password)
                    user.email = user_data['id']
                    user.save()
                except IntegrityError:
                    user = User.objects.get(email=user_data['id'])
                login(request, user)

    return HttpResponseRedirect('/')
