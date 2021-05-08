import os
import json
import datetime

from django.shortcuts import render
from django.urls import reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.views.generic.list import ListView, View
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import ExtractIsoWeekDay
from django.db.models import Sum, Count
from django.core import serializers
from django.core.mail import send_mail
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

from dotenv import load_dotenv, find_dotenv
import jwt

import users.models
from games.models import Games, GameSession, GameScores
from .forms import CustomUserCreationForm, FeedbackForm, CustomUserAddFriendForm, CustomUserRemoveFriendForm
from users.db_actions import add_user_into_db_simple
from users.utils import get_player_calendar

load_dotenv(find_dotenv())
site_root_url = settings.PROJECT_ROOT_URL


class UsersLoginView(LoginView):
    success_message = '%(username)s was successfully login'
    template_name = 'log_in_out.html'

    def get_success_url(self):
        """
        Override classmethod to achieve redirect to profile page in buil-in auth CBV
        :return:
        """
        url = reverse_lazy('users:users_detail', args=[self.request.user.id, ])
        return url


class UsersLogoutView(LogoutView):
    success_message = '%(username)s was successfully logout'
    template_name = 'log_in_out.html'


class UsersListView(LoginRequiredMixin, ListView):
    model = users.models.CustomUser
    template_name = 'users_index.html'
    context_object_name = 'users_list'


    def get_queryset(self):
        """
        Override parent method to get custom queryset depends on 'friendship' field of a request.user
        :return: only friends of request.user or all() for request.user.is_staff=True
        """
        if self.request.user.is_staff:
            return users.models.CustomUser.objects.all()

        self.friends_list = list(self.request.user.friendship.values_list('username', flat=True))
        result = users.models.CustomUser.objects.filter(username__in=self.friends_list)

        return result.union(users.models.CustomUser.objects.filter(pk=self.request.user.pk))


