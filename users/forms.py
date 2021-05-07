from django.contrib.auth.forms import UserCreationForm, UserChangeForm
import django.forms

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


class CustomUserAddFriendForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        """Override to get opportunity to set css-class for ModelForm fields"""
        super().__init__(*args, **kwargs)
        self.fields['friendship'].widget.attrs.update({'class': 'special'})

    class Meta:
        model = CustomUser
        fields = [
            "friendship",
        ]
        labels = {
            "friendship": "Select the user to whom you want to be friends",
        }
        widgets = {'friendship': django.forms.CheckboxSelectMultiple()}