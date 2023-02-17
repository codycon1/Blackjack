from django.shortcuts import render
from game import models

suitDict = {0: 'diamonds', 1: 'hearts', 2: 'spades', 3: 'clubs'}
rankDict = {1: 'ace', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
            10: '10', 11: 'jack', 12: 'queen', 13: 'king'}


def home(request):
    # generate_table()
    return render(request, 'home.html')


def play(request):
    return render(request, 'gametype.html')


def singleplayer(request):
    # TODO: Game logic and socket connections
    return render(request, 'singleplayer.html')


def generate_table():
    table_instance = models.Table(pot=0)
    table_instance.save()
    generate_deck(table_instance)


def generate_deck(table):
    for i in range(4):
        for j in range(1, 14):
            models.Card.objects.create(suit=i, rank=j, img=(rankDict[j] + '_of_' + suitDict[i] + '.png'),
                                       tableID=table, )
