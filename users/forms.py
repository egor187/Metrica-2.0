from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser, FriendshipRequest
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

# Example how to override attributes for widgets in ModelForm (when field isn’t declared directly on the form)
# class CustomUserAddFriendForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         """Override to get opportunity to set css-class for ModelForm fields"""
#         super().__init__(*args, **kwargs)
#         self.fields['friendship'].widget.attrs.update({'class': 'special'})
#
#     class Meta:
#         model = CustomUser
#         fields = [
#             "friendship",
#         ]
#         labels = {
#             "friendship": "Select the user to whom you want to be friends",
#         }
#         widgets = {'friendship': django.forms.CheckboxSelectMultiple()}

class CustomUserAddFriendForm(forms.Form):
    """
    Refusal from ModelForm because in form need to reference to all CustomUsers (further filtered in view)
    and 'message' field in FriendshipRequest instance (two different models)
    """
    friends_candidates = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'special'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'special'}))


class CustomUserRemoveFriendForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "friendship",
        ]
        labels = {
            "friendship": "Select the user('s) from whom you want to leave friends",
        }
        widgets = {'friendship': forms.CheckboxSelectMultiple(attrs={'class': 'special'})}


class FriendshipRequestAcceptForm(forms.ModelForm):
    class Meta:
        """'id' field of a models (type: AutoField) hasn't representation in forms.
        No corresponding field type of a form. That's why it's was chosen to get form with only
        'button' to send form with populated choice in code
        """
        model = FriendshipRequest
        fields = [
            'id',
        ]
