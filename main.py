import asyncio
import signal
import sys
import logging
import discord
from discord.ext import commands
from services.CharacterService import load_characters_from_file, update_characters, list_character_levels, \
    save_characters_to_file

# === SETTINGS ===


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# === LOGGING ===
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
        await bot.start(TOKEN)


# === STARTUP HOOK ===
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    load_characters_from_file()
    await update_characters()
    await list_character_levels()


# === Graceful Shutdown (on Ctrl+C or kill) ===
def handle_exit(*args):
    save_characters_to_file()
    logging.info("Shutting down.")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == "__main__":
    asyncio.run(main())
