# Generated by Django 4.1.6 on 2023-04-13 00:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_remove_table_pot_remove_table_singleplayerid_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='card',
            old_name='userID',
            new_name='playerID',
        ),
    ]