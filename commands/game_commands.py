import discord
from discord.ext import commands

import game_ui
class GameCommands(commands.Cog):
    def __init__(self, bot):  # kas tohtisin boti siia panna
        self.bot = bot
        self.game_ui = game_ui.GameUI()

    @commands.command(name="uno", help="Create an UNO lobby")
    async def start(self, ctx):
        await self.game_ui.handle_start(ctx)

    @commands.command(name="code", help="Enter a cheat code")
    async def cheat_code(self, ctx, code: str):
        await self.game_ui.handle_cheat_code(ctx, code)

    @commands.Cog.listener()
    async def on_button_click(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            # Workaround: Accessing custom_id from interaction.data
            custom_id = interaction.data.get('custom_id', None)  # Use interaction.data for custom_id

            if custom_id is None:
                return  # If there's no custom_id, we can't handle the interaction

            if custom_id == "join-btn":
                await self.game_ui.join_button(interaction)
            elif custom_id == "start-btn":
                await self.game_ui.handle_start_button(interaction)
            elif custom_id == "cancel-btn":
                await self.game_ui.handle_cancel_button(interaction)
            elif custom_id == "show-cards-btn":
                await self.game_ui.handle_show_cards_button(interaction)
            elif custom_id.startswith("card-"):
                card_id = int(custom_id.split("-")[1])  # Get the card ID from the custom_id
                await self.game_ui.handle_card_button(interaction, card_id)
            elif custom_id.startswith("color-"):
                parts = custom_id.split("-")  # Split color and card ID
                color, card_id = parts[1], int(parts[2])
                await self.game_ui.handle_color_selection(interaction, card_id, color)
            elif custom_id == "draw-card-btn":
                await self.game_ui.handle_draw_card_button(interaction)
            elif custom_id == "say-uno-btn":
                await self.game_ui.handle_say_uno(interaction)

async def setup(bot):
    await bot.add_cog(GameCommands(bot))
