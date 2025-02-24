from dataclasses import dataclass
from typing import List, Literal

class Card:
    def __init__(
        self,
        color: Literal["Blue", "Green", "Red", "Yellow", "Wild"],
        face: Literal[
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Skip",
            "Reverse", "Draw Two", "Wild", "Wild Draw Four", "Wild Draw Eight"
        ],
        id: int
    ):
        self.color = color
        self.face = face
        self.id = id

    def __repr__(self):
        return f"Card({self.color}, {self.face}, {self.id})"


class Player:
    def __init__(self, id: str, hand: List['Card'], has_played_card: bool = False, has_said_uno: bool = False):
        self.id = id
        self.hand = hand  # List of Card objects
        self.has_played_card = has_played_card
        self.has_said_uno = has_said_uno

    def __repr__(self):
        return f"Player(ID: {self.id}, Cards: {len(self.hand)}, Has Played: {self.has_played_card}, Has Said Uno: {self.has_said_uno})"

class GameState:
    def __init__(self, current_player_index: int, deck: List['Card'], discard: List['Card'], is_reversed: bool, players: List['Player']):
        self.current_player_index = current_player_index
        self.deck = deck  # List of Card objects
        self.discard = discard  # List of Card objects
        self.is_reversed = is_reversed
        self.players = players  # List of Player objects

    def __repr__(self):
        return f"GameState(Current Player Index: {self.current_player_index}, Players: {len(self.players)}, Deck Size: {len(self.deck)}, Discard Size: {len(self.discard)}, Is Reversed: {self.is_reversed})"