from django.db import models
from users.models import CustomUser


class Games(models.Model):
    name = models.CharField('Game name', max_length=100, unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/games/{self.id}/'


class GameSession(models.Model):
    game = models.ForeignKey(Games, on_delete=models.CASCADE, to_field='name', default='default_game')
    created_at = models.DateTimeField()


class GameScores(models.Model):
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='game_session')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, to_field='username')
    score = models.IntegerField('score')