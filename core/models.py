"""Core models for Philmnight."""
import datetime
from typing import Any

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Override the default django user model."""

    current_votes = models.TextField(blank=True, default='')
    last_vote = models.DateTimeField(default=datetime.datetime.min)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override default save method in order to clean up votes."""
        current_votes = self.current_votes.split(',')
        for item in current_votes:
            if item == '':
                current_votes.remove(item)

        self.current_votes = ','.join(current_votes)
        super().save(*args, **kwargs)
