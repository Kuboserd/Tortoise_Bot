import logging

from discord.ext import commands
from services.CharacterService import TURTLE_WOW_ARMORY_URL, list_character_levels


class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # === COMMANDS USER:
    @commands.command(help="List all characters level in the tracking list.")
    async def list(self, ctx):
        logging.info(f"Handle !list executed by: {ctx.author.display_name}")

        result = await list_character_levels()

        await ctx.send(result)

    @commands.command(help="Sends link to armory page of specified character_name.")
    async def link(self, ctx, character_name: str):
        logging.info(f"Handle !link character:{character_name} executed by: {ctx.author.display_name}")

        url = f"{TURTLE_WOW_ARMORY_URL}{character_name}"

        await ctx.author.send(url)


async def setup(bot):
    await bot.add_cog(User(bot))
