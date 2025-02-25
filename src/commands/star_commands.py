from discord import app_commands
import discord
from src.bot.gs_bot import bot
from src.utils.permissions import has_required_role
from src.utils.embeds import update_gs_message

@bot.tree.command(name="add_star", description="Ajouter des étoiles à un participant")
async def add_star(interaction: discord.Interaction, joueur: discord.Member, nombre: app_commands.Choice[int]):
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Permission refusée.", ephemeral=True, delete_after=10)
        return False

    if joueur.id not in bot.gs_data['players']:
        await interaction.response.send_message("❌ Joueur non trouvé dans la GS.", ephemeral=True, delete_after=10)
        return False

    bot.gs_data['stars'][joueur.id] = nombre.value
    await interaction.response.send_message(
        f"✅ {nombre.value} étoile(s) ajoutée(s) à {joueur.mention}.",
        ephemeral=True
    )
    await update_gs_message(interaction.channel)
    return True