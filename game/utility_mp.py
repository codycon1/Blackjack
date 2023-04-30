import math
import random
import json

from django.db.models import Count

from game import models
import users.models
from collections import Counter

STATIC_URL = 'http://127.0.0.1:8000/static/cards/'

suitDict = {0: 'diamonds', 1: 'hearts', 2: 'spades', 3: 'clubs'}
rankDict = {1: 'ace', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
            10: '10', 11: 'jack', 12: 'queen', 13: 'king'}

TABLE_STATUS_INIT = 0
TABLE_STATUS_IN_PROGRESS = 1
TABLE_STATUS_END = 2

STATUS_INIT = 0
STATUS_BET_PLACED = 1
STATUS_TURN = 2
STATUS_SPLIT = 3

STATUS_STAY = 8
STATUS_DOUBLE = 9

END_CONDITION_BUST = 10
END_CONDITION_WIN = 11
END_CONDITION_21 = 12
END_CONDITION_DEALER_WIN = 13

MP_TABLE_INIT = 0


# Syncs player names and ready actions to interact directly with the table
def mp_group_sync(table):
    table_sync_json = {
        'players': list(table.players.all().values_list('username', flat=True)),
        'mp_ready_action': None
    }
    player_number = table.players.all().count()
    ready_count = table.mp_status
    if ready_count < player_number:
        if 1 < player_number <= 4:
            table_sync_json['mp_ready_action'] = 'Ready'

    print(json.dumps(table_sync_json))
    return table_sync_json


def mp_player_disconnect(table, user):
    models.Bet.objects.filter(playerID=user, tableID=table).delete()
    table.players.remove(user)
    table.save()
    if table.players.count() == 0:
        table.delete()
        return None
    return mp_group_sync(table)


def mp_process_input_json(data, user, table):
    action_primary = None
    action_split = None

    player_number = table.players.all().count()

    # TODO: this is a highly repeated code snippet
    player_tracker = models.PlayerTracker.objects.filter(playerID=user).first()
    if not player_tracker:
        player_tracker = models.PlayerTracker(playerID=user, tableID=table)

    try:
        action_primary = data['primary']['action']
    except KeyError:
        # Screw it, just ignore a key error it's easier this way
        pass
    try:
        action_split = data['split']['action']
    except KeyError:
        pass

    if action_primary is not None:
        if action_primary == 'Ready':
            table.mp_status += 1
            table.save()
            if table.mp_status != player_number:
                return None

        if action_primary == 'reset':
            print("Resetting table")
            table = mp_reset_table(table, user)
        if action_primary == 'New':
            print("New Game")
            table = mp_reset_table(table, user)
            player_tracker = models.PlayerTracker.objects.filter(playerID=user).first()
            if not player_tracker:
                player_tracker = models.PlayerTracker(playerID=user, tableID=table)
        if action_primary.split(' ')[0] == 'bet':
            bet_amount = int(action_primary.split(' ')[1])
            bet_instance = models.Bet.objects.filter(playerID=user, tableID=table).first()
            if not bet_instance:
                bet_instance = models.Bet(playerID=user, tableID=table)
            bet_instance.amount += bet_amount
            table.save()
            bet_instance.save()
            user.balance -= bet_amount
            player_tracker.status = STATUS_BET_PLACED
            player_tracker.save()
            user.save()

        if action_primary == 'Hit':
            mp_player_hit(table, user)

        if action_primary == 'Stay':
            player_tracker.status = STATUS_STAY
            player_tracker.save()

        if action_primary == 'Split':
            player_cards = models.Card.objects.filter(playerID=player_tracker.playerID, tableID=player_tracker.tableID)
            player_card_vals = player_cards.values_list('rank')
            counter = Counter(player_card_vals)
            duplicates = [i for i, x in counter.items() if x > 1]
            split_card = models.Card.objects.filter(playerID=player_tracker.playerID, rank=duplicates[0][0]).first()
            split_card.split = True
            split_card.save()
            player_tracker.split_status = STATUS_INIT
            player_tracker.save()

        if action_primary == 'Double':
            player_tracker.status = STATUS_DOUBLE
            player_tracker.save()

    if action_split is not None:
        if action_split.split(' ')[0] == 'bet':
            print('split betting')
            bet_amount = int(action_split.split(' ')[1])
            bet_instance = models.Bet.objects.filter(playerID=user, tableID=table).first()
            bet_instance.amount_split += bet_amount
            bet_instance.save()
            user.balance -= bet_amount
            player_tracker.split_status = STATUS_BET_PLACED
            player_tracker.save()
            user.save()

        if action_split == 'Double':
            player_tracker.split_status = STATUS_DOUBLE
            player_tracker.save()

        if action_split == 'Hit':
            mp_player_hit(table, user, split=True)

        if action_split == 'Stay':
            player_tracker.split_status = STATUS_STAY
            player_tracker.save()

    return mp_sync(table, user)


