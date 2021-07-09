from django.conf import settings

import requests
import datetime as date
import logging
from spellchecker import SpellChecker

from django.urls import reverse_lazy
from django.utils.text import format_lazy

from telegram import Bot, Update, ForceReply
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, ConversationHandler, UpdateFilter
from dotenv import load_dotenv, find_dotenv

from Metrica_project.income_msg_parser import parse_message
from games.db_actions import stats_repr, add_scores, get_game_names_list, get_game_id_by_name, add_tg_animation_scores
from .db_actions import top_3_week_players_repr_public_sessions
from telegram_bot.models import Chat

load_dotenv(find_dotenv())

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Metrica_logger')

site_root_url = settings.PROJECT_ROOT_URL

# like fstring, but evaluate "lazy objects"
USER_REGISTRATION_URL = format_lazy("{}{}", site_root_url, reverse_lazy('users:add_user_from_bot'))
ADD_GAME_URL = format_lazy("{}{}", site_root_url, reverse_lazy('games:add_game_from_bot'))
GAME_CHECK_URL = format_lazy("{}{}", site_root_url, reverse_lazy('games:game_check'))


GAME_NAME, GAME_COVER = range(2)


class ReplyToMessageFilter(UpdateFilter):
    def filter(self, update):
        if update.message.reply_to_message:
            return update.message.reply_to_message.from_user.is_bot
        else:
            return


reply_to_message_filter = ReplyToMessageFilter()


class StatsBot:

    def __init__(self, token):
        self.bot = Bot(token)
        self.dispatcher = Dispatcher(self.bot, None, workers=0)
        self.dispatcher.add_handler(CommandHandler("add_stats", add_stats_command))
        self.dispatcher.add_handler(CommandHandler("show_current_stats", show_stats_command))
        self.dispatcher.add_handler(CommandHandler("register_user", process_register_user_command))
        self.dispatcher.add_handler(CommandHandler("set_stats_scheduler", set_weekly_top_players_stats_schedule))
        self.dispatcher.add_handler(CommandHandler("unset_stats_scheduler", unset_weekly_top_players_stats_schedule))
        self.dispatcher.add_handler(CommandHandler("cancel", cancel))
        self.dispatcher.add_handler(conv_handler_add_game)
        self.dispatcher.add_handler(conv_handler_weekly_stats)
        self.dispatcher.add_handler(
            MessageHandler(
                ~Filters.command &
                reply_to_message_filter &
                (~Filters.animation) &
                ~Filters.sticker,
                process_bot_reply_message
            )
        )
        self.dispatcher.add_handler(MessageHandler(Filters.animation | Filters.sticker, animation_callback))
        self.dispatcher.add_handler(MessageHandler(~Filters.animation | ~Filters.sticker, linter))

    def process_update(self, request):
        update = Update.de_json(request, self.bot)
        logger.debug(f'Update decoded: {update.update_id}')
        self.dispatcher.process_update(update)
        logger.debug(f'Stats request processed successfully: {update.update_id}')
        chat_id = update.effective_chat.id
        Chat.objects.get_or_create(chat_id=chat_id)


def animation_callback(update, context):
    user_name = update.message.from_user.username
    score = 1
    update.message.reply_text(f"Статы (+1) ботяры '{user_name}' занесены в Метрику")
    add_tg_animation_scores(user_name, score)


def add_game_command(update, context):
    context.user_data["last_command"] = "GAME"
    update.message.reply_text(
        f'Добавить игру',
        reply_markup=ForceReply())


def linter(update, context):
    """
    Spell check chat messages
    """
    spell = SpellChecker(language='ru')
    sentence = update.message.text
    words_list = spell.split_words(sentence)
    mistakes_set = spell.unknown(words_list)
    if mistakes_set:
        update.message.reply_text(f" Ну что бля за '{', '.join(list(mistakes_set))}'?")


