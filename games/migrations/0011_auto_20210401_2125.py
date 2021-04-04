# Generated by Django 3.1.7 on 2021-04-01 18:25

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0010_auto_20210401_1751'),
    ]

    operations = [
        migrations.AlterField(
            model_name='games',
            name='cover_art',
            field=models.ImageField(max_length=120, null=True, upload_to='uploads/games_cover/%Y/%m/%d/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['exe'])]),
        ),
    ]