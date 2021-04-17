from django.urls import path

from games import views


app_name = 'games'

urlpatterns = [
    path('', views.GamesListView.as_view(), name='games_index'),
    path('<int:pk>/', views.GamesDetailView.as_view(), name='games_detail'),
    path('add_game/', views.GamesAddView.as_view(), name='add_game'),
    path('add_game_from_bot/', views.GamesAddBotView.as_view(), name='add_game_from_bot'),
    path('game_check_for_bot/', views.GameCheck.as_view(), name='game_check'),
]
