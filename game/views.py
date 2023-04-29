from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from game import models


def home(request):
    # generate_table()
    return render(request, 'home.html')


@login_required
def play(request):
    return render(request, 'gametype.html')


@login_required
def singleplayer(request):
    return render(request, 'singleplayer.html')


@login_required
def multiplayer(request):
    return render(request, 'multiplayer.html')
