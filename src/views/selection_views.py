import discord
from src.config.settings import GS_CHANNEL_ID
from src.config.constants import MAX_PLAYERS, DEFENSE_EMOJI, TEST_EMOJI, ATTACK_EMOJI
from src.commands.gs_commands import init_gs
from src.bot.gs_bot import bot
from src.utils.embeds import update_gs_message, create_gs_embed
from src.utils.permissions import has_required_role

class InitGSView(discord.ui.View):
    def __init__(self, channel_members):
        super().__init__()

        # Récupérer uniquement les vrais membres (non bots)
        self.real_players = [
            member for member in channel_members
            if not member.bot
        ]

        # Créer les options pour les joueurs
        player_options = [
            discord.SelectOption(
                label=member.display_name,
                description=f"ID: {member.id}",
                value=str(member.id)
            )
            for member in self.real_players
        ]

        # Menu de sélection des joueurs
        player_select = discord.ui.Select(
            placeholder="Sélectionnez les joueurs participants",
            min_values=1,  # Au moins 1 joueur
            max_values=min(MAX_PLAYERS, len(player_options)),  # Jusqu'au maximum autorisé
            options=player_options
        )

        async def player_select_callback(interaction: discord.Interaction):
            try:
                selected_user_ids = [int(value) for value in player_select.values]

                # Initialiser les données
                bot.gs_data['players'] = {}
                bot.gs_data['defenses'] = {}
                bot.gs_data['tests'] = {}
                bot.gs_data['attacks'] = {}
                bot.gs_data['stars'] = {}
                bot.gs_data['message_id'] = None

                # Récupérer les membres
                members = []
                for user_id in selected_user_ids:
                    try:
                        member = await interaction.guild.fetch_member(user_id)
                        members.append(member)
                    except discord.NotFound:
                        continue

                # Ajouter tous les joueurs comme titulaires
                for i, member in enumerate(members):
                    status = "titulaire" if i < 20 else "remplacant"  # Les 20 premiers sont titulaires
                    bot.gs_data['players'][member.id] = {
                        "name": member.display_name,
                        "mention": member.mention,
                        "status": status
                    }

                # Créer et épingler le message du tableau GS
                message = await interaction.channel.send(embed=create_gs_embed())
                await message.pin(reason="Tableau GS")
                bot.gs_data['message_id'] = message.id

                # Compter les titulaires et remplaçants
                titulaires = sum(1 for p in bot.gs_data['players'].values() if p.get('status') == 'titulaire')
                remplacants = sum(1 for p in bot.gs_data['players'].values() if p.get('status') == 'remplacant')

                await interaction.response.edit_message(
                    content=f"✅ GS initialisée avec succès !\n"
                           f"• {titulaires} titulaire(s)\n"
                           f"• {remplacants} remplaçant(s)\n"
                           f"• {len(bot.gs_data['players'])} joueur(s) au total",
                    view=None
                )

            except Exception as e:
                print(f"Erreur dans player_select_callback: {e}")
                await interaction.response.send_message(
                    "❌ Une erreur s'est produite lors de l'initialisation de la GS.",
                    ephemeral=True
                )

        player_select.callback = player_select_callback
        self.add_item(player_select)

