# Generated by Django 2.2.2 on 2019-11-28 12:42

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('film_management', '0013_auto_20191128_1240'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='last_vote',
            field=models.DateTimeField(default=datetime.datetime(1, 1, 1, 0, 0)),
            preserve_default=False,
        ),
    ]