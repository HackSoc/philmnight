# Generated by Django 2.2.2 on 2020-03-09 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('film_management', '0027_auto_20200212_1352'),
    ]

    operations = [
        migrations.AddField(
            model_name='filmconfig',
            name='name',
            field=models.CharField(default='Philmnight', max_length=80),
        ),
    ]