class AddStarView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.selected_player = None

        # Menu de sélection du joueur
        player_options = [
            discord.SelectOption(
                label=player_info["name"],
                description=f"Actuellement : {'⭐' * bot.gs_data['stars'].get(player_id, 0)}",
                value=str(player_id)
            )
            for player_id, player_info in bot.gs_data['players'].items()
        ]

        # Menu de sélection du nombre d'étoiles (maintenant jusqu'à 6)
        star_options = [
            discord.SelectOption(label=f"{i} étoile{'s' if i > 1 else ''}",
                               value=str(i),
                               emoji="⭐",
                               description=f"Total pour {i//3} attaque{'s' if i > 3 else ''} réussie{'s' if i > 3 else ''}")
            for i in range(1, 7)  # de 1 à 6 étoiles
        ]

        player_select = discord.ui.Select(
            placeholder="Sélectionnez un joueur",
            min_values=1,
            max_values=1,
            options=player_options
        )

        star_select = discord.ui.Select(
            placeholder="Nombre d'étoiles total (2 attaques max)",
            min_values=1,
            max_values=1,
            options=star_options
        )

        async def player_callback(interaction: discord.Interaction):
            if str(player_select.values[0]).startswith('dummy_'):
                await interaction.response.send_message(
                    "❌ Sélection invalide.",
                    ephemeral=True
                )
                return
            self.selected_player = int(player_select.values[0])
            await interaction.response.defer()

        async def star_callback(interaction: discord.Interaction):
            try:
                if not self.selected_player:
                    await interaction.response.send_message(
                        "❌ Veuillez d'abord sélectionner un joueur.",
                        ephemeral=True
                    )
                    return

                player = await interaction.guild.fetch_member(self.selected_player)
                stars = int(star_select.values[0])

                # Vérification du nombre d'étoiles
                if stars > 6:
                    await interaction.response.send_message(
                        "❌ Le nombre maximum d'étoiles est de 6 (2 attaques × 3 étoiles).",
                        ephemeral=True
                    )
                    return

                bot.gs_data['stars'][player.id] = stars

                # Calcul du nombre d'attaques réussies
                attaques_reussies = (stars + 2) // 3  # Arrondi supérieur
                await interaction.response.send_message(
                    f"✅ {stars} étoile{'s' if stars > 1 else ''} attribuée{'s' if stars > 1 else ''} à {player.mention}\n"
                    f"📊 Correspond à {attaques_reussies} attaque{'s' if attaques_reussies > 1 else ''} réussie{'s' if attaques_reussies > 1 else ''}",
                    ephemeral=True
                )
                await update_gs_message(interaction.channel)

            except Exception as e:
                print(f"Erreur dans l'attribution des étoiles: {e}")
                await interaction.response.send_message(
                    "❌ Une erreur s'est produite.",
                    ephemeral=True
                )

        player_select.callback = player_callback
        star_select.callback = star_callback

        self.add_item(player_select)
        self.add_item(star_select)

class AddPlayerView(discord.ui.View):
    def __init__(self, channel_members):
        super().__init__()
        self.selected_player = None
        self.selected_position = None

        # Créer le menu de sélection des joueurs
        player_options = []
        for member in channel_members:
            if not member.bot and member.id not in bot.gs_data['players']:
                player_options.append(
                    discord.SelectOption(
                        label=member.display_name,
                        description=f"ID: {member.id}",
                        value=str(member.id)
                    )
                )

        # Ajouter des options factices si nécessaire
        while len(player_options) < 25:
            player_options.append(
                discord.SelectOption(
                    label="━━━",
                    description="Non disponible",
                    value=f"dummy_{len(player_options)}"
                )
            )

        # Menu de sélection du joueur
        player_select = discord.ui.Select(
            placeholder="Sélectionnez le joueur à ajouter",
            min_values=1,
            max_values=1,
            options=player_options
        )

        # Créer les options de position
        current_players_count = len(bot.gs_data['players'])
        position_options = []
        for pos in range(1, current_players_count + 2):  # +2 pour permettre d'ajouter à la fin
            position_options.append(
                discord.SelectOption(
                    label=f"Position {pos}",
                    description="Nouvelle position",
                    value=str(pos)
                )
            )

        # Menu de sélection de la position
        position_select = discord.ui.Select(
            placeholder="Sélectionnez la position",
            min_values=1,
            max_values=1,
            options=position_options
        )

        async def player_callback(interaction: discord.Interaction):
            self.selected_player = int(player_select.values[0])
            await interaction.response.defer()

        async def position_callback(interaction: discord.Interaction):
            try:
                if not self.selected_player:
                    await interaction.response.send_message("❌ Veuillez d'abord sélectionner un joueur.", ephemeral=True, delete_after=10)
                    return

                position = int(position_select.values[0])
                player = await interaction.guild.fetch_member(self.selected_player)

                # Réorganiser les joueurs selon la nouvelle position
                current_players = list(bot.gs_data['players'].items())
                new_players = {}

                # Ajouter le nouveau joueur à la position spécifiée
                player_data = {
                    "name": player.display_name,
                    "mention": player.mention
                }

                # Réorganiser les joueurs
                for i, (user_id, data) in enumerate(current_players, 1):
                    if i == position:
                        new_players[player.id] = player_data
                    new_players[user_id] = data

                # Si la position est à la fin
                if position > len(current_players):
                    new_players[player.id] = player_data

                # Mettre à jour le dictionnaire des joueurs
                bot.gs_data['players'] = new_players

                await interaction.response.send_message(
                    f"✅ {player.mention} a été ajouté en position {position}.",
                    ephemeral=True, delete_after=10
                )
                await update_gs_message(interaction.channel)

            except Exception as e:
                print(f"Erreur dans le callback de position: {e}")
                await interaction.response.send_message("❌ Une erreur s'est produite.", ephemeral=True, delete_after=10)

        player_select.callback = player_callback
        position_select.callback = position_callback

        self.add_item(player_select)
        self.add_item(position_select)

