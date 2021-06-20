import os
import json
import datetime

from django.shortcuts import render
from django.urls import reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.views.generic.list import ListView, View
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView, FormMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import ExtractIsoWeekDay
from django.db.models import Sum, Count, F
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
from games.models import Games, GameSession
from .forms import CustomUserCreationForm, CustomUserUpdateForm, FeedbackForm, CustomUserAddFriendForm,\
    CustomUserRemoveFriendForm, FriendshipRequestAcceptForm
from users.db_actions import add_user_into_db_simple
from users.utils import get_player_calendar_with_week_day_name, get_the_most_played_day
from .filter import FriendshipRequestFilter
from .utils import avatar_double_reducer

load_dotenv(find_dotenv())
site_root_url = settings.PROJECT_ROOT_URL


class UsersLoginView(LoginView):
    success_message = '%(username)s was successfully login'
    template_name = 'log_in_out.html'

    def get_success_url(self):
        """
        Override classmethod to achieve redirect to profile page in built-in auth CBV
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

    def __init__(self, **kwargs):
        """
        Override parent method to add custom attribute for further purposes
        """
        super().__init__()
        self.friends_list = ''

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

    def __init__(self, **kwargs):
        """
        Override parent method to add custom attribute for further purposes
        """
        super().__init__()
        self.friends_pk_list = ''

    def get(self, request, *args, **kwargs):
        """
        Override super_method to achieve filtering access only to autherized user
        """
        self.friends_pk_list = list(self.request.user.friendship.values_list('pk', flat=True))
        if self.get_object().pk != request.user.pk\
                and self.get_object().pk not in self.friends_pk_list\
                and not request.user.is_staff:  # "django_style" method to call .get_object() for get model instance
            messages.error(request, self.perm_denied_msg)
            return HttpResponseRedirect(reverse_lazy('users:users_index'))
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        OPTIONAL
        Override parent method to get context data for template (add JSON -
        format data about current user)
        :param kwargs: captured named param from url_dispatcher path()
        :return: additional context for template rendering
        """
        current_user = self.object
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
        if self.request.user.pk != self.kwargs.get('pk'):
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
            if self.request.user.pk != self.kwargs['pk']:

                sessions_data = list(
                    game.sessions.filter(
                        is_private=False,
                        scores__user=current_user,
                    ).annotate(
                        date=F('created_at'),
                        score=Sum('scores__score')
                    ).values('date', 'score')
                )
                #  Expensive realization with 'for' loop: each iteration = db calls
                # for session in game.sessions.filter(scores__user=current_user, is_private=False).distinct():
                #     session_data = {
                #         "date": session.created_at,
                #         "score": GameScores.objects.filter(
                #             user=current_user,
                #             game_session=session
                #         ).aggregate(Sum('score'))['score__sum'],
                #     }
                #     sessions_data.append(session_data)

            else:
                sessions_data = list(
                    game.sessions.filter(
                        scores__user=current_user
                    ).annotate(
                        date=F('created_at'),
                        score=Sum('scores__score')
                    ).values('date', 'score')
                )

                #  Expensive realization with 'for' loop: each iteration = db calls
                # for session in game.sessions.filter(scores__user=current_user).distinct():
                #     session_data = {
                #         "date": session.created_at,

                        #  Realization with access through related GameSession object
                        # "score": session.scores.filter(
                        #     user=current_user,
                        # ).aggregate(Sum('score'))['score__sum'],

                        #  Realization with raw access to GameScores object
                        # "score": GameScores.objects.filter(
                        #     user=current_user,
                        #     game_session=session
                        # ).aggregate(Sum('score'))['score__sum'],
                    # }
                    # sessions_data.append(session_data)

            if not sessions_data:
                continue

            if bool(game.cover_art):  # checks for associated file for "cover_art" field (model attr)
                game_data = {
                    "name": game.name,
                    "cover": game.cover_art.url,
                    "total_score": game.total_score,
                    "times_played": game.times_played,
                    "sessions": sessions_data
                }
            else:
                game_data = {
                    "name": game.name,
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

        context["self_sessions"] = GameSession.objects.prefetch_related('scores').filter(
            scores__user__id=self.kwargs["pk"]
        )

        if self.request.user.pk == self.kwargs['pk']:
            self_game_sessions = GameSession.objects.filter(scores__user__pk=self.kwargs["pk"]).\
                annotate(weekday=ExtractIsoWeekDay("created_at"))
        else:
            self_game_sessions = GameSession.objects.filter(
                scores__user__pk=self.kwargs["pk"],
                is_private=False
            ).annotate(weekday=ExtractIsoWeekDay("created_at"))

        context['sessions'] = self_game_sessions  # unclaimed yet

        context['most_active_day'] = get_the_most_played_day(self_game_sessions)

        context["frequency"] = get_player_calendar_with_week_day_name(self_game_sessions)

        return context


class FriendRequestListView(LoginRequiredMixin, FormMixin, ListView):
    """
    Also inherits from FormMixin for getting opportunity to render form for 'get' method in ListView CBV
    """
    model = users.models.FriendshipRequest
    template_name = 'requests_list.html'
    context_object_name = 'income_friendship_requests'
    #  FormMixin attrs:
    form_class = FriendshipRequestAcceptForm
    success_url = reverse_lazy('users:users_index')

    def get_queryset(self):
        """
        Override parent method to achieve possibility for splitting portion of friendship requests
        for 'is_staff' and regular users
        """
        if self.request.user.is_staff:
            return users.models.FriendshipRequest.objects.all()
        return users.models.FriendshipRequest.objects.filter(to_user=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        """
        Override parent method to achieve possibility for two kinds fo requests rendering in templates
        """
        context = super().get_context_data()
        context['filter_income'] = FriendshipRequestFilter(
            self.request.GET,
            queryset=users.models.FriendshipRequest.objects.filter(to_user=self.request.user)
        )
        context['filter_outcome'] = FriendshipRequestFilter(
            self.request.GET,
            queryset=users.models.FriendshipRequest.objects.filter(from_user=self.request.user)
        )
        return context


class FriendRequestProceedView(LoginRequiredMixin, UpdateView):
    model = users.models.FriendshipRequest
    template_name = 'request_proceed.html'
    pk_url_kwarg = 'request_pk'
    form_class = FriendshipRequestAcceptForm
    success_url = reverse_lazy('users:users_index')
    context_object_name = 'friendship_request'

    perm_denied_msg = 'Permission denied. Only owner can manage friends'
    friendship_accept_succeed_msg = "You accept '{friend}'s friendship request." \
                                    "'{friend}' now can view your profile page."
    friendship_decline_succeed_msg = "You decline '{friend}'s friendship request. " \
                                     "At now your access to '{friend}'s profile page is closed."
    friendship_withdraw_succeed_msg = "You've withdraw your friendship request to '{friend}'." \
                                      "At now '{friend}' don't have access to your profile page."

    def post(self, request, *args, **kwargs):
        """
        Override parent method for update FriendshipRequest instance (update it fields 'is_accepted'
        and 'is_rejected' depends of user choice about accept or decline friendship with request sender on rendered
        page). If request is accepted - creates new m2m field on CustomUser model for request.user - on
        field 'friendship' with sender of request
        """
        friendship_request = self.get_object()
        friendship_request_sender = friendship_request.from_user
        friendship_request_receiver = friendship_request.to_user

        #  Taking kwarg from url_dispatcher (<str:status>) from rendered form by FriendRequestListView
        if self.kwargs['status'] == 'acc':
            friendship_request.is_accepted, friendship_request.is_rejected = True, False
            friendship_request.save()
            users.models.CustomUser.objects.get(
                pk=friendship_request_sender.pk).friendship.add(request.user)
            messages.info(request, self.friendship_accept_succeed_msg.format(friend=friendship_request_sender))

        elif self.kwargs['status'] == 'dec':
            friendship_request.is_accepted, friendship_request.is_rejected = False, True
            friendship_request.save()
            users.models.CustomUser.objects.get(
                pk=request.user.pk).friendship.remove(friendship_request_sender)
            messages.info(request, self.friendship_decline_succeed_msg.format(friend=friendship_request_sender))

        elif self.kwargs['status'] == 'cancel':
            users.models.CustomUser.objects.get(pk=friendship_request_receiver.id).friendship.remove(request.user)
            friendship_request.delete()
            messages.info(request, self.friendship_withdraw_succeed_msg.format(friend=friendship_request_receiver))
            return HttpResponseRedirect(self.success_url)

        return super(FriendRequestProceedView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Set additional context variables:
         'from_user' - for template rendering correct message depends on "accept/decline" friendship request;
         'status' - for get correct path variable in form 'action' attribute (to send populated form to view)
        """
        context = super().get_context_data(**kwargs)
        from_user = self.object.from_user.username
        context['from_user'] = from_user
        context['friendship_request_answer'] = self.kwargs['status']
        return context


class UsersCreateView(CreateView):
    model = users.models.CustomUser
    form_class = CustomUserCreationForm
    template_name = 'user_register.html'

    def get_success_url(self):
        """
        Override parent method for 'autologin' purpose
        """
        login(self.request, user=self.object)
        return super().get_success_url()

    def form_valid(self, form):
        """
        Override parent method for reduce in a half size of avatar sent by users
        """
        if self.request.FILES.get('avatar'):
            new_user_bounded_form = form.save(commit=False)
            user_avatar = self.request.FILES['avatar']
            new_user_bounded_form.avatar = avatar_double_reducer(user_avatar)
            new_user_bounded_form.save()

        return super().form_valid(form)


class UsersUpdateView(LoginRequiredMixin, UpdateView):
    model = users.models.CustomUser
    form_class = CustomUserUpdateForm
    template_name = 'user_update.html'
    success_url = reverse_lazy('users:users_index')
    perm_denied_msg = 'Permission denied. Only owner can change profile'

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs['pk'] != request.user.pk:
            messages.error(request, self.perm_denied_msg)
            return HttpResponseRedirect(reverse_lazy('users:users_index'))
        return super().dispatch(request, *args, **kwargs)


class PasswordChangeCustomView(PasswordChangeView):
    """ Inherit built-in auth.views for add functional about user messaging"""

    def get_success_url(self):
        return reverse_lazy('users:users_detail', args=[self.request.user.id, ])

    def get_context_data(self, **kwargs):
        """
        Override for add messages() about successful password change on html
        """
        context = super().get_context_data()
        messages.info(self.request, "New password have been set")
        return context

# Realization with vanilla View through adding friend to CustomUser instance
# class FriendAddView(View):
#     form_class = CustomUserAddFriendForm
#     template_name = 'friend_add.html'
#     success_url = reverse_lazy('users:users_index')
#     perm_denied_msg = 'Permission denied. Only owner can manage friends'
#     friendship_succeed_msg  = "You've been succesfully added to '{friend}' friends." \
#                               " '{friend}' now can view your profile page"
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

# Realization with UpdateView through adding friend to CustomUser instance
# class FriendAddView(UpdateView):
#     model = users.models.CustomUser
#     template_name = 'friend_add.html'
#     form_class = CustomUserAddFriendForm
#     success_url = reverse_lazy('users:users_index')
#
#     perm_denied_msg = 'Permission denied. Only owner can manage friends'
#     friendship_succeed_msg  = "You've been succesfully added to '{friend}' friends.
#     '{friend}' now can view your profile page"
#     friendship_exist_msg  = "You're already in '{friend}' friend_list."
#
#     def post(self, request, *args, **kwargs):
#         form = CustomUserAddFriendForm(request.POST)
#         if form.is_valid():
#             user = request.user
#             friends = form.cleaned_data['friendship']
#             for friend in friends:
#                 if friend.pk == request.user.pk:
#                     continue
#                 messages.info(
#                     request,
#                     self.friendship_succeed_msg.format(friend=friend.username)
#                 ) if not friend.friendship.filter(pk=user.pk).exists() else messages.error(
#                     request,
#                     self.friendship_exist_msg.format(friend=friend.username)
#                 )
#                 friend.friendship.add(user)
#             return HttpResponseRedirect(self.success_url)
#         else:
#             messages.error(request, self.perm_denied_msg)
#
#             return HttpResponseRedirect(self.success_url)
#
#     def get(self, request, *args, **kwargs):
#         form = CustomUserAddFriendForm()
#         form.fields['friendship'].queryset = users.models.CustomUser.objects.exclude(
#             pk=self.request.user.pk
#         ).exclude(
#             friendship__pk=self.request.user.pk
#         )
#
#         return render(self.request, self.template_name, {'form': form})


class FriendAddView(CreateView):
    model = users.models.FriendshipRequest
    template_name = 'friend_add.html'
    form_class = CustomUserAddFriendForm
    success_url = reverse_lazy('users:users_index')

    perm_denied_msg = 'Permission denied. Only owner can manage friends'
    friendship_succeed_msg  = "You've been successfully added to '{friend}' friends. " \
                              "'{friend}' now can view your profile page. Friendship request to '{friend}' was sent. " \
                              "If '{friend}' will accept it - you'll be able to get access to his profile"
    friendship_exist_msg  = "You're already in '{friend}' friend_list."
    error_msg = "You can't be a friend with yourself"

    def dispatch(self, request, *args, **kwargs):
        """
        Protection against unauthorized access to the friendship management page
        """
        if self.kwargs['pk'] != request.user.pk:
            messages.error(request, self.perm_denied_msg)
            return HttpResponseRedirect(reverse_lazy('users:users_index'))
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Override parent method for possibility of proceed two workflows on db: creating a friendship request
        and add friend to CustomUser instance (to m2m field)
        """
        form = CustomUserAddFriendForm(request.POST)
        if form.is_valid():
            user = request.user
            friends = form.cleaned_data['friends_candidates']
            message = form.cleaned_data['message']
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
                friendship_request = users.models.FriendshipRequest(
                    from_user=request.user,
                    to_user=friend,
                    message=message,
                )
                friendship_request.save()
            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(request, self.perm_denied_msg)
            return HttpResponseRedirect(self.success_url)

    def get(self, request, *args, **kwargs):
        """
        Override to exclude 'self_request_user' from 'friendship' relation
        """
        form = CustomUserAddFriendForm()
        form.fields['friends_candidates'].queryset = form.fields['friends_candidates'].queryset.exclude(
            pk=request.user.pk
        ).exclude(
            friendship__pk=request.user.pk
        )

        return render(self.request, self.template_name, {'form': form})


class FriendRemoveView(FriendAddView):
    template_name = 'friend_remove.html'
    form_class = CustomUserRemoveFriendForm

    friendship_succeed_msg = "You've been successfully removed from '{friend}' friends. " \
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
                user.friendship.remove(friend)
            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(request, self.perm_denied_msg)
            return HttpResponseRedirect(self.success_url)

    def get(self, request, *args, **kwargs):
        form = CustomUserRemoveFriendForm()
        form.fields['friendship'].queryset = users.models.CustomUser.objects.get(
            pk=request.user.pk
        ).friendship.all()

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
def add_user_view_through_tg_bot(request):
    if request.method == 'POST':
        request_raw = request.body
        request_json = json.loads(request_raw)
        user_name = request_json['user']
        user_tuple = add_user_into_db_simple(user_name)
        is_new_user = user_tuple[1]
        user_pk = user_tuple[0].pk


    return HttpResponse(
        f"Ссылка на Ваш аккаунт: {site_root_url}{str(reverse_lazy('users:reg_cont', args=[user_pk]))}"
    ) if is_new_user else HttpResponse(
        f"Вы уже зарегистрированы. "
        f"Перейдите на сайт по ссылке {request.build_absolute_uri(reverse_lazy('users:users_detail', args=[user_pk]))}"
    )


class UserUpdateViewFromBot(UpdateView):
    """
    Class view without @login_required and permissions check for "registration-through-bot" process
    """
    model = users.models.CustomUser
    form_class = CustomUserCreationForm
    template_name = 'user_update_from_bot.html'

    def get_success_url(self):
        """
        Override classmethod to achieve redirect to profile page in built-in auth CBV
        """
        login(self.request, user=self.object)  # login "just updated from bot" user
        url = reverse_lazy('users:users_detail', args=[self.kwargs.get('pk'), ])
        return url


def feedback_view(request):
    """
    Takes claim from "contact_us" page and send email with text to admin
    :param request:
    :return:
    """
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            send_mail(
                form.cleaned_data['subject'],
                form.cleaned_data['content'],
                from_email=None,
                recipient_list=[os.getenv('DEFAULT_FROM_EMAIL'), ]
            )
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
