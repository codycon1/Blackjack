# Blackjack

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