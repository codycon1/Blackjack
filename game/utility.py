import random
import json

from game import models

STATIC_URL = 'http://127.0.0.1:8000/static/cards/'

suitDict = {0: 'diamonds', 1: 'hearts', 2: 'spades', 3: 'clubs'}
rankDict = {1: 'ace', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
            10: '10', 11: 'jack', 12: 'queen', 13: 'king'}

def sp_dealer_draw(table):
    cards = models.Card.objects.filter(tableID=table, dealt=False)
    if not cards:
        return None
    card_choice = random.choice(cards)
    card_choice.dealt = True
    card_choice.dealer = True
    card_choice.save()
    jsonobj = {"dealercards": [{"url": (STATIC_URL+card_choice.img)}]}
    return json.dumps(jsonobj)

def sp_player_draw(table):
    cards = models.Card.objects.filter(tableID=table, dealt=False)
    if not cards:
        return None
    card_choice = random.choice(cards)
    card_choice.userID = table.singleplayerID
    card_choice.dealt = True
    card_choice.save()
    jsonobj = {"playercards": [{"url": (STATIC_URL+card_choice.img)}]}
    return json.dumps(jsonobj)

def sp_resync(table):
    playercards = models.Card.objects.filter(tableID=table, dealt=True) # TODO: ADD BOOLEAN KEY FOR DEALER AND FILTER FOR IT. RETURN DEALER CARDS TOO
    if playercards is not None:
        jsonobj = {"playercards": []}
        for card in playercards:
            jsonobj["playercards"].append({"url": (STATIC_URL+card.img)})
        return json.dumps(jsonobj)
    else:
        return None


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
    return table


# Generate a table and associated deck for either singleplayer or multiplayer
def generate_table(user=None):
    table_instance = models.Table(pot=0, singleplayerID=user)
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
        card.save()
