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

class GSBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

        # Structure de données pour la GS
        self.gs_data = {
            'players': {},  # Format: {user_id: {"name": display_name, "mention": mention}}
            'defenses': {},
            'tests': {},
            'attacks': {},
            'stars': {},  # Pour stocker le nombre d'étoiles
            'message_id': None  # Pour stocker l'ID du message épinglé
        }

    async def setup_hook(self):
        await self.tree.sync()

bot = GSBot()

def create_gs_embed():
    """Crée un embed Discord avec le tableau GS"""
    embed = discord.Embed(
        title="📊 Tableau Guerre Sainte",
        description="État actuel des défenses, tests et attaques\n",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )

    # Trier les joueurs
    sorted_players = sorted(bot.gs_data['players'].items(), key=lambda x: x[1]["name"].lower())

    # Diviser en deux groupes de 12
    players_per_field = 12

    # Diviser les joueurs en deux groupes
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
                "─────────────────"  # Séparateur
            ]
            player_blocks.append("\n".join(player_block))

        # Ajouter un champ pour ce groupe
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
            # Si le message n'existe plus, on en crée un nouveau
            new_message = await channel.send(embed=create_gs_embed())
            await new_message.pin(reason="Tableau GS")
            bot.gs_data['message_id'] = new_message.id
            return True
    return False

def has_required_role(interaction: discord.Interaction) -> bool:
    """Vérifie si l'utilisateur a le rôle requis"""
    REQUIRED_ROLE_ID = 1336091937567936596
    user_roles = [role.id for role in interaction.user.roles]
    print(f"User roles: {user_roles}")
    print(f"Required role: {REQUIRED_ROLE_ID}")
    has_role = any(role.id == REQUIRED_ROLE_ID for role in interaction.user.roles)
    print(f"Has required role: {has_role}")
    return has_role

@bot.tree.command(name="init_gs", description="Initialiser une nouvelle Guerre Sainte avec les joueurs mentionnés")
@app_commands.describe(
    joueur1="Premier joueur (mention)",
    joueur2="Deuxième joueur (mention)",
    joueur3="Troisième joueur (mention)",
    joueur4="Quatrième joueur (mention)",
    joueur5="Cinquième joueur (mention)"
)
async def init_gs(
    interaction: discord.Interaction,
    joueur1: discord.Member,
    joueur2: Optional[discord.Member] = None,
    joueur3: Optional[discord.Member] = None,
    joueur4: Optional[discord.Member] = None,
    joueur5: Optional[discord.Member] = None
):
    """Initialise une nouvelle GS avec les joueurs mentionnés"""
    try:
        # Vérifier les permissions d'abord
        if not has_required_role(interaction):
            await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return

        if interaction.channel_id != GS_CHANNEL_ID:
            await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
            return

        # Collecter tous les joueurs non-None
        players = [j for j in [joueur1, joueur2, joueur3, joueur4, joueur5] if j is not None]

        if len(players) > MAX_PLAYERS:
            await interaction.response.send_message(f"Erreur: Maximum {MAX_PLAYERS} joueurs autorisés !", ephemeral=True)
            return

        # Réinitialisation des données
        bot.gs_data['players'] = {}
        bot.gs_data['defenses'] = {}
        bot.gs_data['tests'] = {}
        bot.gs_data['attacks'] = {}
        bot.gs_data['stars'] = {}
        bot.gs_data['message_id'] = None

        # Ajout des joueurs
        for player in players:
            bot.gs_data['players'][player.id] = {
                "name": player.display_name,
                "mention": player.mention
            }

        # Créer et envoyer le message d'abord
        message = await interaction.channel.send(embed=create_gs_embed())

        # Épingler le message
        await message.pin(reason="Tableau GS")
        bot.gs_data['message_id'] = message.id

        # Répondre à l'interaction avec un message de confirmation
        await interaction.response.send_message("✅ Guerre Sainte initialisée !", ephemeral=True)

    except Exception as e:
        print(f"Error in init_gs: {str(e)}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Une erreur s'est produite lors de l'initialisation.", ephemeral=True)

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

    # D'abord répondre à l'interaction
    await interaction.response.send_message("\n".join(response), ephemeral=True)

    # Puis mettre à jour le message épinglé
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

    # Retirer les joueurs
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

    # Préparer le message de réponse
    response = []
    if removed_players:
        response.append(f"✅ Joueur(s) retiré(s): {', '.join(removed_players)}")
    if not_found:
        response.append(f"❌ Non trouvé(s): {', '.join(not_found)}")

    await interaction.response.send_message("\n".join(response), embed=create_gs_embed())

