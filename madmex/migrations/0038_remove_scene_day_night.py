# Generated by Django 2.0.5 on 2018-05-05 23:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('madmex', '0037_scene'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scene',
            name='day_night',
        ),
    ]
