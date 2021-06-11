import django.conf

from Metrica_project.celery import app
from telegram_bot.models import Chat
from telegram_bot.services import send_statistic_to_tg_bot
from telegram_bot.db_actions import get_weekly_top_players_public_sessions_repr


BOT_TOKEN = django.conf.settings.BOT_TOKEN


@app.task()
def weekly_stats_tg_notice_top_players(bot_token=BOT_TOKEN):
    """
    Task for celery scheduler
    """
    chats_ids = Chat.objects.filter(is_stats_deliver_ordered=True).values_list('chat_id', flat=True)
    stats_message = get_weekly_top_players_public_sessions_repr()
    send_statistic_to_tg_bot(chats_ids, stats_message, bot_token)
