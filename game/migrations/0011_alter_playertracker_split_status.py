# Generated by Django 4.1.6 on 2023-04-13 01:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0010_playertracker_split_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playertracker',
            name='split_status',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
