import math
import random
import json

from game import models

STATIC_URL = 'http://127.0.0.1:8000/static/cards/'

suitDict = {0: 'diamonds', 1: 'hearts', 2: 'spades', 3: 'clubs'}
rankDict = {1: 'ace', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
            10: '10', 11: 'jack', 12: 'queen', 13: 'king'}

STATUS_INIT = 0
STATUS_BET_PLACED = 1
STATUS_TURN = 2
STATUS_SPLIT = 3


def sp_process_input_json(data, user, table):
    action_primary = None
    action_split = None

    try:
        action_primary = data['primary']['action']
        action_split = data['split']['action']
    except KeyError:
        # Screw it, just ignore a key error it's easier this way
        pass

    if action_primary == 'reset':
        print("Resetting table")
        sp_reset_table(table)


def sp_sync(table, user):
    player_tracker = models.PlayerTracker.objects.filter(playerID=user).first()
    if not player_tracker:
        player_tracker = models.PlayerTracker(playerID=user, tableID=table)
    if cache := player_tracker.json_cache:
        json_string = json.dumps(cache)
        return json_string

    cards = models.Card.objects.filter(tableID=table, dealt=True)
    bets = models.Bet.objects.filter(tableID=table)

    json_obj = {
        'balance': user.balance,
        'dealer_cards': [],
        'primary': {
            'bet': [],
            'cards': [],
            'signal': [],
        },
        'split': {
            'bet': [],
            'cards': [],
            'signal': [],
        },
    }

    if bets:
        if user_bet := bets.filter(playerID=user).amount:
            json_obj['primary']['bet'] = user_bet
        if user_bet.amount_split:
            json_obj['split']['bet'] = user_bet.amount_split
    if playercards := cards.filter(playerID=user):
        for i, card in enumerate(playercards):
            if not card.split:
                json_obj['primary']['cards'].append({"url": (STATIC_URL + card.img)})
            else:
                json_obj['split']['cards'].append({"url": (STATIC_URL + card.img)})
    if dealercards := cards.filter(dealer=True):
        for i, card in enumerate(dealercards):
            if card.hidden:
                json_obj['dealercards'].append({"url": (STATIC_URL + 'back.png')})
            else:
                json_obj['dealercards'].append({"url": (STATIC_URL + card.img)})

    primary_action, split_action = sp_get_ready_signal(player_tracker)
    json_obj['primary']['signal'].extend(primary_action)
    if split_action is not None:
        json_obj['split']['signal'].extend(split_action)

    player_tracker.json_cache = json_obj
    player_tracker.save()

    json_string = json.dumps(json_obj)
    print(json_string)
    return json_string


def sp_get_ready_signal(player_tracker):
    primary_signal = []
    split_signal = None
    if player_tracker.status == STATUS_INIT:
        primary_signal.append('Bet')
    elif player_tracker.status == STATUS_BET_PLACED:
        primary_signal.append('Hit')
        primary_signal.append('Stay')

    if player_tracker.split_status is not None:
        split_signal = []
        if player_tracker.split_status == STATUS_INIT:
            split_signal.append('Bet')
        elif player_tracker.status == STATUS_BET_PLACED:
            split_signal.append('Hit')
            split_signal.append('Stay')
    else:
        player_cards = models.Card.objects.filter(playerID=player_tracker.playerID, tableID=player_tracker.tableID)
        duplicate_ranks = player_cards.values('rank')
        # TODO: finish checking for duplicate and add split option if there are any

    return primary_signal, split_signal


def sp_game_over(table, user, result, win21=False):
    if result:  # Win condition
        if win21:
            user.balance += int(table.pot / 2)
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
    table = models.Table.objects.filter(players__in=[user]).first()
    if table is None:
        table = generate_table(user)
    return table


def sp_reset_table(table):
    if table is None:
        table = generate_table(user)
    else:
        reset_deck(table)
        table.status = 0
        table.pot = 0
        table.save()
    return table


# Generate a table and associated deck for either singleplayer or multiplayer
def generate_table(user):
    table_instance = models.Table(status=0)
    table_instance.save()
    table_instance.players.add(user)
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
