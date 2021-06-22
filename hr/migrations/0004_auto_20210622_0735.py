# Generated by Django 3.1.7 on 2021-06-22 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0003_auto_20210316_1201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='rest_key',
            field=models.CharField(blank=True, default='', help_text='On your server, set a config var called OTREE_REST_KEY, and add it here also, so that oTree HR can authenicate with your server.', max_length=255, verbose_name='OTREE_REST_KEY'),
        ),
    ]
