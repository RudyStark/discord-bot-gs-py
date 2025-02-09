from discord import app_commands
import discord
from src.bot.gs_bot import bot
from src.config.settings import GS_CHANNEL_ID
from src.utils.permissions import has_required_role
from src.utils.embeds import update_gs_message, create_gs_embed

@bot.tree.command(name="init_gs", description="Initialiser une nouvelle Guerre Sainte avec les joueurs mentionnés")
async def init_gs(interaction: discord.Interaction,
                 joueur1: discord.Member,
                 joueur2: discord.Member = None,
                 joueur3: discord.Member = None,
                 joueur4: discord.Member = None,
                 joueur5: discord.Member = None):
    try:
        if not has_required_role(interaction):
            await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True, delete_after=10)
            return

        await interaction.response.defer(ephemeral=True, delete_after=10)

        players = [j for j in [joueur1, joueur2, joueur3, joueur4, joueur5] if j is not None]
        bot.gs_data['players'] = {}
        bot.gs_data['defenses'] = {}
        bot.gs_data['tests'] = {}
        bot.gs_data['attacks'] = {}
        bot.gs_data['stars'] = {}
        bot.gs_data['message_id'] = None

        for player in players:
            bot.gs_data['players'][player.id] = {
                "name": player.display_name,
                "mention": player.mention
            }

        embed = create_gs_embed()
        message = await interaction.channel.send(embed=embed)
        await message.pin()
        bot.gs_data['message_id'] = message.id

        await interaction.followup.send("✅ Guerre Sainte initialisée !", ephemeral=True, delete_after=10)

    except Exception as e:
        print(f"Error in init_gs: {str(e)}")
        await interaction.followup.send("❌ Une erreur s'est produite lors de l'initialisation.", ephemeral=True, delete_after=10)

@bot.tree.command(name="check_actions", description="Voir qui n'a pas encore effectué toutes ses actions")
async def check_actions(interaction: discord.Interaction):
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True, delete_after=10)
        return

    embed = discord.Embed(
        title="📋 Actions manquantes",
        description="Récapitulatif des actions à faire",
        color=discord.Color.orange()
    )
    # Votre logique de vérification existante
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="reset_all_actions", description="Réinitialiser toutes les actions")
async def reset_all_actions(interaction: discord.Interaction):
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True, delete_after=10)
        return

    players_backup = bot.gs_data['players'].copy()
    message_id_backup = bot.gs_data['message_id']

    bot.gs_data['defenses'] = {}
    bot.gs_data['tests'] = {}
    bot.gs_data['attacks'] = {}

    bot.gs_data['players'] = players_backup
    bot.gs_data['message_id'] = message_id_backup

    await interaction.response.send_message("✅ Toutes les actions ont été réinitialisées.", ephemeral=True, delete_after=10)
    await update_gs_message(interaction.channel)