class RemovePlayerView(discord.ui.View):
    def __init__(self, gs_players):
        super().__init__()

        options = [
            discord.SelectOption(
                label=player_info["name"],
                value=str(player_id),
                description=f"ID: {player_id}"
            )
            for player_id, player_info in gs_players.items()
        ]

        select = discord.ui.Select(
            placeholder="Sélectionnez les joueurs à retirer (1-3)",
            min_values=1,
            max_values=min(3, len(options)),
            options=options
        )

        async def select_callback(interaction: discord.Interaction):
            try:
                user_ids = [int(value) for value in select.values]
                removed_players = []

                for user_id in user_ids:
                    if user_id in bot.gs_data['players']:
                        player_mention = bot.gs_data['players'][user_id]['mention']
                        del bot.gs_data['players'][user_id]
                        if user_id in bot.gs_data['defenses']: del bot.gs_data['defenses'][user_id]
                        if user_id in bot.gs_data['tests']: del bot.gs_data['tests'][user_id]
                        if user_id in bot.gs_data['attacks']: del bot.gs_data['attacks'][user_id]
                        if user_id in bot.gs_data['stars']: del bot.gs_data['stars'][user_id]
                        removed_players.append(player_mention)

                await interaction.response.send_message(
                    f"✅ Joueur(s) retiré(s) : {', '.join(removed_players)}",
                    ephemeral=True, delete_after=10
                )
                await update_gs_message(interaction.channel)

            except Exception as e:
                print(f"Erreur dans le callback de retrait de joueurs: {e}")
                await interaction.response.send_message("❌ Une erreur s'est produite.", ephemeral=True, delete_after=10)

        select.callback = select_callback
        self.add_item(select)

