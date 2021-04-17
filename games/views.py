import os
import json
import logging

from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.utils.decorators import method_decorator
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.db.models import Sum, Count

from games.models import Games, GameScores
from games.forms import GameCreationForm
from users.models import CustomUser

from games.db_actions import get_game_id_by_name, add_game_into_db_single_from_bot
from Metrica_project.stats_bot import StatsBot
from games.filter import GameFilter


stats_bot_token = os.getenv("STATS_BOT_TOKEN_TEST")
stats_bot = StatsBot(stats_bot_token)
logger = logging.getLogger("Metrica_logger")


@csrf_exempt
def stats_proceed_view(request):
    request_json = json.loads(request.body)
    stats_bot.process_update(request_json)

    # Бот в нашей реализации ничего не ждет от view, а лишь парсит body в json и использует его
    return HttpResponse()  # "view ALWAYS must return response". В этом случае - пустой instance HttpResponse


class GamesDetailView(DetailView):
    model = Games
    template_name = 'games_detail.html'
    context_object_name = 'game'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        users = CustomUser.objects.prefetch_related("scores") \
            .filter(scores__game_session__game__id=self.kwargs["pk"]) \
            .annotate(played_games_count=Count("scores__game_session"))

        context['played_games_by_players'] = users

        users_with_scores = list(map(lambda user: dict(name=user.username,
                                                       score=GameScores.objects.filter(
                                                           game_session__game__pk=self.kwargs['pk']).filter(
                                                           user=user).aggregate(Sum('score'))['score__sum']), users))

        context["users"] = users_with_scores

        # We put this to server data as JSON and read from Javascript side
        context['server_data'] = {
            "users": users_with_scores
        }

        # Аннотация количества сыгранных сессий для каждой игры для каждого юзера
        # CustomUser.objects.annotate(played_games_count=Count("scores__game_session"))

        return context


# per-view caching (method decorator to convert view decorator to method of the class.
# For cache framework need acces to request, so method of the class should contained it.
# In 'list'-CBV one of that method - is 'get')
@method_decorator(cache_page(120, cache='fs_cache'), name='get')
class GamesListView(ListView):
    model = Games
    template_name = 'games_index.html'
    context_object_name = 'games'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context["filter"] = GameFilter(
            self.request.GET)

        for game in Games.objects.all():
            context[game.name] = CustomUser.objects.filter(scores__game_session__game__name=game.name).distinct()

        if self.request.user.is_authenticated:
            if self.request.GET.get('self_game_sessions') == "on":
                context['filter'] = GameFilter(
                    self.request.GET,
                    queryset=Games.objects.filter(sessions__scores__user=self.request.user).distinct()
                )

        # Realization with sessions in filter
        # if self.request.user.is_authenticated:
        #     if self.request.GET.get('self_game_sessions') == "on":
        #         context['filter'] = GamesFilter(
        #             self.request.GET,
        #             queryset=GameSession.objects.filter(scores__user=self.request.user)
        #         )

        return context


class GamesAddView(CreateView):
    model = Games
    form_class = GameCreationForm
    template_name = 'add_game.html'


@method_decorator(csrf_exempt, name='dispatch')
class GamesAddBotView(View):
    def post(self, request):
        game_name = request.POST["game_name"]
        try:
            avatar = request.FILES["avatar"]
        except MultiValueDictKeyError as e:
            logger.info("No image for cover provided. Apply default cover for case 'new game'")
            result = add_game_into_db_single_from_bot(game_name)
        else:
            result = add_game_into_db_single_from_bot(game_name, avatar)
        return HttpResponse(result)


@method_decorator(csrf_exempt, name="dispatch")
class GameCheck(View):
    def get(self, request):
        game_name = request.GET.get("game_name")
        result = {"exist_game": get_game_id_by_name(game_name)}

        return JsonResponse(result)
