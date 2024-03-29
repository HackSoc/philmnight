# Generated by Django 3.2 on 2021-10-19 22:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('film_management', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='filmconfig',
            name='odd_weeks',
        ),
        migrations.AddField(
            model_name='filmconfig',
            name='filmnight_timedelta',
            field=models.DurationField(default=datetime.timedelta(days=3)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='filmconfig',
            name='next_filmnight',
            field=models.DateTimeField(default=datetime.datetime(2021, 10, 19, 22, 50, 3, 71619)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='filmconfig',
            name='voting_period_length',
            field=models.DurationField(default=datetime.timedelta(days=1)),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Profile',
        ),
    ]
