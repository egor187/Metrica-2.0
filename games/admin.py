from django.contrib import admin
from .models import Games, GameSession, GameScores


class CustomGameScoresAdmin(admin.ModelAdmin):
    model = GameScores
    list_select_related = ("user", "game_session", "game_session__game")


class CustomGameSessionAdmin(admin.ModelAdmin):
    model = GameSession
    list_select_related = ("game",)


admin.site.register(Games)
admin.site.register(GameSession, CustomGameSessionAdmin)
admin.site.register(GameScores, CustomGameScoresAdmin)
