from users.models import CustomUser
from django.shortcuts import render


def index(request):
    return render(request, 'metrica_index.html')
