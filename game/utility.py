from game import models

suitDict = {0: 'diamonds', 1: 'hearts', 2: 'spades', 3: 'clubs'}
rankDict = {1: 'ace', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
            10: '10', 11: 'jack', 12: 'queen', 13: 'king'}

def sp_json_sync(table):
    # TODO: Build a sync JSON here and return for syncing singleplayer clients
    # Dealer cards, pot,
    pass

# Create a single player table if it doesn't exist, else return the existing table
def sp_prep_table(user):
    table = models.Table.objects.filter(singleplayerID=user).first()
    if table is None:
        table = generate_table(user)
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
