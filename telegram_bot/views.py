import json
import os

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from telegram_bot.stats_bot import StatsBot


stats_bot_token = os.getenv("STATS_BOT_TOKEN_TEST")
stats_bot = StatsBot(stats_bot_token)


@csrf_exempt
def stats_proceed_view(request):
    request_json = json.loads(request.body)
    stats_bot.process_update(request_json)

    # Бот в нашей реализации ничего не ждет от view, а лишь парсит body в json и использует его
    return HttpResponse()  # "view ALWAYS must return response". В этом случае - instance HttpResponse