class ResetPlayerActionsView(discord.ui.View):
    def __init__(self):
        super().__init__()

        # Menu de sélection du joueur
        player_options = [
            discord.SelectOption(
                label=player_info["name"],
                description=f"ID: {player_id}",
                value=str(player_id)
            )
            for player_id, player_info in bot.gs_data['players'].items()
        ]

        player_select = discord.ui.Select(
            placeholder="Sélectionnez le joueur",
            min_values=1,
            max_values=1,
            options=player_options
        )

        # Menu de sélection de l'action
        action_options = [
            discord.SelectOption(label="Défense", value="defense", emoji=DEFENSE_EMOJI),
            discord.SelectOption(label="Test", value="test", emoji=TEST_EMOJI),
            discord.SelectOption(label="Attaque", value="attack", emoji=ATTACK_EMOJI),
            discord.SelectOption(label="Toutes les actions", value="all", emoji="🔄")
        ]

        action_select = discord.ui.Select(
            placeholder="Action à réinitialiser",
            min_values=1,
            max_values=1,
            options=action_options
        )

        async def player_callback(interaction: discord.Interaction):
            self.selected_player = int(player_select.values[0])
            await interaction.response.defer()

        async def action_callback(interaction: discord.Interaction):
            try:
                if not self.selected_player:
                    await interaction.response.send_message(
                        "❌ Veuillez d'abord sélectionner un joueur.",
                        ephemeral=True
                    )
                    return

                player = await interaction.guild.fetch_member(self.selected_player)
                action = action_select.values[0]
                message = ""

                if action == "all":
                    if self.selected_player in bot.gs_data['defenses']: del bot.gs_data['defenses'][self.selected_player]
                    if self.selected_player in bot.gs_data['tests']: del bot.gs_data['tests'][self.selected_player]
                    if self.selected_player in bot.gs_data['attacks']: del bot.gs_data['attacks'][self.selected_player]
                    message = f"✅ Toutes les actions de {player.mention} ont été réinitialisées."
                elif action == "defense":
                    if self.selected_player in bot.gs_data['defenses']:
                        del bot.gs_data['defenses'][self.selected_player]
                        message = f"✅ La défense de {player.mention} a été réinitialisée."
                    else:
                        message = f"ℹ️ {player.mention} n'avait pas de défense enregistrée."
                elif action == "test":
                    if self.selected_player in bot.gs_data['tests']:
                        del bot.gs_data['tests'][self.selected_player]
                        message = f"✅ Le test de {player.mention} a été réinitialisé."
                    else:
                        message = f"ℹ️ {player.mention} n'avait pas de test enregistré."
                elif action == "attack":
                    if self.selected_player in bot.gs_data['attacks']:
                        del bot.gs_data['attacks'][self.selected_player]
                        message = f"✅ L'attaque de {player.mention} a été réinitialisée."
                    else:
                        message = f"ℹ️ {player.mention} n'avait pas d'attaque enregistrée."

                await interaction.response.send_message(message, ephemeral=True)
                await update_gs_message(interaction.channel)

            except Exception as e:
                print(f"Erreur dans le reset des actions: {e}")
                await interaction.response.send_message(
                    "❌ Une erreur s'est produite.",
                    ephemeral=True
                )

        player_select.callback = player_callback
        action_select.callback = action_callback

        self.add_item(player_select)
        self.add_item(action_select)

class SelectRemplacantView(discord.ui.View):
    def __init__(self, selected_players: list, has_test_players: bool):
        super().__init__()
        self.has_test_players = has_test_players

        # Créer les options pour les vrais joueurs
        player_options = [
            discord.SelectOption(
                label=player['name'],
                value=str(player['id'])
            )
            for player in selected_players
        ]

        # Ajouter des options fictives si nécessaire pour atteindre le minimum de 4
        dummy_count = max(0, 4 - len(player_options))
        dummy_options = [
            discord.SelectOption(
                label=f"━━━",
                description="Non disponible",
                value=f"dummy_{i}",
                default=True  # Les options fictives sont présélectionnées
            )
            for i in range(dummy_count)
        ]

        all_options = player_options + dummy_options

        # Menu pour sélectionner les remplaçants
        select = discord.ui.Select(
            placeholder="Choisir les remplaçants",
            min_values=min(4, len(player_options)),  # Ajuster min_values selon le nombre de joueurs
            max_values=min(4, len(player_options)),  # Ajuster max_values selon le nombre de joueurs
            options=all_options
        )

        async def select_callback(interaction: discord.Interaction):
            try:
                # Filtrer les valeurs non-dummy
                remplacant_ids = [
                    value for value in select.values
                    if not str(value).startswith('dummy_')
                ]

                # Initialiser les données
                bot.gs_data['players'] = {}
                bot.gs_data['defenses'] = {}
                bot.gs_data['tests'] = {}
                bot.gs_data['attacks'] = {}
                bot.gs_data['stars'] = {}
                bot.gs_data['message_id'] = None

                # Ajouter tous les joueurs avec leur statut
                for player in selected_players:
                    if player['is_test']:
                        bot.gs_data['players'][player['id']] = {
                            "name": player['name'],
                            "mention": player['name'],
                            "status": "remplacant" if player['id'] in remplacant_ids else "titulaire"
                        }
                    else:
                        member = await interaction.guild.fetch_member(player['id'])
                        bot.gs_data['players'][player['id']] = {
                            "name": member.display_name,
                            "mention": member.mention,
                            "status": "remplacant" if player['id'] in remplacant_ids else "titulaire"
                        }

                # Créer et épingler le message du tableau GS
                message = await interaction.channel.send(embed=create_gs_embed())
                await message.pin(reason="Tableau GS")
                bot.gs_data['message_id'] = message.id

                titulaires = len(selected_players) - len(remplacant_ids)
                await interaction.response.edit_message(
                    content=f"✅ GS initialisée avec succès !\n"
                           f"• {titulaires} titulaires\n"
                           f"• {len(remplacant_ids)} remplaçants",
                    view=None
                )

            except Exception as e:
                print(f"Erreur lors de la sélection des remplaçants : {e}")
                await interaction.response.send_message(
                    "Une erreur s'est produite.",
                    ephemeral=True
                )

        select.callback = select_callback
        self.add_item(select)

