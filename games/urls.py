import os
from django.urls import path
from games import views
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

stats_bot_token = os.getenv("STATS_BOT_TOKEN_TEST")

app_name = 'games'

urlpatterns = [
    path('', views.GamesListView.as_view(), name='games_index'),
    path('<int:pk>/', views.GamesDetailView.as_view(), name='games_detail'),
    path('add_game/', views.GamesAddView.as_view(), name='add_game'),
    path('add_game_from_bot/', views.GamesAddBotView.as_view(), name='add_game_from_bot'),
    path('game_check_for_bot/', views.GameCheck.as_view(), name='game_check'),
    path('stats_proceed/' + stats_bot_token, views.stats_proceed_view, name='stats_proceed_from_bot'),
]
