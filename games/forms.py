from django import forms

from games.models import Games


class GameCreationForm(forms.ModelForm):
    class Meta:
        model = Games
        fields = [
            'name',
            'cover_art',
        ]