def mp_sync(table, user, init=False):
    player_number = table.players.all().count()
    ready_count = table.mp_status
    if ready_count < player_number:
        return None

    player_tracker = models.PlayerTracker.objects.filter(playerID=user, tableID=table).first()
    if not player_tracker:
        player_tracker = models.PlayerTracker(playerID=user, tableID=table)
        player_tracker.save()

    cards = models.Card.objects.filter(tableID=table)
    primary_action, split_action = mp_process_turn(player_tracker, cards)
    cards = models.Card.objects.filter(tableID=table)  # Gotta query this a second time unfortunately
    bets = models.Bet.objects.filter(tableID=table)
    user = users.models.BlackjackUser.objects.filter(pk=user.pk).first()  # Refresh this too

    json_obj = {
        'balance': user.balance,
        'players': [],
        'dealer_cards': [],
        'primary': {
            'bet': None,
            'cards': [],
            'signal': [],
            'end_condition': None,
        },
        'split': {
            'bet': None,
            'cards': [],
            'signal': [],
            'end_condition': None,
        },
    }

    if bets:
        if user_bet := bets.filter(playerID=user).first():
            json_obj['primary']['bet'] = user_bet.amount
        if user_bet.amount_split:
            json_obj['split']['bet'] = user_bet.amount_split
    if playercards := cards.filter(playerID=user, dealt=True):
        for i, card in enumerate(playercards):
            if card.split:
                json_obj['split']['cards'].append({"url": (STATIC_URL + card.img)})
            else:
                json_obj['primary']['cards'].append({"url": (STATIC_URL + card.img)})
    if dealercards := cards.filter(dealer=True, dealt=True):
        for i, card in enumerate(dealercards):
            if card.hidden:
                json_obj['dealer_cards'].append({"url": (STATIC_URL + 'back.png')})
            else:
                json_obj['dealer_cards'].append({"url": (STATIC_URL + card.img)})

    if primary_action is not None:
        json_obj['primary']['signal'].extend(primary_action)
    if split_action is not None:
        json_obj['split']['signal'].extend(split_action)

    if player_tracker.status == END_CONDITION_BUST:
        json_obj['primary']['end_condition'] = 'Bust'
    elif player_tracker.status == END_CONDITION_WIN:
        json_obj['primary']['end_condition'] = 'Win'
    elif player_tracker.status == END_CONDITION_21:
        json_obj['primary']['end_condition'] = 'Win with 21'
    elif player_tracker.status == END_CONDITION_DEALER_WIN:
        json_obj['primary']['end_condition'] = 'You lose'

    if player_tracker.split_status is not None:
        if player_tracker.split_status == END_CONDITION_BUST:
            json_obj['split']['end_condition'] = 'Bust'
        elif player_tracker.split_status == END_CONDITION_WIN:
            json_obj['split']['end_condition'] = 'Win'
        elif player_tracker.split_status == END_CONDITION_21:
            json_obj['split']['end_condition'] = 'Win with 21'
        elif player_tracker.split_status == END_CONDITION_DEALER_WIN:
            json_obj['split']['end_condition'] = 'You lose'

    player_tracker.json_cache = json_obj
    player_tracker.save()

    json_string = json.dumps(json_obj)
    print("mp_sync output: " + json_string)
    return json_string


