import os
import random
import sys
from typing import List, Union, Dict

from application.types import GameCheat
from common.types import Player

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Fisher-Yates shuffle algorithm
def shuffle(array):
    m = len(array)

    while m:
        m -= 1
        i = random.randint(0, m)
        array[m], array[i] = array[i], array[m]

    return array


def create_cards() -> List[Dict[str, Union[str, int]]]:
    colors = ["Blue", "Green", "Red", "Yellow"]
    faces = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Skip", "Reverse", "Draw Two"]
    wild_faces = ["Wild", "Wild Draw Four"]
    cards = []

    def add_card(clr: str, fc: str):
        cards.append({"color": clr, "face": fc, "id": len(cards)})

    for color in colors:
        for face in faces:
            add_card(color, face)
            if face != "0":
                add_card(color, face)

    for face in wild_faces:
        for _ in range(4):
            add_card("Wild", face)

    return cards


def distribute_cards(players, cards):
    for player in players:
        player["hand"] = [cards.pop(0) for _ in range(7)]


class GameLogic:
    def __init__(self):
        self.game_state = {
            "current_player_index": 0,
            "deck": [],
            "discard": [],
            "is_reversed": False,
            "players": []
        }

    def is_reversed(self):
        return self.game_state["is_reversed"]

    def reset(self):
        self.game_state.update({
            "current_player_index": 0,
            "deck": [],
            "discard": [],
            "is_reversed": False,
            "players": []
        })

    def start_game(self, player_ids):
        players = [{"hand": [], "has_played_card": False, "has_said_uno": False, "id": pid} for pid in player_ids]
        self.game_state["players"] = shuffle(players)
        self.game_state["deck"] = shuffle(create_cards())
        distribute_cards(self.game_state["players"], self.game_state["deck"])

    def get_players(self):
        return self.game_state["players"].copy()  # kas copyta?

    def get_player_cards(self, user_id):
        player = next((p for p in self.game_state["players"] if p["id"] == user_id), None)
        if player is None:
            raise ValueError("Player not found")
        return player["hand"]

    def get_top_card(self):
        if not self.game_state["discard"]:
            return None
        return self.game_state["discard"][-1]

    def get_deck_cards(self):
        return self.game_state["deck"].copy()  # kas copyta?

    def get_discard_cards(self):
        return self.game_state["discard"].copy()  # kas copyta?

    def get_current_player(self):
        return self.game_state["players"][self.game_state["current_player_index"]]

    def next_turn(self):
        current_player = self.get_current_player()

        if len(current_player["hand"]) == 1 and not current_player["has_said_uno"]:
            self.draw_cards(current_player, 2)

        current_player["has_played_card"] = False
        current_player["has_said_uno"] = False
        self.game_state["current_player_index"] = self.game_state["players"].index(self.get_next_player())

    def can_play_card(self, card: dict, player_id: str) -> bool:
        if not self.game_state["discard"]:
            return True

        top_card = self.game_state["discard"][-1]
        can_play_others = card["color"] == top_card["color"] or card["face"] == top_card["face"] or card[
            "color"] == "Wild"

        if not can_play_others and card["face"] != "Wild Draw Four":
            return False

        player = next((p for p in self.game_state["players"] if p["id"] == player_id), None)
        if not player:
            raise ValueError("Player not found")

        has_other_cards = any(c["color"] == top_card["color"] for c in player["hand"])
        return not has_other_cards

    def play_card(self, player_id: str, card_id: int) -> dict:
        player = next((p for p in self.game_state["players"] if p["id"] == player_id), None)
        if not player:
            raise ValueError("Player not found")

        if player["id"] != self.get_current_player()["id"]:
            return {"error": "Not the player's turn"}
        if player.get("hasPlayedCard"):
            return {"error": "Player has already played a card"}

        card_index = next((i for i, c in enumerate(player["hand"]) if c["id"] == card_id), -1)
        if card_index == -1:
            return {"error": "Card not found in player's hand"}

        card = player["hand"].pop(card_index)
        if not self.can_play_card(card, player_id):
            return {"error": "Cannot play this card"}

        self.game_state["discard"].append(card)
        player["hasPlayedCard"] = True

        if card["face"] == "Wild Draw Four":
            self.draw_cards(self.get_next_player(), 4)
        elif card["face"] == "Wild Draw Eight":
            self.draw_cards(self.get_next_player(), 8)
            self.next_turn()
        elif card["face"] == "Reverse":
            self.game_state["isReversed"] = not self.game_state["isReversed"]
        elif card["face"] == "Skip":
            self.next_turn()
        elif card["face"] == "Draw Two":
            self.draw_cards(self.get_next_player(), 2)
            self.next_turn()

        self.next_turn()
        return {"data": None}

    def change_wild_card_color(self, card_id: int, new_color: str) -> dict:
        if not self.game_state["discard"]:
            return {"error": "No cards in discard pile"}

        last_card = self.game_state["discard"][-1]
        if last_card["id"] != card_id:
            return {"error": "Last card is not this one."}

        if last_card["color"] != "Wild":
            raise ValueError("Last card in deck is not a Wild card")

        last_card["color"] = new_color
        return {"data": None}

    def draw_card(self, player_id: str) -> dict:
        player = next((p for p in self.game_state["players"] if p["id"] == player_id), None)
        if not player:
            raise ValueError("Player not found")

        if player["id"] != self.get_current_player()["id"]:
            return {"error": "Not the player's turn"}
        if player.get("hasPlayedCard"):
            return {"error": "Player has already played a card"}
        self.draw_cards(player, 1)
        player["hasPlayedCard"] = True
        self.next_turn()
        return {"data": None}

    def is_winner(self, player_id: str) -> bool:
        player = next((p for p in self.game_state["players"] if p["id"] == player_id), None)
        if not player:
            raise ValueError("Player not found")
        return len(player["hand"]) == 0

    def say_uno(self, player_id: str) -> dict:
        player = next((p for p in self.game_state["players"] if p["id"] == player_id), None)
        if not player:
            raise ValueError("Player not found")

        if player.get("hasSaidUno"):
            return {"error": "Player has already called UNO"}

        if len(player["hand"]) != 2:
            return {"error": "Player cannot call UNO unless they have exactly two cards"}

        player["hasSaidUno"] = True
        return {"data": None}

    def activate_cheat_code(self, player_id: str, game_cheat: GameCheat) -> dict:
        if not self.game_state["players"]:
            return {"error": "Game has not started yet"}

        player = next((p for p in self.game_state["players"] if p["id"] == player_id), None)
        if not player:
            raise ValueError("Player not found")

        if game_cheat == GameCheat.GIVE_WILD_FOUR:
            new_card_id = random.randint(10000, 10000000)
            new_card = {"color": "Wild", "face": "Wild Draw Four", "id": new_card_id}
            player["hand"].append(new_card)
        elif game_cheat == GameCheat.GIVE_WILD_EIGHT:
            new_card_id = random.randint(10000, 10000000)
            new_card = {"color": "Wild", "face": "Wild Draw Eight", "id": new_card_id}
            player["hand"].append(new_card)
        else:
            return {"error": "Invalid cheat code"}

        return {"data": None}

    def draw_cards(self, player: Player, count: int) -> None:
        for _ in range(count):
            if not self.game_state["deck"]:
                self.game_state["deck"] = shuffle(self.game_state["discard"][:-1])
                for card in self.game_state["deck"]:
                    if card["face"].startswith("Wild"):
                        card["color"] = "Wild"

            if self.game_state["deck"]:
                card = self.game_state["deck"].pop()
                player.hand.append(card)

    def get_next_player(self) ->  Player:
        players = self.game_state["players"]
        if not players:
            raise ValueError("No players in the game")
        current_index = self.game_state["currentPlayerIndex"]
        player_count = len(players)
        next_index = (current_index - 1 + player_count) % player_count if self.game_state["isReversed"] else (current_index + 1) % player_count
        return self.game_state[next_index]