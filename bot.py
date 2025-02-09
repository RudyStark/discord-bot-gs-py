import discord
from discord import app_commands
from discord.ext import commands
import datetime
from dotenv import load_dotenv
import os
from typing import Optional

# Configuration
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GS_CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
MAX_PLAYERS = 26

# Emojis pour chaque type d'action
DEFENSE_EMOJI = "🛡️"
TEST_EMOJI = "🔍"
ATTACK_EMOJI = "⚔️"

class GSBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

        # Structure de données pour la GS
        self.gs_data = {
            'players': {},
            'defenses': {},
            'tests': {},
            'attacks': {},
            'stars': {},
            'message_id': None
        }

    async def setup_hook(self):
        await self.tree.sync()

# Initialisation du bot
bot = GSBot()

class ActionView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.action_type = None

    @discord.ui.button(label="Défense", emoji="🛡️", style=discord.ButtonStyle.primary)
    async def defense_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_number_select(interaction, "defense")

    @discord.ui.button(label="Test", emoji="🔍", style=discord.ButtonStyle.primary)
    async def test_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_number_select(interaction, "test")

    @discord.ui.button(label="Attaque", emoji="⚔️", style=discord.ButtonStyle.primary)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_number_select(interaction, "attack")

    async def show_number_select(self, interaction: discord.Interaction, action_type: str):
        try:
            self.action_type = action_type
            select = ActionSelect()
            self.clear_items()
            self.add_item(select)

            embed = discord.Embed(
                title=f"Choisissez votre {action_type}",
                description="Sélectionnez un numéro entre 1 et 20",
                color=discord.Color.blue()
            )

            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"Erreur dans show_number_select: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Une erreur s'est produite.", ephemeral=True)

class ActionSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=str(i), value=str(i))
            for i in range(1, 21)
        ]
        super().__init__(placeholder="Choisissez un numéro", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            view = self.view
            action_value = int(self.values[0])

            if view.action_type == "defense":
                bot.gs_data['defenses'][interaction.user.id] = action_value
                message = f"✅ Défense {action_value} enregistrée."
            elif view.action_type == "test":
                bot.gs_data['tests'][interaction.user.id] = action_value
                message = f"✅ Test {action_value} enregistré."
            else:
                bot.gs_data['attacks'][interaction.user.id] = action_value
                message = f"✅ Attaque {action_value} enregistrée."

            await interaction.response.edit_message(content=message, embed=None, view=None)
            await update_gs_message(interaction.channel)
        except Exception as e:
            print(f"Erreur dans le callback de sélection: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Une erreur s'est produite.", ephemeral=True)

# Classes pour le menu admin
class GSManagementView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Initialiser GS", emoji="🆕", style=discord.ButtonStyle.success)
    async def init_gs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Utilisez /init_gs pour initialiser une nouvelle GS", ephemeral=True)

    @discord.ui.button(label="Reset Actions", emoji="🔄", style=discord.ButtonStyle.danger)
    async def reset_actions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
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

            # Sauvegarder les données importantes
            players_backup = bot.gs_data['players'].copy()
            message_id_backup = bot.gs_data['message_id']

            # Réinitialiser les actions
            bot.gs_data['defenses'] = {}
            bot.gs_data['tests'] = {}
            bot.gs_data['attacks'] = {}

            # Restaurer les données sauvegardées
            bot.gs_data['players'] = players_backup
            bot.gs_data['message_id'] = message_id_backup

            await interaction.response.send_message(
                "✅ Toutes les actions ont été réinitialisées. La liste des participants reste inchangée.",
                ephemeral=True
            )

            await update_gs_message(interaction.channel)

        except Exception as e:
            print(f"Erreur lors de la réinitialisation des actions : {e}")
            await interaction.response.send_message(
                "❌ Une erreur s'est produite lors de la réinitialisation des actions.",
                ephemeral=True
            )

    @discord.ui.button(label="Vérifier Actions", emoji="📋", style=discord.ButtonStyle.primary)
    async def check_actions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Utilisez /check_actions pour voir les actions manquantes", ephemeral=True)

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
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission d'utiliser cette commande.",
                ephemeral=True
            )
            return

        channel = interaction.guild.get_channel(GS_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message(
                "❌ Erreur : impossible d'accéder au salon GS.",
                ephemeral=True
            )
            return

        # Compter les membres éligibles
        eligible_members = [
            member for member in channel.members
            if not member.bot and member.id not in bot.gs_data['players']
        ]

        # Cas où il n'y a pas de membres éligibles
        if len(eligible_members) == 0:
            await interaction.response.send_message(
                "❌ Il n'y a actuellement aucun joueur disponible à ajouter à la Guerre Sainte. "
                "Assurez-vous que les membres que vous souhaitez ajouter sont présents dans le salon.",
                ephemeral=True
            )
            return

        # Si nous avons des membres éligibles, créer la vue avec seulement ces membres
        view = AddPlayerView(eligible_members)  # Passer uniquement les membres éligibles
        await interaction.response.send_message(
            f"👥 Il y a {len(eligible_members)} joueur(s) disponible(s) à ajouter à la Guerre Sainte.",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="Retirer Joueur", emoji="➖", style=discord.ButtonStyle.danger)
    async def remove_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Utilisez /remove_player pour retirer des joueurs", ephemeral=True)

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
        await interaction.response.send_message("Utilisez /add_star pour ajouter des étoiles", ephemeral=True)

    @discord.ui.button(label="GG", emoji="🎉", style=discord.ButtonStyle.primary)
    async def gg_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Utilisez /gg pour féliciter les participants", ephemeral=True)

    @discord.ui.button(label="Retour", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Menu Administrateur",
            description="Sélectionnez une catégorie",
            color=discord.Color.blue()
        )
        view = AdminCategoryView()
        await interaction.response.edit_message(embed=embed, view=view)

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

class GSBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

        # Structure de données pour la GS
        self.gs_data = {
            'players': {},
            'defenses': {},
            'tests': {},
            'attacks': {},
            'stars': {},
            'message_id': None
        }

    async def setup_hook(self):
        await self.tree.sync()

bot = GSBot()

def has_required_role(interaction: discord.Interaction) -> bool:
    """Vérifie si l'utilisateur a le rôle requis ou est l'admin"""
    REQUIRED_ROLE_ID = 1336091937567936596
    ADMIN_ID = 861536212056408094

    if interaction.user.id == ADMIN_ID:
        return True

    return any(role.id == REQUIRED_ROLE_ID for role in interaction.user.roles)

def create_gs_embed():
    """Crée un embed Discord avec le tableau GS"""
    embed = discord.Embed(
        title="📊 Tableau Guerre Sainte",
        description="État actuel des défenses, tests et attaques\n",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )

    sorted_players = sorted(bot.gs_data['players'].items(), key=lambda x: x[1]["name"].lower())
    players_per_field = 12

    for i in range(0, len(sorted_players), players_per_field):
        group = sorted_players[i:i + players_per_field]
        player_blocks = []

        for user_id, player_info in group:
            def_value = bot.gs_data['defenses'].get(user_id, '-')
            test_value = bot.gs_data['tests'].get(user_id, '-')
            atq_value = bot.gs_data['attacks'].get(user_id, '-')
            stars = "⭐" * bot.gs_data['stars'].get(user_id, 0)

            player_block = [
                f"**{player_info['mention']}** :",
                f"{DEFENSE_EMOJI} Déf: `{def_value}`",
                f"{TEST_EMOJI} Test: `{test_value}`",
                f"{ATTACK_EMOJI} Atq: `{atq_value}`",
                f"{stars}" if stars else "",
                "─────────────────"
            ]
            player_blocks.append("\n".join(player_block))

        field_value = "\n".join(player_blocks)
        if field_value:
            field_name = "Participants Groupe 1" if i == 0 else "Participants Groupe 2"
            embed.add_field(
                name=f"{field_name} ({len(bot.gs_data['players'])}/{MAX_PLAYERS})",
                value=field_value,
                inline=False
            )

    if not bot.gs_data['players']:
        embed.add_field(
            name=f"Participants (0/{MAX_PLAYERS})",
            value="Aucun joueur",
            inline=False
        )

    embed.set_footer(text="Dernière mise à jour")
    return embed

async def update_gs_message(channel):
    """Met à jour le message épinglé du tableau GS"""
    if bot.gs_data['message_id']:
        try:
            message = await channel.fetch_message(bot.gs_data['message_id'])
            await message.edit(embed=create_gs_embed())
            return True
        except discord.NotFound:
            new_message = await channel.send(embed=create_gs_embed())
            await new_message.pin(reason="Tableau GS")
            bot.gs_data['message_id'] = new_message.id
            return True
    return False

# Nouvelle commande admin
@bot.tree.command(name="admin", description="Accéder au menu d'administration")
async def admin(interaction: discord.Interaction):
    """Interface d'administration pour la GS"""
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

        embed = discord.Embed(
            title="Menu Administrateur",
            description="Sélectionnez une catégorie",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📊 Gestion GS",
            value="Initialisation, reset et vérification des actions",
            inline=False
        )
        embed.add_field(
            name="👥 Gestion Joueurs",
            value="Ajout et retrait de joueurs",
            inline=False
        )
        embed.add_field(
            name="⭐ Gestion Performances",
            value="Attribution d'étoiles et félicitations",
            inline=False
        )

        view = AdminCategoryView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        print(f"Erreur dans la commande admin: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("Une erreur s'est produite.", ephemeral=True)

@bot.tree.command(name="action", description="Définir une action (Défense/Test/Attaque)")
async def action(interaction: discord.Interaction):
    """Interface unifiée pour définir une action"""
    try:
        if interaction.channel_id != GS_CHANNEL_ID:
            await interaction.response.send_message(
                "Cette commande ne peut être utilisée que dans le salon GS !",
                ephemeral=True
            )
            return

        if interaction.user.id not in bot.gs_data['players']:
            await interaction.response.send_message(
                f"{interaction.user.mention} vous n'êtes pas dans la liste des joueurs GS !",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Choisissez votre action",
            description="Cliquez sur un bouton pour choisir le type d'action",
            color=discord.Color.blue()
        )

        view = ActionView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        print(f"Erreur dans la commande action: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("Une erreur s'est produite.", ephemeral=True)

@bot.tree.command(name="init_gs", description="Initialiser une nouvelle Guerre Sainte avec les joueurs mentionnés")
async def init_gs(
    interaction: discord.Interaction,
    joueur1: discord.Member,
    joueur2: Optional[discord.Member] = None,
    joueur3: Optional[discord.Member] = None,
    joueur4: Optional[discord.Member] = None,
    joueur5: Optional[discord.Member] = None
):
    try:
        if not has_required_role(interaction):
            await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        if interaction.channel_id != GS_CHANNEL_ID:
            await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
            return

        # Différer la réponse
        await interaction.response.defer(ephemeral=True)
        print("Interaction différée avec succès")

        players = [j for j in [joueur1, joueur2, joueur3, joueur4, joueur5] if j is not None]

        if len(players) > MAX_PLAYERS:
            await interaction.followup.send(f"Erreur: Maximum {MAX_PLAYERS} joueurs autorisés !", ephemeral=True)
            return

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

        # Créer et envoyer le tableau
        embed = create_gs_embed()
        message = await interaction.channel.send(embed=embed)

        try:
            await message.pin(reason="Tableau GS")
        except discord.Forbidden:
            pass

        bot.gs_data['message_id'] = message.id

        # Confirmation avec followup
        await interaction.followup.send("✅ Guerre Sainte initialisée !", ephemeral=True)
        print("Guerre Sainte initialisée avec succès")

    except discord.NotFound:
        print("Erreur : Message introuvable")
        await interaction.followup.send("❌ Une erreur s'est produite : message introuvable.", ephemeral=True)

    except discord.HTTPException as e:
        print(f"Erreur HTTP: {e}")
        await interaction.followup.send("❌ Une erreur HTTP s'est produite.", ephemeral=True)

    except Exception as e:
        print(f"Erreur inattendue: {str(e)}")
        await interaction.followup.send("❌ Une erreur s'est produite lors de l'initialisation.", ephemeral=True)

@bot.tree.command(name="add_player", description="Ajouter un ou plusieurs joueurs à la GS en cours")
@app_commands.describe(
    joueur1="Premier joueur à ajouter (mention)",
    joueur2="Deuxième joueur à ajouter (mention)",
    joueur3="Troisième joueur à ajouter (mention)"
)
async def add_player(
    interaction: discord.Interaction,
    joueur1: discord.Member,
    joueur2: Optional[discord.Member] = None,
    joueur3: Optional[discord.Member] = None
):
    """Ajoute des joueurs à la GS en cours"""
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    if not bot.gs_data['players']:
        await interaction.response.send_message("Aucune GS n'est initialisée. Utilisez d'abord /init_gs", ephemeral=True)
        return

    new_players = [j for j in [joueur1, joueur2, joueur3] if j is not None]

    if len(bot.gs_data['players']) + len(new_players) > MAX_PLAYERS:
        await interaction.response.send_message(f"Erreur: Le nombre total de joueurs ne peut pas dépasser {MAX_PLAYERS} !", ephemeral=True)
        return

    added_players = []
    already_present = []
    for player in new_players:
        if player.id in bot.gs_data['players']:
            already_present.append(player.mention)
        else:
            bot.gs_data['players'][player.id] = {
                "name": player.display_name,
                "mention": player.mention
            }
            added_players.append(player.mention)

    response = []
    if added_players:
        response.append(f"✅ Joueur(s) ajouté(s): {', '.join(added_players)}")
    if already_present:
        response.append(f"⚠️ Déjà présent(s): {', '.join(already_present)}")

    await interaction.response.send_message("\n".join(response), ephemeral=True)

    if bot.gs_data['message_id']:
        try:
            message = await interaction.channel.fetch_message(bot.gs_data['message_id'])
            await message.edit(embed=create_gs_embed())
        except discord.NotFound:
            new_message = await interaction.channel.send(embed=create_gs_embed())
            await new_message.pin(reason="Tableau GS")
            bot.gs_data['message_id'] = new_message.id

@bot.tree.command(name="remove_player", description="Retirer un ou plusieurs joueurs de la GS en cours")
@app_commands.describe(
    joueur1="Premier joueur à retirer (mention)",
    joueur2="Deuxième joueur à retirer (mention)",
    joueur3="Troisième joueur à retirer (mention)"
)
async def remove_player(
    interaction: discord.Interaction,
    joueur1: discord.Member,
    joueur2: Optional[discord.Member] = None,
    joueur3: Optional[discord.Member] = None
):
    """Retire des joueurs de la GS en cours"""
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    # Vérifier si une GS est en cours
    if not bot.gs_data['players']:
        await interaction.response.send_message("Aucune GS n'est initialisée. Utilisez d'abord /init_gs", ephemeral=True)
        return

    # Collecter les joueurs à retirer
    players_to_remove = [j for j in [joueur1, joueur2, joueur3] if j is not None]

    removed_players = []
    not_found = []
    for player in players_to_remove:
        if player.id in bot.gs_data['players']:
            del bot.gs_data['players'][player.id]
            if player.id in bot.gs_data['defenses']: del bot.gs_data['defenses'][player.id]
            if player.id in bot.gs_data['tests']: del bot.gs_data['tests'][player.id]
            if player.id in bot.gs_data['attacks']: del bot.gs_data['attacks'][player.id]
            if player.id in bot.gs_data['stars']: del bot.gs_data['stars'][player.id]
            removed_players.append(player.mention)
        else:
            not_found.append(player.mention)

    response = []
    if removed_players:
        response.append(f"✅ Joueur(s) retiré(s): {', '.join(removed_players)}")
    if not_found:
        response.append(f"❌ Non trouvé(s): {', '.join(not_found)}")

    await interaction.response.send_message("\n".join(response), embed=create_gs_embed())

@bot.tree.command(name="reset_player", description="Réinitialiser une action spécifique d'un joueur")
@app_commands.describe(
    joueur="Joueur à réinitialiser (mention)",
    action="Action à réinitialiser"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Défense", value="defense"),
    app_commands.Choice(name="Test", value="test"),
    app_commands.Choice(name="Attaque", value="attack"),
    app_commands.Choice(name="Tout", value="all")
])
async def reset_player(
    interaction: discord.Interaction,
    joueur: discord.Member,
    action: app_commands.Choice[str]
):
    """Réinitialise une ou toutes les actions d'un joueur"""
    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    if not bot.gs_data['players']:
        await interaction.response.send_message("Aucune GS n'est initialisée. Utilisez d'abord /init_gs", ephemeral=True)
        return

    if joueur.id not in bot.gs_data['players']:
        await interaction.response.send_message(f"❌ {joueur.mention} n'est pas dans la liste des joueurs GS !", ephemeral=True)
        return

    action_value = action.value
    message = ""

    if action_value == "all":
        if joueur.id in bot.gs_data['defenses']: del bot.gs_data['defenses'][joueur.id]
        if joueur.id in bot.gs_data['tests']: del bot.gs_data['tests'][joueur.id]
        if joueur.id in bot.gs_data['attacks']: del bot.gs_data['attacks'][joueur.id]
        message = f"✅ Toutes les actions de {joueur.mention} ont été réinitialisées."
    elif action_value == "defense":
        if joueur.id in bot.gs_data['defenses']:
            del bot.gs_data['defenses'][joueur.id]
            message = f"✅ La défense de {joueur.mention} a été réinitialisée."
        else:
            message = f"ℹ️ {joueur.mention} n'avait pas de défense enregistrée."
    elif action_value == "test":
        if joueur.id in bot.gs_data['tests']:
            del bot.gs_data['tests'][joueur.id]
            message = f"✅ Le test de {joueur.mention} a été réinitialisé."
        else:
            message = f"ℹ️ {joueur.mention} n'avait pas de test enregistré."
    elif action_value == "attack":
        if joueur.id in bot.gs_data['attacks']:
            del bot.gs_data['attacks'][joueur.id]
            message = f"✅ L'attaque de {joueur.mention} a été réinitialisée."
        else:
            message = f"ℹ️ {joueur.mention} n'avait pas d'attaque enregistrée."

    await interaction.response.send_message(message, ephemeral=True)
    await update_gs_message(interaction.channel)

@bot.tree.command(name="reset_all_actions", description="Réinitialiser toutes les actions de tous les joueurs")
async def reset_all_actions(interaction: discord.Interaction):
    """Réinitialise toutes les actions tout en gardant la liste des joueurs"""
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    if not bot.gs_data['players']:
        await interaction.response.send_message("Aucune GS n'est initialisée. Utilisez d'abord /init_gs", ephemeral=True)
        return

    players_backup = bot.gs_data['players'].copy()
    message_id_backup = bot.gs_data['message_id']

    bot.gs_data['defenses'] = {}
    bot.gs_data['tests'] = {}
    bot.gs_data['attacks'] = {}

    bot.gs_data['players'] = players_backup
    bot.gs_data['message_id'] = message_id_backup

    await interaction.response.send_message(
        "✅ Toutes les actions ont été réinitialisées. La liste des participants reste inchangée.",
        ephemeral=True
    )

    await update_gs_message(interaction.channel)

@bot.tree.command(name="add_star", description="Ajouter des étoiles à un participant")
@app_commands.describe(
    joueur="Joueur à qui ajouter des étoiles",
    nombre="Nombre d'étoiles à ajouter (1-3)"
)
@app_commands.choices(nombre=[
    app_commands.Choice(name="1 étoile", value=1),
    app_commands.Choice(name="2 étoiles", value=2),
    app_commands.Choice(name="3 étoiles", value=3)
])
async def add_star(
    interaction: discord.Interaction,
    joueur: discord.Member,
    nombre: app_commands.Choice[int]
):
    """Ajoute des étoiles à un participant"""
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    if not bot.gs_data['players']:
        await interaction.response.send_message("Aucune GS n'est initialisée. Utilisez d'abord /init_gs", ephemeral=True)
        return

    if joueur.id not in bot.gs_data['players']:
        await interaction.response.send_message(f"❌ {joueur.mention} n'est pas dans la liste des joueurs GS !", ephemeral=True)
        return

    bot.gs_data['stars'][joueur.id] = nombre.value

    await interaction.response.send_message(
        f"✅ {nombre.value} étoile(s) {'a' if nombre.value == 1 else 'ont'} été ajoutée(s) à {joueur.mention}.",
        ephemeral=True
    )
    await update_gs_message(interaction.channel)

@bot.tree.command(name="gg", description="Féliciter les participants avec 3 étoiles")
async def congratulate(interaction: discord.Interaction):
    """Félicite les participants avec 3 étoiles et remercie tout le monde"""
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    if not bot.gs_data['players']:
        await interaction.response.send_message("Aucune GS n'est initialisée. Utilisez d'abord /init_gs", ephemeral=True)
        return

    three_stars = [
        bot.gs_data['players'][user_id]['mention']
        for user_id in bot.gs_data['players']
        if bot.gs_data['stars'].get(user_id, 0) >= 3
    ]

    embed = discord.Embed(
        title="🎉 Félicitations et Remerciements !",
        color=discord.Color.gold(),
        timestamp=datetime.datetime.now()
    )

    if three_stars:
        embed.add_field(
            name="🌟 Performances Exceptionnelles !",
            value=f"Félicitations à nos champions avec 3 étoiles :\n{', '.join(three_stars)}",
            inline=False
        )

    all_participants = [info['mention'] for info in bot.gs_data['players'].values()]
    embed.add_field(
        name="👏 Merci à tous les participants !",
        value=f"Un grand merci à tous pour votre participation :\n{', '.join(all_participants)}",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="check_actions", description="Voir qui n'a pas encore effectué toutes ses actions")
async def check_actions(interaction: discord.Interaction):
    """Affiche un résumé des actions manquantes pour chaque joueur"""
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    if not bot.gs_data['players']:
        await interaction.response.send_message("Aucune GS n'est initialisée. Utilisez d'abord /init_gs", ephemeral=True)
        return

    embed = discord.Embed(
        title="📋 Actions manquantes",
        description="Récapitulatif des actions à faire",
        color=discord.Color.orange(),
        timestamp=datetime.datetime.now()
    )

    missing_def = []
    missing_test = []
    missing_atq = []
    all_done = []

    for user_id, player_info in bot.gs_data['players'].items():
        missing = []
        if user_id not in bot.gs_data['defenses']: missing.append("Défense")
        if user_id not in bot.gs_data['tests']: missing.append("Test")
        if user_id not in bot.gs_data['attacks']: missing.append("Attaque")

        if missing:
            actions = ", ".join(missing)
            if "Défense" in actions: missing_def.append(player_info['mention'])
            if "Test" in actions: missing_test.append(player_info['mention'])
            if "Attaque" in actions: missing_atq.append(player_info['mention'])
        else:
            all_done.append(player_info['mention'])

    if missing_def:
        embed.add_field(name="❌ Défense manquante", value="\n".join(missing_def), inline=False)
    if missing_test:
        embed.add_field(name="❌ Test manquant", value="\n".join(missing_test), inline=False)
    if missing_atq:
        embed.add_field(name="❌ Attaque manquante", value="\n".join(missing_atq), inline=False)
    if all_done:
        embed.add_field(name="✅ Actions complétées", value="\n".join(all_done), inline=False)

    await interaction.response.send_message(embed=embed)

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