class MovePlayerView(discord.ui.View):
    def __init__(self):
        super().__init__()

        # Menu de sélection du joueur
        player_options = [
            discord.SelectOption(
                label=player_info["name"],
                description=f"Position actuelle: {i+1}",
                value=str(player_id)
            )
            for i, (player_id, player_info) in enumerate(bot.gs_data['players'].items())
        ]

        player_select = discord.ui.Select(
            placeholder="Sélectionnez le joueur à déplacer",
            min_values=1,
            max_values=1,
            options=player_options
        )

        # Menu de sélection de la position
        total_players = len(bot.gs_data['players'])
        position_options = [
            discord.SelectOption(
                label=f"Position {pos}",
                value=str(pos)
            )
            for pos in range(1, total_players + 1)
        ]

        position_select = discord.ui.Select(
            placeholder="Sélectionnez la nouvelle position",
            min_values=1,
            max_values=1,
            options=position_options
        )

        async def player_callback(interaction: discord.Interaction):
            self.selected_player = int(player_select.values[0])
            await interaction.response.defer()

        async def position_callback(interaction: discord.Interaction):
            try:
                if not hasattr(self, 'selected_player'):
                    await interaction.response.send_message(
                        "❌ Veuillez d'abord sélectionner un joueur.",
                        ephemeral=True
                    )
                    return

                new_position = int(position_select.values[0])
                player = await interaction.guild.fetch_member(self.selected_player)

                # Réorganiser les joueurs
                current_players = list(bot.gs_data['players'].items())
                player_data = bot.gs_data['players'][self.selected_player]

                # Retirer le joueur de sa position actuelle
                current_players = [(id, data) for id, data in current_players if id != self.selected_player]

                # Insérer le joueur à sa nouvelle position
                current_players.insert(new_position - 1, (self.selected_player, player_data))

                # Mettre à jour le dictionnaire avec le nouvel ordre
                new_players = {}
                for id, data in current_players:
                    new_players[id] = data

                bot.gs_data['players'] = new_players

                await interaction.response.send_message(
                    f"✅ {player.mention} a été déplacé en position {new_position}.",
                    ephemeral=True
                )
                await update_gs_message(interaction.channel)

            except Exception as e:
                print(f"Erreur dans le déplacement du joueur: {e}")
                await interaction.response.send_message(
                    "❌ Une erreur s'est produite.",
                    ephemeral=True
                )

        player_select.callback = player_callback
        position_select.callback = position_callback

        self.add_item(player_select)
        self.add_item(position_select)