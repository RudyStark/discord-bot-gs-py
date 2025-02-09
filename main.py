from src.bot.gs_bot import bot
from src.config.settings import TOKEN
import src.commands.admin_commands
import src.commands.gs_commands
import src.commands.player_commands
import src.commands.star_commands
import src.commands.celebration_commands
import src.commands.action_commands

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)} commandes")
        for cmd in synced:
            print(f"- /{cmd.name}")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes : {e}")

bot.run(TOKEN)