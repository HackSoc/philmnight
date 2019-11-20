from django.db import models


class Film(models.Model):
    name = models.CharField(max_length=70, blank=False)
    film_id = models.CharField(max_length=70, unique=True, blank=True)
    vote_count = models.IntegerField(default=0)
    in_current_vote = models.BooleanField(default=False)

    date_submitted = models.DateTimeField(auto_now_add=True, blank=True)

    def save(self, *args, **kwargs):
        self.film_id = self.name.replace(' ', '').lower()

        super(Film, self).save(*args, **kwargs)
