import discord
from discord.ext import commands
from core.config import DISCORD_TOKEN
from core.logger import logger
import os

class SentinelBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="/", intents=intents)
        self.logger = logger

    async def setup_hook(self):
        self.logger.info("Setting up bot hooks...")
        # Load extensions (cogs) here if needed
        await self.load_extension('events.handlers')
        await self.load_extension('modules.auth.commands')

    async def on_ready(self):
        self.logger.info(f'Logged in as {self.user.name} (ID: {self.user.id})')
        self.logger.info('------')

if __name__ == "__main__":
    bot = SentinelBot()
    if not DISCORD_TOKEN:
        logger.error("No DISCORD_TOKEN found in .env file.")
    else:
        bot.run(DISCORD_TOKEN)
