import discord
from discord.ext import commands

class GSBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

        self.gs_data = {
            'players': {},
            'defenses': {},
            'tests': {},
            'attacks': {},
            'stars': {},
            'message_id': None,
            'season_start': None
        }

    async def setup_hook(self):
        await self.tree.sync()

# Instance globale du bot
bot = GSBot()