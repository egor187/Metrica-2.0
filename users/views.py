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
from django.db.models import Sum
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
from .forms import CustomUserCreationForm, CustomUserUpdateForm, FeedbackForm
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


class UsersListView(ListView):
    model = users.models.CustomUser
    template_name = 'users_index.html'
    context_object_name = 'users_list'


class UsersDetailView(LoginRequiredMixin, DetailView):
    model = users.models.CustomUser
    template_name = 'users_detail.html'

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

        context["last_five_games_played"] = Games.objects.prefetch_related('sessions').filter(
            sessions__scores__user__pk=self.kwargs['pk']
        ).distinct().annotate(player_score=Sum("sessions__scores__score"))

        context["self_sessions"] = GameSession.objects.prefetch_related('scores').filter(scores__user__id=self.kwargs["pk"])

        self_game_sessions = GameSession.objects.filter(scores__user__pk=self.kwargs["pk"]).\
            annotate(weekday=ExtractIsoWeekDay("created_at"))

        context['sessions'] = self_game_sessions

        context["frequency"] = get_player_calendar(self_game_sessions)

        return context


class UsersCreateView(CreateView):
    model = users.models.CustomUser
    form_class = CustomUserCreationForm
    template_name = 'user_register.html'


class UsersUpdateView(LoginRequiredMixin, UpdateView):
    model = users.models.CustomUser
    form_class = CustomUserUpdateForm
    template_name = 'user_update.html'
    success_url = reverse_lazy('users:users_index')
    perm_denied_msg = 'Permission denied. Only owner can change account'

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs['pk'] != request.user.pk:
            messages.error(request, self.perm_denied_msg)
            return HttpResponseRedirect(reverse_lazy('users:users_index'))
        return super().dispatch(request, *args, **kwargs)


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
    form_class = CustomUserUpdateForm
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

    return HttpResponse(f"{site_root_url}{str(reverse_lazy('users:reg_cont', args=[new_user_pk]))}"
    ) if new_user_pk else HttpResponse(
        f"Вы уже зарегистрированы. Можете перейти на сайт по этой ссылке {request.build_absolute_uri(reverse_lazy('index'))}"
    )


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