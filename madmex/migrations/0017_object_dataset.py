# Generated by Django 2.0 on 2018-02-02 00:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('madmex', '0016_auto_20180119_2014'),
    ]

    operations = [
        migrations.AddField(
            model_name='object',
            name='dataset',
            field=models.CharField(default=None, max_length=100),
        ),
    ]