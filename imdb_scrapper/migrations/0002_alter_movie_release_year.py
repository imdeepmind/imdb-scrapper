# Generated by Django 4.2.18 on 2025-01-21 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imdb_scrapper', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='release_year',
            field=models.CharField(max_length=2, null=True),
        ),
    ]
