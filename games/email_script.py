import os
import django

from django.core.mail import send_mail

# add <path_to_script> to system path for correct modules import.
# sys.path.append('C:\\Users\home_\PycharmProjects\Metrica_project')

os.environ['DJANGO_SETTINGS_MODULE'] = 'Metrica_project.settings'  # set Django-needed settings module
django.setup()

from django.db.models import Min
from games.models import GameSession, GameScores


def email_send():
    """
    Send email to users which score in last 5 in-game sessions was the fewest
    """
    subject = "Looser detected!?"
    message = "Tight up your game. You have scored the fewest points in last 5 in-game sessions."
    recipients_email = []

    last_five_sessions = GameSession.objects.all()[:5]
    last_five_scores = GameScores.objects.filter(game_session__in=last_five_sessions)
    min_score = GameScores.objects.filter(game_session__in=last_five_sessions).aggregate(Min('score'))['score__min']
    worst_players_row = last_five_scores.filter(score=min_score)

    for row in worst_players_row:
        if row.user.email not in recipients_email:
            recipients_email.append(row.user.email)
        else:
            continue

    send_mail(subject=subject, message=message, from_email=None, recipient_list=recipients_email)


if __name__ == '__main__':
    email_send()
