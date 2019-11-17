from django.db import models


class Film(models.Model):
    name = models.CharField(max_length=70, blank=False)
    vote_count = models.IntegerField(default=0)
    in_current_vote = models.BooleanField(default=False)