def process_add_game_command(update, context):
    game = update.message.text
    avatar = update.message.photo[-1].get_file()
    response = requests.post(ADD_GAME_URL, data={'game_name': game}, files={'avatar': avatar.download_as_bytearray()})
    update.message.reply_text(response.text)


def process_register_user_command(update, context):
    # Store the command in context to check later in message processors
    user = update.message.from_user.username
    context.user_data["last_command"] = "REGISTER"
    update.message.reply_text(
        f'Send any text in response to this message to register you with tg account name "{user}". '
        f'Or send command "/cancel" - to cancel process',
        reply_markup=ForceReply())


def register_user_command(update, context):
    """
    Register user in Metrica db with actual tg account name
    """
    user = update.message.from_user.username
    response = requests.post(USER_REGISTRATION_URL, json={"user": str(user)})
    update.message.reply_text(response.text)


def add_stats_command(update, context):
    # Store the command in context to check later in message processors
    context.user_data["last_command"] = "ADD"
    update.message.reply_text(
        f'Добавить статы для активности (уже зарегистрированные: {", ".join(get_game_names_list())}).'
        f' "/cancel" - чтобы отменить процедуру',
        reply_markup=ForceReply(selective=True))


def show_stats_command(update, context):
    # Store the command in context to check later in message processors
    context.user_data["last_command"] = "SHOW"
    update.message.reply_text(
        f'Показать статы для активности (уже зарегистрированные: {", ".join(get_game_names_list())}).'
        f' "/cancel" - чтобы отменить процедуру',
        reply_markup=ForceReply(selective=True))


def process_unknown_message(update, context):
    update.message.reply_text('В эту игру вы еще не шпилили')


def process_wrong_message(update, context):
    update.message.reply_text('Не получилось обработать запрос')


def is_scores_message(update):
    return ':' in update.message.text


def is_known_activity_message(update):
    game = parse_message(update.message.text)
    return True if get_game_id_by_name(game) else False


def process_bot_reply_message(update, context):
    try:
        last_command = context.user_data["last_command"]
        if last_command == 'ADD' and is_scores_message(update):
            process_add_stats_message(update, context)
        elif last_command == 'SHOW':
            if is_scores_message(update):
                process_wrong_message(update, context)

            elif is_known_activity_message(update):
                process_show_stats_message(update, context)
            else:
                process_unknown_message(update, context)
        elif last_command == 'REGISTER':
            register_user_command(update, context)
    except KeyError:
        update.message.reply_text('Unrecognized command/message')


def process_show_stats_message(update, context):
    data = update.message.text
    game = parse_message(data)
    score_pairs = stats_repr(game)

    if isinstance(score_pairs, dict):
        result_dict = score_pairs

    result_msg = f'На {date.datetime.today().replace(microsecond=0)} ' \
                 f'по игре "{game}" {"общие статы ВСЕХ игрокококов такие"}:\n'
    for user_name, score in result_dict.items():
        result_msg += user_name + ': ' + str(score) + '\n'

    update.message.reply_text(result_msg)


def process_add_stats_message(update, context):
    data = update.message.text
    game, score_pairs = parse_message(data)
    result_dict = add_scores(game, score_pairs)
    if isinstance(result_dict, str):
        negative_score_msg = result_dict
        update.message.reply_text(negative_score_msg)
        return

    result_msg = f'На {date.datetime.today().replace(microsecond=0)} ' \
                 f'по игре "{game}" {"статы для текущих игрококов"}:\n'
    for user_name, score in result_dict.items():
        result_msg += user_name + ': ' + str("Register first, please" if not score else score) + '\n'

    update.message.reply_text(result_msg)


def add_game_start(update, context):
    update.message.reply_text('What is the name of the game?')

    return GAME_NAME


def game_name(update, context):
    context.user_data['game_name'] = update.message.text

    response = requests.get(GAME_CHECK_URL, params={'game_name': context.user_data['game_name']})

    if response.json()["exist_game"]:
        update.message.reply_text(f'Game "{context.user_data["game_name"]}" already tracking by Metrica!')
        return cancel(update, context)
    else:
        update.message.reply_text(
            "Send me cover for your game OR send any text in response to register game with default cover"
        )
        return GAME_COVER


