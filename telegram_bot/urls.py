import os

from django.urls import path

from dotenv import load_dotenv, find_dotenv

from telegram_bot import views


app_name = 'telegram_bot'

load_dotenv(find_dotenv())

stats_bot_token = os.getenv("STATS_BOT_TOKEN_TEST")

urlpatterns = [
    path('stats_proceed/' + stats_bot_token, views.stats_proceed_view, name='stats_proceed_from_bot'),

]