def mp_process_turn(player_tracker, cards):
    split_signal = None
    primary_signal = None

    print("Status: " + str(player_tracker.status) + " Split status: " + str(player_tracker.split_status))

    player_cards = cards.filter(playerID=player_tracker.playerID)

    if player_tracker.status is not None:
        primary_signal = []
        if player_tracker.status == STATUS_INIT:
            primary_signal.append('Bet')
        elif player_tracker.status == STATUS_BET_PLACED:

            # TODO: BLOCK OUT UNIT TEST
            # START
            deck = cards.filter(dealt=False)
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

            player_init_card = deck.filter(rank=2).first()
            player_init_card.playerID = player_tracker.playerID
            player_init_card.dealt = True
            player_init_card.save()
            deck = deck.exclude(pk=player_init_card.pk)
            player_init_card = deck.filter(rank=2).first()
            player_init_card.playerID = player_tracker.playerID
            player_init_card.dealt = True
            player_init_card.save()

            player_tracker.status = STATUS_TURN
            player_tracker.save()
            # END
            #
            # # Dealer's initial cards are drawn
            # deck = cards.filter(dealt=False)
            # # TODO: this is brute force, make it elegant by looping twice
            # dealer_flipped_card = random.choice(deck)
            # dealer_flipped_card.hidden = True
            # dealer_flipped_card.dealt = True
            # dealer_flipped_card.dealer = True
            # dealer_flipped_card.save()
            # deck = deck.exclude(pk=dealer_flipped_card.pk)
            #
            # dealer_card_1 = random.choice(deck)
            # dealer_card_1.dealt = True
            # dealer_card_1.dealer = True
            # dealer_card_1.save()
            # deck = deck.exclude(pk=dealer_card_1.pk)
            #
            # player_tracker.status = STATUS_TURN
            # player_tracker.save()
            #
            # # Player's initial cards are drawn
            # # TODO: this is brute force, make it elegant
            # player_init_card = random.choice(deck)
            # player_init_card.playerID = player_tracker.playerID
            # player_init_card.dealt = True
            # player_init_card.save()
            # deck = deck.exclude(pk=player_init_card.pk)
            #
            # player_card_1 = random.choice(deck)
            # player_card_1.playerID = player_tracker.playerID
            # player_card_1.dealt = True
            # player_card_1.save()

            primary_signal.append('Hit')
            primary_signal.append('Stay')

            bet_amt = models.Bet.objects.filter(playerID=player_tracker.playerID).first().amount
            if bet_amt <= player_tracker.playerID.balance:
                primary_signal.append('Double')

        elif player_tracker.status == STATUS_TURN:
            bust = mp_check_bust(player_cards.filter(split=False))

            if not bust:
                primary_signal.append('Hit')
                primary_signal.append('Stay')
            else:
                player_tracker.status = END_CONDITION_BUST
                player_tracker.save()
                # Game over processing here

        elif player_tracker.status == STATUS_DOUBLE:
            bet_obj = models.Bet.objects.filter(playerID=player_tracker.playerID).first()
            player_obj = player_tracker.playerID
            player_obj.balance = player_obj.balance - bet_obj.amount
            player_obj.save()
            bet_obj.amount = bet_obj.amount * 2
            bet_obj.save()

            # Check for split condition
        if player_tracker.split_status is None:
            player_cards = models.Card.objects.filter(playerID=player_tracker.playerID,
                                                      tableID=player_tracker.tableID)
            player_card_vals = player_cards.values_list('rank')
            unique_player_card_vals = set(player_card_vals)
            if (len(player_card_vals) > len(unique_player_card_vals)) and (player_tracker.status < STATUS_STAY):
                primary_signal.append('Split')

    if player_tracker.split_status is not None:
        split_signal = []
        if player_tracker.split_status == STATUS_INIT:
            split_signal.append('Bet')
        elif player_tracker.split_status == STATUS_BET_PLACED:
            deck = models.Card.objects.filter(dealt=False, tableID=player_tracker.tableID)
            card1 = random.choice(deck)
            card1.dealt = True
            card1.playerID = player_tracker.playerID
            card1.split = True
            card1.save()
            deck = deck.exclude(pk=card1.pk)
            card2 = random.choice(deck)
            card2.dealt = True
            card2.playerID = player_tracker.playerID
            card2.split = True
            card2.save()
            player_tracker.split_status = STATUS_TURN
            player_tracker.save()

            bet_amt = models.Bet.objects.filter(playerID=player_tracker.playerID).first().amount
            if bet_amt <= player_tracker.playerID.balance:
                split_signal.append('Double')
            split_signal.append('Hit')
            split_signal.append('Stay')
        elif player_tracker.split_status == STATUS_TURN:
            bust = mp_check_bust(player_cards.filter(split=True))

            if not bust:
                split_signal.append('Hit')
                split_signal.append('Stay')
            else:
                player_tracker.split_status = END_CONDITION_BUST
                player_tracker.save()
        elif player_tracker.split_status == STATUS_DOUBLE:
            bet_obj = models.Bet.objects.filter(playerID=player_tracker.playerID).first()
            player_obj = player_tracker.playerID
            player_obj.balance = player_obj.balance - bet_obj.amount_split
            player_obj.save()
            bet_obj.amount_split = bet_obj.amount_split * 2
            bet_obj.save()

    if player_tracker.status >= STATUS_STAY and player_tracker.split_status is None:
        mp_dealer_turn(player_tracker.tableID, cards)
        final_cards = models.Card.objects.filter(tableID=player_tracker.tableID)
        dealer_cards = final_cards.filter(dealer=True)
        player_cards = final_cards.filter(playerID=player_tracker.playerID)
        player_tracker.status = mp_final_check(player_cards, dealer_cards)
        player_tracker.save()
    if player_tracker.split_status is not None:
        if player_tracker.status >= STATUS_STAY and player_tracker.split_status >= STATUS_STAY:
            mp_dealer_turn(player_tracker.tableID, cards)
            final_cards = models.Card.objects.filter(tableID=player_tracker.tableID)
            dealer_cards = final_cards.filter(dealer=True)
            player_cards = final_cards.filter(playerID=player_tracker.playerID)
            player_cards_split = player_cards.filter(split=True)

            player_tracker.status = mp_final_check(player_cards, dealer_cards)
            player_tracker.split_status = mp_final_check(player_cards_split, dealer_cards)
            player_tracker.save()

    if player_tracker.status >= END_CONDITION_BUST and player_tracker.split_status is None:
        primary_signal.append('New')
        mp_payout(player_tracker)
    elif player_tracker.status >= END_CONDITION_BUST and player_tracker.split_status >= END_CONDITION_BUST:
        primary_signal.append('New')
        mp_payout(player_tracker)

    print(primary_signal, split_signal)
    return primary_signal, split_signal