class UsersDetailView(LoginRequiredMixin, DetailView):
    model = users.models.CustomUser
    template_name = 'users_detail.html'
    perm_denied_msg = 'Permission denied. Only owner can view profile'

    def get(self, request, *args, **kwargs):
        """
        Override super_method to achieve filtering access only to autherized user
        """
        self.friends_pk_list = list(self.request.user.friendship.values_list('pk', flat=True))
        if self.get_object().pk != request.user.pk\
                and self.get_object().pk not in self.friends_pk_list\
                and not request.user.is_staff:  # more "django_style" method to call .get_object() for get instance of a model
            messages.error(request, self.perm_denied_msg)
            return HttpResponseRedirect(reverse_lazy('users:users_index'))
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        OPTIONAL
        Override parent method to get context data for template (add JSON -
        format data about current user)
        :param kwargs: captured named param from url_disptacher path()
        :return: additional context for template rendering
        """
        context = super().get_context_data(**kwargs)
        context['json'] = serializers.serialize(
            'json',
            users.models.CustomUser.objects.filter(pk=self.kwargs['pk']),
            fields=(
                'username',
                'first_name',
                'last_name',
                'Email'
            )
        )
        if self.request.user.pk != self.kwargs["pk"]:
            games = Games.objects.prefetch_related('sessions').filter(
                sessions__scores__user__pk=self.kwargs['pk'],
                sessions__is_private=False,
            ).distinct().annotate(total_score=Sum("sessions__scores__score"), times_played=Count("sessions"))
        else:
            games = Games.objects.prefetch_related('sessions').filter(
                sessions__scores__user__pk=self.kwargs['pk'],
            ).distinct().annotate(total_score=Sum("sessions__scores__score"), times_played=Count("sessions"))


        games_data = []
        for game in games:
            sessions_data = []
            if self.request.user.pk != self.kwargs['pk']:
                for session in game.sessions.filter(scores__user=self.get_object(), is_private=False):
                    session_data = {
                        "date": session.created_at,
                        "score": GameScores.objects.filter(user=self.get_object()).get(game_session=session).score,
                    }
                    sessions_data.append(session_data)
            else:
                for session in game.sessions.filter(scores__user=self.get_object()):
                    session_data = {
                        "date": session.created_at,
                        "score": GameScores.objects.filter(user=self.get_object()).get(game_session=session).score,
                    }
                    sessions_data.append(session_data)

            if not sessions_data:
                continue

            game_data = {
                "name": game.name,
                "cover": game.cover_art,
                "total_score": game.total_score,
                "times_played": game.times_played,
                "sessions": sessions_data
            }
            games_data.append(game_data)

        context["games"] = games_data


        if self.request.user.pk == self.kwargs['pk']:
            context["last_five_games_played"] = Games.objects.prefetch_related('sessions').filter(
                sessions__scores__user__pk=self.kwargs['pk']
            ).distinct().annotate(player_score=Sum("sessions__scores__score"))

        else:
            context["last_five_games_played"] = Games.objects.prefetch_related('sessions').filter(
                sessions__scores__user__pk=self.kwargs['pk'],
                sessions__is_private=False
            ).distinct().annotate(player_score=Sum("sessions__scores__score"))

        games = Games.objects.prefetch_related('sessions').filter(
            sessions__scores__user__pk=self.kwargs['pk']
        ).distinct().annotate(total_score=Sum("sessions__scores__score"), times_played=Count("sessions"))

        games_data = []
        for game in games:
            sessions_data = []
            for session in game.sessions.filter(scores__user=self.get_object()):
                session_data = {
                    "date": session.created_at,
                    "score": GameScores.objects.filter(user=self.get_object()).get(game_session=session).score,
                }
                sessions_data.append(session_data)
            game_data = {
                "name": game.name,
                "cover": game.cover_art,
                "total_score": game.total_score,
                "times_played": game.times_played,
                "sessions": sessions_data
            }
            games_data.append(game_data)

        context["games"] = games_data

        context["last_five_games_played"] = Games.objects.prefetch_related('sessions').filter(
            sessions__scores__user__pk=self.kwargs['pk']
        ).distinct().annotate(player_score=Sum("sessions__scores__score"))

        context["self_sessions"] = GameSession.objects.prefetch_related('scores').filter(scores__user__id=self.kwargs["pk"])

        if self.request.user.pk == self.kwargs['pk']:
            self_game_sessions = GameSession.objects.filter(scores__user__pk=self.kwargs["pk"]).\
                annotate(weekday=ExtractIsoWeekDay("created_at"))
        else:
            self_game_sessions = GameSession.objects.filter(
                scores__user__pk=self.kwargs["pk"],
                is_private=False
            ).annotate(weekday=ExtractIsoWeekDay("created_at"))

        context['sessions'] = self_game_sessions

        context["frequency"] = get_player_calendar(self_game_sessions)

        return context


class UsersCreateView(CreateView):
    model = users.models.CustomUser
    form_class = CustomUserCreationForm
    template_name = 'user_register.html'


class UsersUpdateView(LoginRequiredMixin, UpdateView):
    model = users.models.CustomUser
    form_class = CustomUserCreationForm
    template_name = 'user_update.html'
    success_url = reverse_lazy('users:users_index')
    perm_denied_msg = 'Permission denied. Only owner can change profile'

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs['pk'] != request.user.pk:
            messages.error(request, self.perm_denied_msg)
            return HttpResponseRedirect(reverse_lazy('users:users_index'))
        return super().dispatch(request, *args, **kwargs)


# Realization with vanila View
# class FriendAddView(View):
#     form_class = CustomUserAddFriendForm
#     template_name = 'friend_add.html'
#     success_url = reverse_lazy('users:users_index')
#     perm_denied_msg = 'Permission denied. Only owner can manage friends'
#     friendship_succeed_msg  = "You've been succesfully added to '{friend}' friends. '{friend}' now can view your profile page"
#     friendship_exist_msg  = "You're already in '{friend}' friend_list."
#
#     def post(self, *args, **kwargs):
#         form = CustomUserAddFriendForm(self.request.POST)
#         if form.is_valid():
#             user = self.request.user
#             friends = form.cleaned_data['friendship']
#             for friend in friends:
#                 if friend.pk == self.request.user.pk:
#                     continue
#                 messages.info(
#                     self.request,
#                     self.friendship_succeed_msg.format(friend=friend.username)
#                 ) if not friend.friendship.filter(pk=user.pk).exists() else messages.error(
#                     self.request,
#                     self.friendship_exist_msg.format(friend=friend.username)
#                 )
#                 friend.friendship.add(user)
#             return HttpResponseRedirect(reverse_lazy('users:users_index'))
#         else:
#             messages.error(self.request, self.perm_denied_msg)
#
#             return HttpResponseRedirect(reverse_lazy('users:users_index'))
#
#     def get(self, *args, **kwargs):
#         form = CustomUserAddFriendForm()
#         form.fields['friendship'].queryset = users.models.CustomUser.objects.exclude(
#             pk=self.request.user.pk
#         ).exclude(
#             friendship__pk=self.request.user.pk
#         )
#
#         return render(self.request, self.template_name, {'form': form})


class FriendAddView(UpdateView):
    model = users.models.CustomUser
    template_name = 'friend_add.html'
    form_class = CustomUserAddFriendForm
    success_url = reverse_lazy('users:users_index')

    perm_denied_msg = 'Permission denied. Only owner can manage friends'
    friendship_succeed_msg  = "You've been succesfully added to '{friend}' friends. '{friend}' now can view your profile page"
    friendship_exist_msg  = "You're already in '{friend}' friend_list."

    def post(self, request, *args, **kwargs):
        form = CustomUserAddFriendForm(request.POST)
        if form.is_valid():
            user = request.user
            friends = form.cleaned_data['friendship']
            for friend in friends:
                if friend.pk == request.user.pk:
                    continue
                messages.info(
                    request,
                    self.friendship_succeed_msg.format(friend=friend.username)
                ) if not friend.friendship.filter(pk=user.pk).exists() else messages.error(
                    request,
                    self.friendship_exist_msg.format(friend=friend.username)
                )
                friend.friendship.add(user)
            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(request, self.perm_denied_msg)

            return HttpResponseRedirect(self.success_url)

    def get(self, request, *args, **kwargs):
        form = CustomUserAddFriendForm()
        form.fields['friendship'].queryset = users.models.CustomUser.objects.exclude(
            pk=self.request.user.pk
        ).exclude(
            friendship__pk=self.request.user.pk
        )

        return render(self.request, self.template_name, {'form': form})


class FriendRemoveView(FriendAddView):
    template_name = 'friend_remove.html'
    form_class = CustomUserRemoveFriendForm

    friendship_succeed_msg = "You've been succesfully removed from '{friend}' friends. " \
                             "'{friend}' now can't view your profile page"

    def post(self, request, *args, **kwargs):
        form = CustomUserRemoveFriendForm(request.POST)
        if form.is_valid():
            user = request.user
            friends = form.cleaned_data['friendship']
            for friend in friends:
                messages.info(
                    request,
                    self.friendship_succeed_msg.format(friend=friend.username)
                )
                friend.friendship.remove(user)
            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(request, self.perm_denied_msg)
            return HttpResponseRedirect(self.success_url)

    def get(self, *args, **kwargs):
        form = CustomUserRemoveFriendForm()
        form.fields['friendship'].queryset = users.models.CustomUser.objects.exclude(
            pk=self.request.user.pk
        ).filter(
            friendship__pk=self.request.user.pk
        )

        return render(self.request, self.template_name, {'form': form})


def invite_to_register(request):
    """
    DRAFT
    :param request:
    :return:    str()__link for user update IF user already login (useless for REST with tg_bot)
                OR redirect to registration page (form)
    """
    if request.user.id:
        return HttpResponse(f"{site_root_url}{str(reverse_lazy('users:users_update', args=[request.user.id]))}")
    return HttpResponseRedirect(reverse_lazy('users:users_register'))


@csrf_exempt  # disable csrf protection for testing via Postman by using decorator
def add_user_view(request):
    if request.method == 'POST':
        request_raw = request.body
        request_json = json.loads(request_raw)
        user = request_json['user']
        new_user_pk = add_user_into_db_simple(user)

    if request.method == 'GET':
        user = request.GET.get('user')
        new_user_pk = add_user_into_db_simple(user)

    return HttpResponse(
        f"{site_root_url}{str(reverse_lazy('users:reg_cont', args=[new_user_pk]))}"
    ) if new_user_pk else HttpResponse(
        f"Вы уже зарегистрированы. Можете перейти на сайт по этой ссылке {request.build_absolute_uri(reverse_lazy('index'))}"
    )


class UserUpdateViewFromBot(UpdateView):
    """
    Class view without @login_required and permissions check for "registration-through-bot" process
    """
    model = users.models.CustomUser
    form_class = CustomUserCreationForm
    template_name = 'user_update_from_bot.html'
    success_url = reverse_lazy('index')


def feedback_view(request):
    """
    Takes claim from "contact_us" page and send email with text to admin
    :param request:
    :return:
    """
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            send_mail(form.cleaned_data['subject'], form.cleaned_data['content'], from_email=None,
                      recipient_list=[os.getenv('DEFAULT_FROM_EMAIL'), ])
            messages.info(request, 'Письмо отправлено')
            HttpResponseRedirect(reverse_lazy('users:users_index'))
        else:
            messages.error(request, 'Невалидная форма')
            HttpResponse(reverse_lazy('users:users_index'))
    form = FeedbackForm()
    return render(request, 'feedback.html', {'form': form})


class ClaimCreateView(LoginRequiredMixin, CreateView):
    model = users.models.Claim
    form_class = FeedbackForm
    template_name = 'feedback.html'

    def form_valid(self, form):
        form.instance.claimer = self.request.user
        return super().form_valid(form)


@method_decorator(csrf_exempt, name='dispatch')
class JwtLoginView(View):
    def post(self, request):
        request_json_decoded = json.loads(request.body)
        username = request_json_decoded['username']
        password = request_json_decoded['password']

        user = users.models.CustomUser.objects.filter(username=username).first()

        payload = {
            "id": user.pk,
            "username": user.username,
            "password": password,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=1),
            "iat": datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        response = HttpResponse()

        response.set_cookie("jwt", token, httponly=True, secure=True, expires=300)

        if user is None:
            # raise ObjectDoesNotExist('User not found!')
            return HttpResponseNotFound('User not found!')

        if not user.check_password(password):
            # raise ObjectDoesNotExist('Incorrect password!')
            return HttpResponseNotFound('Incorrect password!')
        return response


@method_decorator(csrf_exempt, name='dispatch')
class JwtUserView(View):
    def get(self, requsest):
        token = requsest.COOKIES.get('jwt')

        if not token:
            return HttpResponse('No auth')

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except:
            return HttpResponse('Fake token!')

        user = users.models.CustomUser.objects.filter(id=payload['id']).first()

        authenticate(requsest, username=payload["username"], password=payload["password"])

        login(requsest, user)

        return HttpResponseRedirect(reverse_lazy('users:users_detail', args=[payload['id']]))
