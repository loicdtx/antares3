# Generated by Django 2.0.3 on 2018-04-04 22:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('madmex', '0034_auto_20180404_2115'),
    ]

    operations = [
        migrations.AddField(
            model_name='predictclassification',
            name='name',
            field=models.CharField(default='', max_length=200),
        ),
    ]