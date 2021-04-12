from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser
from django import forms


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


class FeedbackForm(forms.Form):
    subject = forms.ChoiceField()
    content = forms.CharField(label="Текст обращения", widget=forms.Textarea)
    email = forms.EmailField()
