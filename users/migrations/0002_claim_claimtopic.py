# Generated by Django 3.1.7 on 2021-03-20 15:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClaimTopic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('adding a game', 'adding a game'), ('error in statistics', 'error in statistics'), ('wishes', 'wishes'), ('general issues', 'general issues')], max_length=25)),
            ],
        ),
        migrations.CreateModel(
            name='Claim',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('claim', models.TextField(verbose_name='text of the claim')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('answer_date_expiration', models.DateTimeField()),
                ('claimer', models.ForeignKey(default='claimer is delete from db', on_delete=django.db.models.deletion.SET_DEFAULT, to=settings.AUTH_USER_MODEL)),
                ('topic', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='claims', to='users.claimtopic')),
            ],
        ),
    ]
