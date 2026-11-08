import logging

from discord.ext import commands
from services.CharacterService import list_character_levels
from services.blizzard_api import armory_url


class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # === COMMANDS USER:
    @commands.command(help="List all characters level in the tracking list.")
    async def list(self, ctx):
        logging.info(f"Handle !list executed by: {ctx.author.display_name}")

        result = await list_character_levels()

        await ctx.send(result)

    @commands.command(help="Sends the Forever armory link. Usage: !link <name> <surname>")
    async def link(self, ctx, name: str, surname: str):
        character_name = f"{name} {surname}"
        logging.info(f"Handle !link character:{character_name} executed by: {ctx.author.display_name}")

        await ctx.author.send(armory_url(character_name))


async def setup(bot):
    await bot.add_cog(User(bot))
