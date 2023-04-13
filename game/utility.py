import math
import random
import json

from game import models

STATIC_URL = 'http://127.0.0.1:8000/static/cards/'

suitDict = {0: 'diamonds', 1: 'hearts', 2: 'spades', 3: 'clubs'}
rankDict = {1: 'ace', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
            10: '10', 11: 'jack', 12: 'queen', 13: 'king'}

def split(user):
    pass

def sp_game_over(table, user, result, win21=False):
    if result:  # Win condition
        if win21:
            user.balance += int(table.pot/2)
        user.balance += table.pot
        table.status = 3
        table.save()
        user.save()
    else:  # Lose condition
        table.status = 4
        table.save()
    user.save()


def sp_check(table, user, dealer=False):  # Signals a game over condition
    playercards = models.Card.objects.filter(tableID=table, dealt=True, userID=user)
    dealercards = models.Card.objects.filter(tableID=table, dealt=True, dealer=True)

    playertotal = 0
    dealertotal = 0
    for card in playercards:
        if card.rank == 1 and (playertotal + 11) < 21:
            playertotal += 11
        else:
            playertotal += min(card.rank, 10)

    if playertotal == 21:
        return True
    if playertotal > 21:
        return False
    if dealer:
        for card in dealercards:
            if card.rank == 1 and (dealertotal + 11) < 21:
                dealertotal += 11
            else:
                dealertotal += min(card.rank, 10)
        while dealertotal <= 16:
            dealer_card = sp_dealer_hit(table)
            if dealer_card.rank == 1 and (dealertotal + 11) < 21:
                dealertotal += 11
            else:
                dealertotal += min(dealer_card.rank, 10)
        if dealertotal > 21:
            return True
    if dealer:
        return dealertotal > playertotal
    else:
        return None


def sp_place_bet(table, player, amt):
    table.pot += amt
    player.balance -= amt
    table.status = 1
    table.save()
    player.save()


def sp_dealer_hit(table):
    cards = models.Card.objects.filter(tableID=table, dealt=False)
    if not cards:
        return None
    card_choice = random.choice(cards)
    card_choice.dealt = True
    card_choice.dealer = True
    card_choice.save()
    return card_choice


def sp_player_hit(table):
    cards = models.Card.objects.filter(tableID=table, dealt=False)
    if not cards:
        return None
    card_choice = random.choice(cards)
    card_choice.userID = table.singleplayerID
    card_choice.dealt = True
    card_choice.save()
    jsonobj = {"playercards": [{"url": (STATIC_URL + card_choice.img)}]}


def sp_resync(table, user, dealer_flip=False):
    playercards = models.Card.objects.filter(tableID=table, dealt=True, userID=user)
    dealercards = models.Card.objects.filter(tableID=table, dealt=True, dealer=True)
    jsonobj = {
        'balance': user.balance,
        'pot': table.pot,
    }
    if playercards is not None:
        jsonobj['playercards'] = []
        for card in playercards:
            jsonobj["playercards"].append({"url": (STATIC_URL + card.img)})

    if dealercards is not None:
        jsonobj['dealercards'] = []
        for i, card in enumerate(dealercards):
            if i == 0 and not dealer_flip:
                jsonobj['dealercards'].append({"url": (STATIC_URL + 'back.png')})
            else:
                jsonobj["dealercards"].append({"url": (STATIC_URL + card.img)})

    if table.status == 0:
        jsonobj['readysignal'] = ['Bet']
    elif table.status == 1:
        jsonobj['readysignal'] = ['Start']
    elif table.status == 2:
        jsonobj['readysignal'] = ['Hit', 'Stay']
    elif table.status == 3:
        jsonobj['result'] = True
        jsonobj['readysignal'] = ['Again']
    elif table.status == 4:
        jsonobj['result'] = False
        jsonobj['readysignal'] = ['Again']
    jsons = json.dumps(jsonobj)
    print(jsons)
    return jsons


# Create a single player table if it doesn't exist, else return the existing table
def sp_prep_table(user):
    table = models.Table.objects.filter(singleplayerID=user).first()
    if table is None:
        table = generate_table(user)
    return table


def sp_reset_table(user):
    table = models.Table.objects.filter(singleplayerID=user).first()
    if table is None:
        table = generate_table(user)
    else:
        reset_deck(table)
        table.status = 0
        table.pot = 0
        table.save()
    return table


# Generate a table and associated deck for either singleplayer or multiplayer
def generate_table(user=None):
    table_instance = models.Table(pot=0, singleplayerID=user, status=0)
    table_instance.save()
    generate_deck(table_instance)
    return table_instance


# Generate a deck for a table
def generate_deck(table):
    for i in range(4):
        for j in range(1, 14):
            models.Card.objects.create(suit=i, rank=j, img=(rankDict[j] + '_of_' + suitDict[i] + '.png'),
                                       tableID=table, )


def reset_deck(table):
    deck = models.Card.objects.filter(tableID=table)
    for card in deck:
        card.dealt = False
        card.dealer = False
        card.userID = None
        card.save()
