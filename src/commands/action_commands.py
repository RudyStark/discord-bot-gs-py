from discord import app_commands
import discord
from src.bot.gs_bot import bot
from src.config.settings import GS_CHANNEL_ID
from src.views.action_views import ActionView

@bot.tree.command(name="action", description="Définir une action (Défense/Test/Attaque)")
async def action(interaction: discord.Interaction):
    """Interface unifiée pour définir une action"""
    try:
        if interaction.channel_id != GS_CHANNEL_ID:
            await interaction.response.send_message(
                "Cette commande ne peut être utilisée que dans le salon GS !",
                ephemeral=True, delete_after=10
            )
            return

        if interaction.user.id not in bot.gs_data['players']:
            await interaction.response.send_message(
                f"{interaction.user.mention} vous n'êtes pas dans la liste des joueurs GS !",
                ephemeral=True, delete_after=10
            )
            return

        embed = discord.Embed(
            title="Choisissez votre action",
            description="Cliquez sur un bouton pour choisir le type d'action",
            color=discord.Color.blue()
        )

        view = ActionView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True, delete_after=10)

    except Exception as e:
        print(f"Erreur dans la commande action: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("Une erreur s'est produite.", ephemeral=True, delete_after=10)