@bot.tree.command(name="def", description="Définir une défense (1-20)")
async def defense(interaction: discord.Interaction, target: int):
    """Enregistre une défense pour un joueur"""
    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    if interaction.user.id not in bot.gs_data['players']:
        await interaction.response.send_message(
            f"{interaction.user.mention} vous n'êtes pas dans la liste des joueurs GS !",
            ephemeral=True
        )
        return

    # Vérifier que la valeur est entre 1 et 20
    if target < 1 or target > 20:
        await interaction.response.send_message(
            f"❌ La valeur doit être comprise entre 1 et 20 !",
            ephemeral=True
        )
        return

    # Enregistrer la défense
    bot.gs_data['defenses'][interaction.user.id] = target

    # D'abord répondre à l'interaction avec un message éphémère
    await interaction.response.send_message(f"✅ Défense {target} enregistrée.", ephemeral=True)

    # Ensuite mettre à jour le message avec update_gs_message
    await update_gs_message(interaction.channel)

@bot.tree.command(name="test", description="Définir un test (1-20)")
async def test(interaction: discord.Interaction, target: int):
    """Enregistre un test pour un joueur"""
    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    if interaction.user.id not in bot.gs_data['players']:
        await interaction.response.send_message(
            f"{interaction.user.mention} vous n'êtes pas dans la liste des joueurs GS !",
            ephemeral=True
        )
        return

    # Vérifier que la valeur est entre 1 et 20
    if target < 1 or target > 20:
        await interaction.response.send_message(
            f"❌ La valeur doit être comprise entre 1 et 20 !",
            ephemeral=True
        )
        return

    # Enregistrer le test
    bot.gs_data['tests'][interaction.user.id] = target

    # D'abord répondre à l'interaction avec un message éphémère
    await interaction.response.send_message(f"✅ Test {target} enregistré.", ephemeral=True)

    # Ensuite mettre à jour le message avec update_gs_message
    await update_gs_message(interaction.channel)

@bot.tree.command(name="atq", description="Définir une attaque (1-20)")
async def attack(interaction: discord.Interaction, target: int):
    """Enregistre une attaque pour un joueur"""
    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    if interaction.user.id not in bot.gs_data['players']:
        await interaction.response.send_message(
            f"{interaction.user.mention} vous n'êtes pas dans la liste des joueurs GS !",
            ephemeral=True
        )
        return

    # Vérifier que la valeur est entre 1 et 20
    if target < 1 or target > 20:
        await interaction.response.send_message(
            f"❌ La valeur doit être comprise entre 1 et 20 !",
            ephemeral=True
        )
        return

    # Enregistrer l'attaque
    bot.gs_data['attacks'][interaction.user.id] = target

    # D'abord répondre à l'interaction avec un message éphémère
    await interaction.response.send_message(f"✅ Attaque {target} enregistrée.", ephemeral=True)

    # Ensuite mettre à jour le message avec update_gs_message
    await update_gs_message(interaction.channel)

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

    # Réinitialiser l'action spécifiée
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

    # D'abord répondre à l'interaction
    await interaction.response.send_message(message, ephemeral=True)

    # Puis mettre à jour le message épinglé
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

    # Garder la liste des joueurs et message_id mais réinitialiser toutes les actions
    players_backup = bot.gs_data['players'].copy()
    message_id_backup = bot.gs_data['message_id']

    # Réinitialiser les actions
    bot.gs_data['defenses'] = {}
    bot.gs_data['tests'] = {}
    bot.gs_data['attacks'] = {}

    # Restaurer la liste des joueurs et message_id
    bot.gs_data['players'] = players_backup
    bot.gs_data['message_id'] = message_id_backup

    # D'abord répondre à l'interaction
    await interaction.response.send_message(
        "✅ Toutes les actions ont été réinitialisées. La liste des participants reste inchangée.",
        ephemeral=True
    )

    # Puis mettre à jour le message épinglé
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
    # Vérification du rôle
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

    # Ajouter les étoiles
    bot.gs_data['stars'][joueur.id] = nombre.value

    # Répondre et mettre à jour le tableau
    await interaction.response.send_message(
        f"✅ {nombre.value} étoile(s) {'a' if nombre.value == 1 else 'ont'} été ajoutée(s) à {joueur.mention}.",
        ephemeral=True
    )
    await update_gs_message(interaction.channel)

@bot.tree.command(name="gg", description="Féliciter les participants avec 3 étoiles")
async def congratulate(interaction: discord.Interaction):
    """Félicite les participants avec 3 étoiles et remercie tout le monde"""
    # Vérification du rôle
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    if interaction.channel_id != GS_CHANNEL_ID:
        await interaction.response.send_message("Cette commande ne peut être utilisée que dans le salon GS !", ephemeral=True)
        return

    if not bot.gs_data['players']:
        await interaction.response.send_message("Aucune GS n'est initialisée. Utilisez d'abord /init_gs", ephemeral=True)
        return

    # Trouver les participants avec 3 étoiles
    three_stars = [
        bot.gs_data['players'][user_id]['mention']
        for user_id in bot.gs_data['players']
        if bot.gs_data['stars'].get(user_id, 0) >= 3
    ]

    # Créer le message de félicitations
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

    # Remercier tous les participants
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

    # Vérifier les actions manquantes pour chaque joueur
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

    # Ajouter les champs au embed
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
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes : {e}")

bot.run(TOKEN)