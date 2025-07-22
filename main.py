import asyncio
import os
import signal
import sys
import logging
import discord
from discord.ext import commands
from services.CharacterService import load_characters_from_file, \
    save_characters_to_file

# === SETTINGS ===
TOKEN = os.getenv("TORTOISE_BOT_TOKEN")
GUILD_ID = 1391355994059182160
CHANNEL_ID = 1395098029404717076
ADMIN_ROLE = "Manager Ruchu"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# === LOGGING ===
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers.clear()

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler('latest.log', mode='a')
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

async def main():
    async with bot:
        await bot.load_extension("admin_commands.admin")
        await bot.load_extension("user_commands.user")
        await bot.load_extension("services.Scheduler")
        await bot.start(TOKEN)


# === STARTUP HOOK ===
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    load_characters_from_file()
    logging.info(f"Bot is ready!")


# === Graceful Shutdown (on Ctrl+C or kill) ===
def handle_exit(*args):
    save_characters_to_file()
    logging.info("Shutting down.")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == "__main__":
    asyncio.run(main())
