from django.db import models
from users.models import CustomUser


class Games(models.Model):
    name = models.CharField('Game name', max_length=100, unique=True)
    cover_art = models.ImageField(upload_to='uploads/games_cover/%Y/%m/%d/', null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/games/{self.id}/'


class GameSession(models.Model):
    game = models.ForeignKey(Games, on_delete=models.CASCADE, default='default_game', related_name='sessions')
    created_at = models.DateTimeField()
    class Meta():
        ordering = ['-created_at']

    def __str__(self):
        return str(self.created_at)


class GameScores(models.Model):
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='scores')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='scores')
    score = models.IntegerField('score')

    def __str__(self):
        return str(self.score)