def mp_payout(player_tracker):
    bet_obj = models.Bet.objects.filter(playerID=player_tracker.playerID).first()
    player_obj = users.models.BlackjackUser.objects.filter(pk=player_tracker.playerID.pk).first()
    if player_tracker.status == END_CONDITION_BUST:
        player_obj.balance -= bet_obj.amount
    elif player_tracker.status == END_CONDITION_WIN:
        player_obj.balance += bet_obj.amount
    elif player_tracker.status == END_CONDITION_21:
        player_obj.balance += (bet_obj.amount * 1.5)

    if player_tracker.split_status is not None:
        if player_tracker.split_status == END_CONDITION_BUST:
            player_obj.balance -= bet_obj.amount
        elif player_tracker.split_status == END_CONDITION_WIN:
            player_obj.balance += bet_obj.amount
        elif player_tracker.split_status == END_CONDITION_21:
            player_obj.balance += (bet_obj.amount * 1.5)

        bet_obj.amount_split = 0

    bet_obj.amount = 0
    bet_obj.save()
    player_obj.save()

    if player_tracker.split_status:
        if player_tracker.split_status == END_CONDITION_BUST:
            player_obj.balance -= bet_obj.amount
        elif player_tracker.split_status == END_CONDITION_WIN:
            player_obj.balance += bet_obj.amount
        elif player_tracker.split_status == END_CONDITION_21:
            player_obj.balance += (bet_obj.amount * 1.5)

        bet_obj.amount = 0
        bet_obj.save()
        player_obj.save()


