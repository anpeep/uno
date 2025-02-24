import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        await interaction.response.send_message(f"Received interaction with {interaction.custom_id}")

async def run():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Could not find BOT_TOKEN in your environment")

    await bot.start(token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
