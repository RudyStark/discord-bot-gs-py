import discord
import datetime
from src.config.settings import GS_CHANNEL_ID
from src.config.constants import MAX_PLAYERS
from src.utils.permissions import has_required_role
from src.utils.embeds import create_admin_menu_embed, update_gs_message, create_check_actions_embed
from src.views.selection_views import InitGSView, AddPlayerView, RemovePlayerView, AddStarView, ResetPlayerActionsView, MovePlayerView
from src.bot.gs_bot import bot
from src.commands.gs_commands import reset_all_actions, check_actions

class AdminCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Gestion GS", emoji="📊", style=discord.ButtonStyle.primary)
    async def gs_management(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_gs_management(interaction)

    @discord.ui.button(label="Gestion Joueurs", emoji="👥", style=discord.ButtonStyle.primary)
    async def player_management(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_player_management(interaction)

    @discord.ui.button(label="Gestion Performances", emoji="⭐", style=discord.ButtonStyle.primary)
    async def performance_management(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_performance_management(interaction)

    async def show_gs_management(self, interaction: discord.Interaction):
        view = GSManagementView()
        embed = discord.Embed(
            title="📊 Gestion de la GS",
            description="Sélectionnez une action à effectuer",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def show_player_management(self, interaction: discord.Interaction):
        view = PlayerManagementView()
        embed = discord.Embed(
            title="👥 Gestion des Joueurs",
            description="Sélectionnez une action à effectuer",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def show_performance_management(self, interaction: discord.Interaction):
        view = PerformanceManagementView()
        embed = discord.Embed(
            title="⭐ Gestion des Performances",
            description="Sélectionnez une action à effectuer",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

class GSManagementView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Initialiser GS", emoji="🆕", style=discord.ButtonStyle.success)
    async def init_gs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_required_role(interaction):
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission d'utiliser cette commande.",
                ephemeral=True
            )
            return

        channel = interaction.guild.get_channel(GS_CHANNEL_ID)
        channel_members = channel.members

        view = InitGSView(channel_members)
        await interaction.response.send_message(
            f"Sélectionnez les joueurs pour la GS (1-{MAX_PLAYERS} joueurs) :",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="Reset All Actions", emoji="🔄", style=discord.ButtonStyle.danger)
    async def reset_actions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
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

            if not bot.gs_data['players']:
                await interaction.response.send_message(
                    "Aucune GS n'est initialisée. Utilisez d'abord /init_gs",
                    ephemeral=True, delete_after=10
                )
                return

            # Sauvegarde uniquement des données essentielles
            players_backup = bot.gs_data['players'].copy()
            message_id_backup = bot.gs_data['message_id']

            # Réinitialisation complète de toutes les statistiques
            bot.gs_data['defenses'] = {}
            bot.gs_data['tests'] = {}
            bot.gs_data['attacks'] = {}
            bot.gs_data['stars'] = {}  # Ajout de la réinitialisation des étoiles

            # Restauration uniquement des données essentielles
            bot.gs_data['players'] = players_backup
            bot.gs_data['message_id'] = message_id_backup

            await interaction.response.send_message(
                "✅ Toutes les actions et statistiques ont été réinitialisées. La liste des participants reste inchangée.",
                ephemeral=True, delete_after=10
            )

            # Mise à jour du tableau
            await update_gs_message(interaction.channel)

        except Exception as e:
            print(f"Erreur lors de la réinitialisation des actions : {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Une erreur s'est produite lors de la réinitialisation des actions.",
                    ephemeral=True, delete_after=10
                )

    @discord.ui.button(label="Reset Joueur", emoji="🔁", style=discord.ButtonStyle.secondary)
    async def reset_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_required_role(interaction):
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission d'utiliser cette commande.",
                ephemeral=True
            )
            return

        if not bot.gs_data['players']:
            await interaction.response.send_message(
                "Aucun joueur dans la GS actuellement.",
                ephemeral=True
            )
            return

        view = ResetPlayerActionsView()
        await interaction.response.send_message(
            "Sélectionnez le joueur et l'action à réinitialiser :",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="Vérifier Actions", emoji="📋", style=discord.ButtonStyle.primary)
    async def check_actions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not has_required_role(interaction):
                await interaction.response.send_message(
                    "❌ Vous n'avez pas la permission d'utiliser cette commande.",
                    ephemeral=True
                )
                return

            if interaction.channel_id != GS_CHANNEL_ID:
                await interaction.response.send_message(
                    "Cette commande ne peut être utilisée que dans le salon GS !",
                    ephemeral=True
                )
                return

            if not bot.gs_data['players']:
                await interaction.response.send_message(
                    "Aucune GS n'est initialisée. Utilisez d'abord /init_gs",
                    ephemeral=True
                )
                return

            # Utiliser defer pour indiquer que nous allons répondre
            await interaction.response.defer()

            # Créer et envoyer le message de vérification
            check_message = await interaction.channel.send(embed=create_check_actions_embed())
            # Épingler le message
            await check_message.pin(reason="Suivi des actions GS")

            # Stocker l'ID du message pour les mises à jour futures
            bot.gs_data['check_message_id'] = check_message.id

            # Confirmer à l'utilisateur
            await interaction.followup.send(
                "✅ Le tableau de suivi des actions a été créé et épinglé.",
                ephemeral=True
            )

        except Exception as e:
            print(f"Erreur lors de la vérification des actions : {e}")
            await interaction.followup.send(
                "❌ Une erreur s'est produite lors de la vérification des actions.",
                ephemeral=True
            )

    @discord.ui.button(label="Retour", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Menu Administrateur",
            description="Sélectionnez une catégorie",
            color=discord.Color.blue()
        )
        view = AdminCategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

class PlayerManagementView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Ajouter Joueur", emoji="➕", style=discord.ButtonStyle.success)
    async def add_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_required_role(interaction):
            await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True, delete_after=10)
            return

        # Récupérer les membres du salon GS
        channel = interaction.guild.get_channel(GS_CHANNEL_ID)
        channel_members = channel.members

        view = AddPlayerView(channel_members)
        await interaction.response.send_message(
            "Sélectionnez les joueurs à ajouter (1-3 joueurs) :",
            view=view,
            ephemeral=True, delete_after=10
        )

    @discord.ui.button(label="Retirer Joueur", emoji="➖", style=discord.ButtonStyle.danger)
    async def remove_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_required_role(interaction):
            await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True, delete_after=10)
            return

        if not bot.gs_data['players']:
            await interaction.response.send_message(
                "Aucun joueur dans la GS actuellement.",
                ephemeral=True, delete_after=10
            )
            return

        view = RemovePlayerView(bot.gs_data['players'])
        await interaction.response.send_message(
            "Sélectionnez les joueurs à retirer (1-3 joueurs) :",
            view=view,
            ephemeral=True, delete_after=10
        )

    @discord.ui.button(label="Position Joueur", emoji="↕️", style=discord.ButtonStyle.primary)
    async def move_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not bot.gs_data['players']:
            await interaction.response.send_message(
                "Aucun joueur dans la GS actuellement.",
                ephemeral=True
            )
            return

        view = MovePlayerView()
        await interaction.response.send_message(
            "Sélectionnez le joueur à déplacer et sa nouvelle position :",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="Retour", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Menu Administrateur",
            description="Sélectionnez une catégorie",
            color=discord.Color.blue()
        )
        view = AdminCategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

class PerformanceManagementView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Ajouter Étoiles", emoji="⭐", style=discord.ButtonStyle.success)
    async def add_star_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not bot.gs_data['players']:
            await interaction.response.send_message(
                "Aucun joueur dans la GS actuellement.",
                ephemeral=True
            )
            return

        view = AddStarView()  # Plus besoin de passer les joueurs en paramètre
        await interaction.response.send_message(
            "Sélectionnez un joueur et le nombre d'étoiles :",
            view=view,
            ephemeral=True,
            delete_after=10
        )

    @discord.ui.button(label="GG", emoji="🎉", style=discord.ButtonStyle.primary)
    async def gg_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not has_required_role(interaction):
                await interaction.response.send_message(
                    "❌ Vous n'avez pas la permission d'utiliser cette commande.",
                    ephemeral=True
                )
                return

            if interaction.channel_id != GS_CHANNEL_ID:
                await interaction.response.send_message(
                    "Cette commande ne peut être utilisée que dans le salon GS !",
                    ephemeral=True
                )
                return

            if not bot.gs_data['players']:
                await interaction.response.send_message(
                    "Aucune GS n'est initialisée. Utilisez d'abord /init_gs",
                    ephemeral=True
                )
                return

            await interaction.response.defer()

            # Joueurs avec 6 étoiles pour performances exceptionnelles
            perfect_players = [
                bot.gs_data['players'][user_id]['mention']
                for user_id in bot.gs_data['players']
                if bot.gs_data['stars'].get(user_id, 0) == 6
            ]

            # Tous les participants avec leurs étoiles
            all_players_with_stars = [
                f"{info['mention']} ({bot.gs_data['stars'].get(user_id, 0)}⭐)"
                for user_id, info in bot.gs_data['players'].items()
                if bot.gs_data['stars'].get(user_id, 0) > 0
            ]

            embed = discord.Embed(
                title="🎉 Félicitations et Remerciements !",
                color=discord.Color.gold()
            )

            if perfect_players:
                embed.add_field(
                    name="🌟 Performances Exceptionnelles !",
                    value=f"Félicitations à nos champions avec 6 étoiles :\n{', '.join(perfect_players)}",
                    inline=False
                )

            if all_players_with_stars:
                embed.add_field(
                    name="⭐ Résultats des attaques",
                    value="\n".join(all_players_with_stars),
                    inline=False
                )

            # Liste de tous les participants
            all_participants = [info['mention'] for info in bot.gs_data['players'].values()]
            embed.add_field(
                name="👏 Merci à tous les participants !",
                value=f"Un grand merci à tous pour votre participation :\n{', '.join(all_participants)}",
                inline=False
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Erreur dans le bouton GG: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Une erreur s'est produite.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Une erreur s'est produite.", ephemeral=True, delete_after=10)

    @discord.ui.button(label="Retour", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Menu Administrateur",
            description="Sélectionnez une catégorie",
            color=discord.Color.blue()
        )
        view = AdminCategoryView()
        await interaction.response.edit_message(embed=embed, view=view)