def game_cover(update, context):
    game_name = context.user_data["game_name"]
    update.message.reply_text(f"Processing the cover for the '{game_name}'...")
    try:
        photo = update.message.photo[-1].get_file()
        requests.post(ADD_GAME_URL, data={'game_name': game_name}, files={'avatar': photo.download_as_bytearray()})
    except IndexError:
        requests.post(ADD_GAME_URL, data={'game_name': game_name})
    update.message.reply_text(f'New game "{game_name}" added to Metrica!')
    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text('End dialog')
    context.user_data.clear()  # clean context with /cancel bot-command for success tracking all msgs to catch GIFs
    return ConversationHandler.END


def default_cover_process(update, context):
    update.message.reply_text('Creating game with default cover...')
    game_name = context.user_data["game_name"]
    requests.post(ADD_GAME_URL, data={'game_name': game_name})
    update.message.reply_text(f'New game "{game_name}" added to Metrica!')
    return ConversationHandler.END


conv_handler_add_game = ConversationHandler(
    entry_points=[CommandHandler('add_game', add_game_start)],
    states={
        GAME_NAME: [MessageHandler(Filters.text & ~Filters.command, game_name)],
        GAME_COVER: [MessageHandler(Filters.photo | Filters.text, game_cover)]
    },
    fallbacks=[
        CommandHandler('cancel', cancel),
        MessageHandler(Filters.text, default_cover_process),
    ]
)


def weekly_stats_start(update, context):
    update.message.reply_text('What is the name of the game for "top 3 players" you want get?')

    return 0


def game_name_for_weekly_stats(update, context):
    context.user_data['game_name'] = update.message.text

    response = requests.get(GAME_CHECK_URL, params={'game_name': context.user_data['game_name']})

    if response.json()["exist_game"]:
        update.message.reply_text('What period? (integer -> number of weeks before now)')
        return 1

    else:
        update.message.reply_text(f'Game "{context.user_data["game_name"]}" is not registered in Metrica!')
        return cancel(update, context)


def send_stats_message(update, context):
    game_name = context.user_data["game_name"]
    period = update.message.text
    bot_answer = top_3_week_players_repr_public_sessions(game_name, period)
    update.message.reply_text(bot_answer)
    return ConversationHandler.END


conv_handler_weekly_stats = ConversationHandler(
    entry_points=[CommandHandler('get_top_3_players_stats', weekly_stats_start)],
    states={
        0: [MessageHandler(Filters.text & ~Filters.command, game_name_for_weekly_stats)],
        1: [MessageHandler(Filters.text, send_stats_message)],
    },
    fallbacks=[
        CommandHandler('cancel', cancel),
    ]
)


def set_weekly_top_players_stats_schedule(update, context):
    """
    Set 'is_stats_deliver_ordered' 'Chat' model to 'True'
    """
    chat_id = update.effective_chat.id
    update.message.reply_text("I will send you 'top players of the week' statistic every monday")

    # Instead of using Model.update() method which is not call Model.save() method and update objects on SQL level
    # --Chat.objects.filter(chat_id=chat_id).update(is_stats_deliver_ordered=True)--
    # use 'ORM'-level for updating objects with Model.save() method calling because it's need for 'auto_now' arg of
    # a model field
    chat = Chat.objects.get(chat_id=chat_id)
    chat.is_stats_deliver_ordered = True
    chat.save()


def unset_weekly_top_players_stats_schedule(update, context):
    """
    Set 'is_stats_deliver_ordered' 'Chat' model to 'True'
    """
    chat_id = update.effective_chat.id
    update.message.reply_text("Subscription for stats mailing is canceled. Have a nice day")
    Chat.objects.filter(chat_id=chat_id).update(is_stats_deliver_ordered=False)
