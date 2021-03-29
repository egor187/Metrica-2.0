import os
import json
from games.models import Games, GameSession, GameScores
from games.forms import GameCreationForm
from users.models import CustomUser
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from games.db_actions import get_game_id_by_name, get_game_object_by_id, \
    add_game_into_db, add_game_session_into_db, add_scores
from django.views.decorators.csrf import csrf_exempt
from Metrica_project.stats_bot import StatsBot
from django.db.models import Sum
from games.filter import GamesFilter

stats_bot_token = os.getenv("STATS_BOT_TOKEN_TEST")
stats_bot = StatsBot(stats_bot_token)


@csrf_exempt
def stats_proceed_view(request):
    request_json = json.loads(request.body)
    stats_bot.process_update(request_json)

    # Бот в нашей реализации ничего не ждет от view, а лишь парсит body в json и использует его
    return HttpResponse()  # view ALWAYS must return response. В этом случае - пустой instance HttpResponse


class GamesDetailView(DetailView):
    model = Games
    template_name = 'games_detail.html'
    context_object_name = 'game'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        users = CustomUser.objects.distinct().filter(scores__game_session__game__pk=self.kwargs['pk'])

        users_with_scores = list(map(lambda user: dict(name=user.username,
                                      score=GameScores.objects.filter(game_session__game__pk=self.kwargs['pk']).filter(
                                          user=user).aggregate(Sum('score'))['score__sum']), users))

        context["users"] = users_with_scores

        # We put this to server data as JSON and read from Javascript side
        context['server_data'] = {
            "users": users_with_scores
        }

        return context


class GamesListView(ListView):
    model = Games
    template_name = 'games_index.html'
    context_object_name = 'games'

    def get_context_data(self, *, object_list=None, **kwargs):

        context = super().get_context_data(object_list=Games.objects.all().prefetch_related("sessions", "sessions__scores"))

        if self.request.user.is_authenticated:
            if self.request.GET.get('self_game_sessions') == "on":
                context['filter'] = GamesFilter(
                    self.request.GET,
                    queryset=GameSession.objects.filter(scores__user=self.request.user).prefetch_related("sessions", "sessions__scores")
                )
        else:
            context["filter"] = GamesFilter(
                self.request.GET)

        context["game_session_boost"] = GameSession.objects.all().prefetch_related("game", "scores")

        return context


class GamesAddView(CreateView):
    model = Games
    form_class = GameCreationForm
    template_name = 'add_game.html'
