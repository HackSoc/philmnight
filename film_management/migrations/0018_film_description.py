# Generated by Django 2.2.2 on 2020-01-31 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('film_management', '0017_auto_20200131_1241'),
    ]

    operations = [
        migrations.AddField(
            model_name='film',
            name='description',
            field=models.TextField(default='', null=True),
        ),
    ]
