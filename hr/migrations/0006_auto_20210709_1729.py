# Generated by Django 3.1.7 on 2021-07-09 23:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0005_auto_20210709_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='aws_keys_added',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='site',
            name='rest_key_added',
            field=models.DateTimeField(null=True),
        ),
    ]