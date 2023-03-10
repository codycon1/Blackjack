# Generated by Django 4.1.6 on 2023-02-22 19:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='singleplayerID',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='card',
            name='rank',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='card',
            name='suit',
            field=models.IntegerField(),
        ),
    ]
