import logging

from discord.ext import commands

from STATES import AddResult, RemoveResult
from services.CharacterService import remove_character_from_list, add_character_to_list, update_characters
from services.player import select_player


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # === COMMANDS ADMIN:
    @commands.command(help="Manually start characters level update")
    async def update(self, ctx):
        logging.info(f"Handle !update executed by: {ctx.author.display_name}")

        await update_characters()

        await ctx.send(f"Updated character levels!")


    @commands.command(help="Adds players character to checklist")
    async def add_character(self, ctx, character_name: str, player_name: str):
        logging.info(
            f"Handle !add_character character:{character_name} player:{player_name} executed by: {ctx.author.display_name}")

        player_id = await select_player(ctx.message.guild.members, player_name)
        result = await add_character_to_list(character_name, player_id)

        if result == AddResult.EXISTS:
            await ctx.send(f"{character_name} is already in the list.")
        elif result == AddResult.NO_SUCH_PLAYER:
            await ctx.send(f"{player_name} is not a member of this server.")
        elif result == AddResult.NO_SUCH_CHARACTER:
            await ctx.send(f"{character_name} is not valid.")
        elif result == AddResult.ADDED:
            await ctx.send(f"Added {character_name} to the tracking list!")

    @commands.command(help="Removes players character from the checklist.")
    async def remove_character(self, ctx, character_name: str):
        logging.info(f"Handle !remove_character character:{character_name} executed by: {ctx.author.display_name}")

        result = await remove_character_from_list()

        if result == RemoveResult.NOT_EXISTS:
            await ctx.send(f"{character_name} is not in the list.")
        elif result == RemoveResult.REMOVED:
            await ctx.send(f"Removed {character_name} from the tracking list.")


async def setup(bot):
    await bot.add_cog(Admin(bot))
