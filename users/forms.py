from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser
from django import forms
from .models import Claim

from django_summernote.widgets import SummernoteWidget


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
        ]


class CustomUserUpdateForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
        ]


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = [
            'topic',
            'claim'
        ]
        widgets = {
            'claim': SummernoteWidget()
        }