from discord import app_commands
import discord
from src.bot.gs_bot import bot
from src.config.settings import GS_CHANNEL_ID
from src.utils.permissions import has_required_role
from src.utils.embeds import create_admin_menu_embed
from src.views.admin_views import AdminCategoryView

@bot.tree.command(name="admin", description="Accéder au menu d'administration")
async def admin(interaction: discord.Interaction):
    """Interface d'administration pour la GS"""
    try:
        if not has_required_role(interaction):
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission d'utiliser cette commande.",
                ephemeral=True, delete_after=10
            )
            return

        if interaction.channel_id != GS_CHANNEL_ID:
            await interaction.response.send_message(
                "Cette commande ne peut être utilisée que dans le salon GS !",
                ephemeral=True, delete_after=10
            )
            return

        embed = create_admin_menu_embed()
        view = AdminCategoryView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        print(f"Erreur dans la commande admin: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("Une erreur s'est produite.", ephemeral=True, delete_after=10)