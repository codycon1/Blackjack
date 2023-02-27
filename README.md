# Blackjack

## Starting the local development server
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

## Modules
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

## TODO:
- Django Channels Integration
- Game rooms
- Game logic
- Multiplayer compatibility

## Singleplayer JSON structure:
dealercards{
  [card(suit, rank, url)]
}
playercards{
  [card(suit, rank, url)]
}
action{
  int - 0: hit, 1: stay, etc
}