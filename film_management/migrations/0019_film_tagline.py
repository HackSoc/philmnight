# Generated by Django 2.2.2 on 2020-01-31 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('film_management', '0018_film_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='film',
            name='tagline',
            field=models.TextField(default='', null=True),
        ),
    ]
