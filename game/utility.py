import math
import random
import json

from game import models
from collections import Counter

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

    # TODO: this is a highly repeated code snippet
    player_tracker = models.PlayerTracker.objects.filter(playerID=user).first()
    if not player_tracker:
        player_tracker = models.PlayerTracker(playerID=user, tableID=table)

    try:
        action_primary = data['primary']['action']
        action_split = data['split']['action']
    except KeyError:
        # Screw it, just ignore a key error it's easier this way
        pass

    if action_primary == 'reset':
        print("Resetting table")
        sp_reset_table(table, user)
    if action_primary.split(' ')[0] == 'bet':
        bet_amount = int(action_primary.split(' ')[1])
        bet_instance = models.Bet.objects.filter(playerID=user, tableID=table).first()
        if not bet_instance:
            bet_instance = models.Bet(playerID=user, tableID=table)
        bet_instance.amount += bet_amount
        bet_instance.save()
        user.balance -= bet_amount
        player_tracker.status = STATUS_BET_PLACED
        player_tracker.save()
        user.save()

    if action_primary == 'Hit':
        sp_player_hit(table, user)

    if action_primary == 'stay':
        pass

    if action_primary == 'Split':
        player_cards = models.Card.objects.filter(playerID=player_tracker.playerID, tableID=player_tracker.tableID)
        player_card_vals = player_cards.values_list('rank')
        counter = Counter(player_card_vals)
        duplicates = [i for i, x in counter.items() if x > 1]
        split_card = models.Card.objects.filter(playerID=player_tracker.playerID, rank=duplicates[0][0]).first()
        split_card.split = True
        split_card.save()
        player_tracker.split_status = 1
        player_tracker.save()

    if action_primary == 'double down':
        pass

    return sp_sync(table, user)


def sp_sync(table, user, init=False):
    player_tracker = models.PlayerTracker.objects.filter(playerID=user).first()
    if not player_tracker:
        player_tracker = models.PlayerTracker(playerID=user, tableID=table)
        player_tracker.save()

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

    primary_action, split_action = sp_process_turn(player_tracker)

    if bets:
        if user_bet := bets.filter(playerID=user).first():
            json_obj['primary']['bet'] = user_bet.amount
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
                json_obj['dealer_cards'].append({"url": (STATIC_URL + 'back.png')})
            else:
                json_obj['dealer_cards'].append({"url": (STATIC_URL + card.img)})

    json_obj['primary']['signal'].extend(primary_action)
    if split_action is not None:
        json_obj['split']['signal'].extend(split_action)

    player_tracker.json_cache = json_obj
    player_tracker.save()

    json_string = json.dumps(json_obj)
    print(json_string)
    return json_string


def sp_process_turn(player_tracker):
    split_signal = None
    primary_signal = None

    if player_tracker.status is not None:
        primary_signal = []
        if player_tracker.status == STATUS_INIT:
            primary_signal.append('Bet')
        elif player_tracker.status == STATUS_BET_PLACED:
            # Dealer's initial cards are drawn
            deck = models.Card.objects.filter(dealt=False, tableID=player_tracker.tableID)
            # TODO: this is brute force, make it elegant by looping twice
            dealer_flipped_card = random.choice(deck)
            dealer_flipped_card.hidden = True
            dealer_flipped_card.dealt = True
            dealer_flipped_card.dealer = True
            dealer_flipped_card.save()
            deck = deck.exclude(pk=dealer_flipped_card.pk)

            dealer_card_1 = random.choice(deck)
            dealer_card_1.dealt = True
            dealer_card_1.dealer = True
            dealer_card_1.save()
            deck = deck.exclude(pk=dealer_card_1.pk)

            player_tracker.status = STATUS_TURN
            player_tracker.save()

            # Player's initial cards are drawn
            # TODO: this is brute force, make it elegant
            player_init_card = random.choice(deck)
            player_init_card.playerID = player_tracker.playerID
            player_init_card.dealt = True
            player_init_card.save()
            deck = deck.exclude(pk=player_init_card.pk)

            player_card_1 = random.choice(deck)
            player_card_1.playerID = player_tracker.playerID
            player_card_1.dealt = True
            player_card_1.save()

            primary_signal.append('Hit')
            primary_signal.append('Stay')

        elif player_tracker.status == STATUS_TURN:
            primary_signal.append('Hit')
            primary_signal.append('Stay')

            # Check for split condition
            if player_tracker.split_status == 0:
                player_cards = models.Card.objects.filter(playerID=player_tracker.playerID, tableID=player_tracker.tableID)
                player_card_vals = player_cards.values_list('rank')
                unique_player_card_vals = set(player_card_vals)
                if len(player_card_vals) > len(unique_player_card_vals):
                    primary_signal.append('Split')

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


def sp_player_hit(table, user):
    cards = models.Card.objects.filter(tableID=table, dealt=False)
    if not cards:
        return None
    card_choice = random.choice(cards)
    card_choice.dealt = True
    card_choice.playerID = user
    card_choice.save()


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


def sp_reset_table(table, user):
    player_tracker = models.PlayerTracker.objects.filter(playerID=user, tableID=table).first()
    table.delete()
    table = generate_table(user)
    if player_tracker:
        player_tracker.tableID = table
        player_tracker.status = STATUS_INIT
        player_tracker.split_status = None
        player_tracker.save()

    bet_instance = models.Bet.objects.filter(playerID=user, tableID=table)
    if bet_instance:
        bet_instance.delete()

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
    if deck := models.Card.objects.filter(tableID=table):
        reset_deck(table)
    else:

        for i in range(4):
            for j in range(1, 14):
                models.Card.objects.create(suit=i, rank=j, img=(rankDict[j] + '_of_' + suitDict[i] + '.png'),
                                           tableID=table, )


def reset_deck(table):
    deck = models.Card.objects.filter(tableID=table)
    for card in deck:
        card.dealt = False
        card.dealer = False
        card.playerID = None
        hidden = False
        split = False
        card.save()
