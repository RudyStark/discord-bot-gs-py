from discord import app_commands
import discord
from src.bot.gs_bot import bot
from src.config.settings import GS_CHANNEL_ID
from src.utils.permissions import has_required_role
from src.utils.embeds import update_gs_message

@bot.tree.command(name="add_player", description="Ajouter des joueurs à la GS")
async def add_player(interaction: discord.Interaction,
                    joueur1: discord.Member,
                    joueur2: discord.Member = None,
                    joueur3: discord.Member = None):
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True, delete_after=10)
        return

    new_players = [j for j in [joueur1, joueur2, joueur3] if j is not None]

    for player in new_players:
        if player.id not in bot.gs_data['players']:
            bot.gs_data['players'][player.id] = {
                "name": player.display_name,
                "mention": player.mention
            }

    await interaction.response.send_message("✅ Joueurs ajoutés avec succès.", ephemeral=True, delete_after=10)
    await update_gs_message(interaction.channel)

@bot.tree.command(name="remove_player", description="Retirer des joueurs de la GS")
async def remove_player(interaction: discord.Interaction,
                       joueur1: discord.Member,
                       joueur2: discord.Member = None,
                       joueur3: discord.Member = None):
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True, delete_after=10)
        return

    players = [j for j in [joueur1, joueur2, joueur3] if j is not None]

    for player in players:
        if player.id in bot.gs_data['players']:
            del bot.gs_data['players'][player.id]
            if player.id in bot.gs_data['defenses']: del bot.gs_data['defenses'][player.id]
            if player.id in bot.gs_data['tests']: del bot.gs_data['tests'][player.id]
            if player.id in bot.gs_data['attacks']: del bot.gs_data['attacks'][player.id]
            if player.id in bot.gs_data['stars']: del bot.gs_data['stars'][player.id]

    await interaction.response.send_message("✅ Joueurs retirés avec succès.", ephemeral=True, delete_after=10)
    await update_gs_message(interaction.channel)