# Process the dealer's turn. Does not evaluate conditions.
def mp_dealer_turn(table, cards):
    dealercards = cards.filter(dealer=True)
    for card in dealercards:
        print("Card: " + str(card.rank) + "Flipped: " + str(card.hidden))
    flipped_card = dealercards.filter(hidden=True).first()
    if flipped_card is not None:
        flipped_card.hidden = False
        flipped_card.save()
    dealertotal = 0
    for card in dealercards:
        if card.rank == 1 and (dealertotal + 11) < 21:
            dealertotal += 11
        else:
            dealertotal += min(card.rank, 10)
    while dealertotal <= 16:
        dealer_card = mp_dealer_hit(table)
        if dealer_card.rank == 1 and (dealertotal + 11) < 21:
            dealertotal += 11
        else:
            dealertotal += min(dealer_card.rank, 10)


# Checks when there's a stay condition
# Returns result, does not process status or bets
# Does not call dealer turn
def mp_final_check(player_cards, dealer_cards):
    playertotal = 0
    dealertotal = 0

    for card in player_cards:
        if card.rank == 1 and (playertotal + 11) < 12:
            playertotal += 11
        else:
            playertotal += min(card.rank, 10)

    for card in dealer_cards:
        if card.rank == 1 and (dealertotal + 11) < 12:
            dealertotal += 11
        else:
            dealertotal += min(card.rank, 10)

    if playertotal > 21:
        return END_CONDITION_BUST
    elif playertotal == 21:
        return END_CONDITION_21
    elif dealertotal > 21:
        return END_CONDITION_WIN
    return END_CONDITION_DEALER_WIN


# Returns bust condition based on player's hand
# Return true if bust
def mp_check_bust(player_cards):  # Signals a game over condition. Checks predefined subset of cards
    playertotal = 0

    for card in player_cards:
        if card.rank == 1 and (playertotal + 11) < 21:
            playertotal += 11
        else:
            playertotal += min(card.rank, 10)

    if playertotal == 21:
        return END_CONDITION_21
    if playertotal > 21:
        return END_CONDITION_BUST
    else:
        return None


def mp_place_bet(table, player, amt):
    table.pot += amt
    player.balance -= amt
    table.status = 1
    table.save()
    player.save()


def mp_dealer_hit(table):
    cards = models.Card.objects.filter(tableID=table, dealt=False)
    if not cards:
        return None
    card_choice = random.choice(cards)
    card_choice.dealt = True
    card_choice.dealer = True
    card_choice.save()
    return card_choice


def mp_player_hit(table, user, split=False):
    cards = models.Card.objects.filter(tableID=table, dealt=False)
    if not cards:
        return None
    card_choice = random.choice(cards)
    card_choice.dealt = True
    card_choice.split = split
    card_choice.playerID = user
    card_choice.save()


def mp_resync(table, user, dealer_flip=False):
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
def mp_prep_table(user):
    if tableInstance := models.Table.objects.annotate(num_players=Count('players')).filter(num_players__lt=5,
                                                                                           mp_status__isnull=False).first():
        tableInstance.players.add(user)
    if tableInstance is None:
        tableInstance = mp_generate_table(user)
    return tableInstance


def mp_reset_table(table, user):
    trackers = models.PlayerTracker.objects.filter(tableID=table)
    trackers.delete()
    bets = models.Bet.objects.filter(tableID=table)
    bets.delete()
    table.delete()
    deck = models.Card.objects.filter(tableID=table)
    deck.delete()

    return mp_generate_table(user)


# Generate a table and associated deck for either singleplayer or multiplayer
def mp_generate_table(user):
    table_instance = models.Table(status=0)
    table_instance.save()
    table_instance.mp_status = 0
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
        card.hidden = False
        card.split = False
        card.save()
