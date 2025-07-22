import datetime
import logging

from discord.ext import commands, tasks

from main import GUILD_ID
from services.CharacterService import update_characters


class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.task_update_characters.start()

    # === BACKGROUND TASK === Machine is in UTC+0 that's why we are setting hour to 22
    @tasks.loop(time=datetime.time(hour=22, minute=0, second=0))
    async def task_update_characters(self):
        logging.info('Task update characters started')
        await update_characters(self.bot.get_guild(GUILD_ID).members)
        logging.info('Task update characters ended')

async def setup(bot):
    await bot.add_cog(Scheduler(bot))