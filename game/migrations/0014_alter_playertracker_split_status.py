# Generated by Django 4.1.6 on 2023-04-19 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0013_playertracker_json_cache'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playertracker',
            name='split_status',
            field=models.IntegerField(default=None, null=True),
        ),
    ]
