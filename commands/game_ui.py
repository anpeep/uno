import asyncio

import discord
from discord import ButtonStyle, Button
from discord import Interaction, Embed
from discord.ui import Button
from discord.ui import View

from application.game_logic import GameLogic
from application.types import GameCheat
from common.types import Card
from common.types import Player


def get_card_label(card: Card) -> str:
    color_emoji = get_color_emoji(card.color)
    return f"{color_emoji}{card.face}"


def get_color_emoji(color: str) -> str:
    if color == "Wild":
        return "⚫"
    elif color == "Red":
        return "🔴"
    elif color == "Green":
        return "🟢"
    elif color == "Blue":
        return "🔵"
    elif color == "Yellow":
        return "🟡"
    else:
        raise ValueError("Unknown color")


def get_card_image_path(card: Card) -> str:
    base_path = "./assets/images/cards"
    return f"{base_path}/card-{card.color.lower()}-{card.face.lower().replace(' ', '_')}.png"


class GameUI(View):
    def __init__(self):
        super().__init__()
        self.message = None
        self.initiator = None
        self.last_player = None
        self.game_logic = GameLogic()
        self.players = []

        self.action_player_interactions: dict[str, dict[str, list[Interaction]]] = {
            "cardSelection": {},
            "wildCardColorSelection": {}
        }

    async def handle_start(self, interaction: Interaction):
        if self.initiator is not None:
            await interaction.response.send_message(
                "There is already a lobby in progress.", ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        self.initiator = interaction.user
        self.players.append(self.initiator)

        await interaction.response.send_message(
            f"Lobby created! {self.initiator.mention} is the host.", view=self
        )

    @discord.ui.button(label="Join", style=ButtonStyle.primary, custom_id="join-btn")
    async def join_button(self, interaction: Interaction):
        if self.message is None:
            raise ValueError("Message is null")
        member = interaction.user
        if any(player.id == member.id for player in self.players):
            await interaction.response.send_message(
                "You have already joined this lobby.", ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return
        self.players.append(member)
        await self.message.edit(content=self.get_message_content())
        if self.initiator is None:
            raise ValueError("Initiator is null")
        await interaction.response.send_message(
            f"You have joined {self.initiator.mention}'s lobby.", ephemeral=True
        )
        await asyncio.sleep(10)
        await interaction.delete_original_response()

    @discord.ui.button(label="Start", style=ButtonStyle.success, custom_id="start-btn")
    async def handle_start_button(self, interaction: Interaction):
        member = interaction.user
        if self.initiator != member:
            await interaction.response.send_message(
                "You are not the initiator.",
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        min_player_amount = 2
        if len(self.players) < min_player_amount:
            await interaction.response.send_message(
                f"Not enough players. Needed amount: {min_player_amount}.",
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return
        if self.message is None:
            raise ValueError("Message is null")
        await self.start_game()

        await interaction.response.send_message(
            "Game has started!",
            ephemeral=False
        )
        await asyncio.sleep(10)
        await interaction.delete_original_response()

    @discord.ui.button(label="Cancel", style=ButtonStyle.danger, custom_id="cancel-btn")
    async def handle_cancel_button(self, interaction: Interaction):
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user
        if self.initiator != member:
            await interaction.response.send_message(
                "You are not the initiator.",
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        await self.message.delete()
        self.reset_game()

        await interaction.response.send_message(
            "You have deleted the lobby.",
            ephemeral=True
        )

        await asyncio.sleep(10)
        await interaction.delete_original_response()

    async def handle_show_cards_button(self, interaction: Interaction):
        member = interaction.user
        await self.delete_action_replies(["cardSelection", "wildCardColorSelection"], member.name)

        cards = self.game_logic.get_player_cards(member.id)

        current_player = self.game_logic.get_current_player()
        if isinstance(current_player, Player):
            is_current_player = current_player.id == member.id

            buttons = []
            for card in cards:
                label = get_card_label(card)
                can_play = self.game_logic.can_play_card(card, current_player.id)

                button = Button(
                    label=label,
                    style=ButtonStyle.secondary,
                    custom_id=f"card-{card.id}",
                    disabled=not is_current_player or not can_play
                )
                buttons.append(button)

            draw_card_button = Button(
                label="Draw Card",
                style=ButtonStyle.danger,
                custom_id="draw-card-btn",
                disabled=not is_current_player
            )
            buttons.append(draw_card_button)
            max_buttons_per_row = 25

            rows = []
            for i in range(0, len(buttons), max_buttons_per_row):
                row = buttons[i:i + max_buttons_per_row]
                view = View()
                view.add_item(*row)
                rows.append(view)

            for row in rows:
                await interaction.response.send_message(
                    content="Here are your cards:",
                    view=row
                )
            self.add_action_player_interaction("cardSelection", interaction.user.name, interaction)

    async def handle_card_button(self, interaction: discord.Interaction, card_id: int):
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user
        player_cards = self.game_logic.get_player_cards(member.id)
        card = next((c for c in player_cards if c.id == card_id), None)

        if not card:
            await interaction.response.send_message(
                "Card not found.",
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        if card.color == "Wild":
            await self.handle_wild_card_color(card_id, interaction)
            return

        result = self.game_logic.play_card(self.players[member.id], card_id)

        if "error" in result:
            await interaction.response.send_message(
                result["error"],
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        self.last_player = member

        await interaction.response.send_message(
            "You played a card.",
            ephemeral=True
        )

        await interaction.delete_original_response()

        top_card = self.game_logic.get_top_card()
        await self.message.edit(
            content=self.get_game_message_content(),
            attachments=[get_card_image_path(top_card) if top_card else []]
        )

        await self.delete_action_replies(["cardSelection", "wildCardColorSelection"], self.players[member.id])

        is_winner = self.game_logic.is_winner(self.players[member.id])
        if not is_winner:
            return

        if not top_card:
            raise ValueError("Top card is null")

        card_label = get_card_label(top_card)
        await self.message.edit(
            content=f"🏆 {member.mention} has won the game!\n\n... by placing {card_label} as their last card.",
            components=[],
            attachments=[]
        )

        # Timeout, pärast seda kustutame sõnumi ja lähtestame mängu
        await asyncio.sleep(30)
        await self.message.delete()
        self.reset_game()

    async def handle_color_selection(self, interaction: Interaction, card_id: int, color: str):
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user  # Discordi liige
        player_cards = self.game_logic.get_player_cards(member.id)
        card = next((c for c in player_cards if c.id == card_id), None)

        if not card:
            await interaction.response.send_message(
                "Card not found.",
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        result2 = self.game_logic.play_card(self.players[member.id], card_id)
        if "error" in result2:
            await interaction.response.send_message(
                result2["error"],
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        result1 = self.game_logic.change_wild_card_color(card_id, color)
        if "error" in result1:
            await interaction.response.send_message(
                result1["error"],
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        self.last_player = member

        await interaction.response.send_message(
            "You played a card.",
            ephemeral=True
        )

        await interaction.delete_original_response()

        await self.delete_action_replies(["cardSelection", "wildCardColorSelection"], (self.players[member.id]))

        top_card = self.game_logic.get_top_card()
        await self.message.edit(
            content=self.get_game_message_content(),
            attachments=[get_card_image_path(top_card) if top_card else []]
        )

        is_winner = self.game_logic.is_winner(self.players[member.id])
        if not is_winner:
            return

        if not top_card:
            raise ValueError("Top card is null")

        card_label = get_card_label(top_card)
        await self.message.edit(
            content=f"🏆 {member.mention} has won the game!\n\n... by placing {card_label} as their last card.",
            components=[],
            attachments=[]
        )
        await asyncio.sleep(30)
        await self.message.delete()
        self.reset_game()

    async def handle_draw_card_button(self, interaction: Interaction):
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user
        current_player = self.game_logic.get_current_player()

        if current_player.id != member.id:
            await interaction.response.send_message(
                "It is not your turn.",
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return
        result = self.game_logic.draw_card(self.players[member.id])
        if "error" in result:
            await interaction.response.send_message(
                result["error"],
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        await interaction.response.send_message(
            "You drew a card.",
            ephemeral=True
        )

        await interaction.delete_original_response()

        await self.delete_action_replies(["cardSelection", "wildCardColorSelection"], self.players[member.id])

        await self.message.edit(
            content=self.get_game_message_content(),
        )

    async def handle_say_uno(self, interaction: Interaction):
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user

        if member.id != self.game_logic.get_current_player().id:
            await interaction.response.send_message(
                "It is not your turn.",
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        result = self.game_logic.say_uno(self.players[member.id])

        if "error" in result:
            await interaction.response.send_message(
                result["error"],
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        # Tagasiside, et mängija ütles "UNO"
        await interaction.response.send_message(
            f"{member.mention} said UNO!"
        )

        await asyncio.sleep(10)
        await interaction.delete_original_response()

    async def handle_cheat_code(self, interaction: Interaction, code: str):
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user
        result = {"data": None, "error": "No cheat code found"}

        if code == "giveWildFour":
            result = self.game_logic.activate_cheat_code(self.players[member.id], GameCheat.GIVE_WILD_FOUR)
        elif code == "giveWildEight":
            result = self.game_logic.activate_cheat_code(self.players[member.id], GameCheat.GIVE_WILD_EIGHT)

        if "error" in result:
            await interaction.response.send_message(
                result["error"],
                ephemeral=True
            )
            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        await self.message.edit(
            embeds=[self.get_game_message_content()]
        )

        await interaction.response.send_message(
            "Cheat code activated.",
            ephemeral=True
        )

    async def handle_wild_card_color(self, card_id: int, interaction: Interaction):
        colors = ["Red", "Green", "Blue", "Yellow"]

        buttons = [
            Button(
                label=get_color_emoji(color),
                style=discord.ButtonStyle.secondary,
                custom_id=f"color-{color}-{card_id}",
            )
            for color in colors
        ]

        await interaction.response.send_message(
            content="Select a color for the wild card:",
            components=[buttons],
            ephemeral=True,
        )

        member = interaction.user
        await self.delete_action_replies(["wildCardColorSelection"], self.players[member.id])
        self.add_action_player_interaction("wildCardColorSelection", self.players[member.id], interaction)

    def add_action_player_interaction(self, action: str, player_id: str, interaction: Interaction):
        self.action_player_interactions[action][player_id].append(interaction)

    async def delete_action_replies(self, actions: list, player_id: str) -> None:
        for action in actions:
            interactions = self.action_player_interactions.get(action, {}).get(player_id, [])
            self.action_player_interactions[action][player_id] = []  # Clear interactions for this player
            await asyncio.gather(*(interaction.delete_original_response() for interaction in interactions))

    def reset_game(self):
        self.initiator = None
        self.message = None
        self.players.clear()
        self.game_logic.reset()

    async def start_game(self):
        if self.message is None:
            raise ValueError("Message is null")

        player_ids = [player.user.id for player in self.players]  # kas user
        self.game_logic.start_game(player_ids)

        id_order = [player.id for player in self.game_logic.get_players()]
        self.players.sort(key=lambda player: id_order.index(player.user.id))

        say_uno_button = Button(
            label="Say UNO",
            style=ButtonStyle.primary,
            custom_id="say-uno-btn"
        )

        leave_button = Button(
            label="Leave",
            style=ButtonStyle.danger,
            custom_id="leave-btn"
        )
        show_cards_button = Button(
            label="Show Cards",
            style=ButtonStyle.danger,
            custom_id="show-cards-btn"
        )

        view = View()
        view.add_item(show_cards_button)
        view.add_item(say_uno_button)
        view.add_item(leave_button)

        await self.message.edit(
            components=[show_cards_button, say_uno_button, leave_button],
            content=None,
            view=view,
            embeds=[self.get_game_message_content()]
        )

    def get_game_message_content(self):
        players = []
        for player in self.players:
            card_count = len(self.game_logic.get_player_cards(player.user.id))
            if player.user.id == self.game_logic.get_current_player().id:
                players.append(f"> {str(player)} ({card_count} cards)")
            else:
                players.append(f"     {str(player)} ({card_count} cards)")

        if self.game_logic.is_reversed():
            players.reverse()

        order_message = "\n".join(players)

        top_card = self.game_logic.get_top_card()
        top_card_label = get_card_label(top_card) if top_card else "None"

        deck_card_amount = len(self.game_logic.get_deck_cards())
        discard_card_amount = len(self.game_logic.get_discard_cards())

        embed = Embed(title="UNO Game Status")
        embed.add_field(name="Deck", value=str(deck_card_amount), inline=True)
        embed.add_field(name="Discard", value=str(discard_card_amount), inline=True)
        embed.add_field(name="Players", value=order_message, inline=False)
        embed.add_field(name="Top card", value=top_card_label, inline=True)
        embed.add_field(name="Placed by", value=str(self.last_player) if self.last_player else "None", inline=True)
        if top_card:
            path = get_card_image_path(top_card)
            base_path = "./assets/images/cards/"
            if path.startswith(base_path):
                path = path[len(base_path):]
            embed.set_image(url=f"attachment://{path}")
        return embed

    def get_message_content(self) -> str:
        if self.initiator is None:
            raise ValueError("Initiator is null")
        players_list = ", ".join(str(player) for player in self.players)

        return f"{str(self.initiator)} has created an UNO lobby.\n\nPlayers: {players_list}"
