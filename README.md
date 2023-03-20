# Blackjack

### Starting the local development server
- Add modules to global python (or use a VENV)
  - pip install -r requirements.txt
- Start Redis and PostgreSQL with docker
  - docker-compose up
- Initialize the database
  - python3 manage.py makemigrations
  - python3 manage.py migrate
- Make a superuser for the django admin panel
  - python3 manage.py createsuperuser
- Start inbuilt django server
  - python3 manage.py runserver

### Modules
- Users
  - User authentication
  - User model
    - Username
    - Password
    - Balance
- Game
  - Blackjack game module
  - Table model
    - Table ID (primary key)
    - Pot (decimal)
    - Status(integer)
  - Card model (52 entries w/same tableID => deck)
    - Card ID (primary key)
    - User ID (foreign key)
    - Suit (integer 0-3)
    - Rank (integer 1-13)
    - Image (url, relative)
    - Dealt (bool)
    - tableID

### TODO:
- Django Channels Integration
- Game rooms
- Game logic
- Multiplayer compatibility

### Singleplayer JSON structure - Server to Client:
- player - singleplayer serialized JSON representation of user model
- dealercards - list of dealer's cards
- playercards - list of player cards
- dtotal - dealer's running total
- ptotal - player's running total
- readysignal - list of button IDs to display based on available user actions

player{
  int playerid
  str username
  int balance
}
dealercards{
  [card(suit, rank, url)]
}
playercards{
  [card(suit, rank, url)]
}
playerbalance{
  int balance
}
dtotal{
  int dtotal
}
ptotal{
  int ptotal
}
readysignal{
  [btn]
}

Note: Any of these may be Null, structure will always be sent in this format

## Singleplayer JSON structure - Client to Server:
- action - button id for player's action
- betamt - bet amount (optional - only for initial bet)

