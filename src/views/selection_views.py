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

        options = []
        # Ajouter les vrais membres
        for member in channel_members:
            if not member.bot:
                options.append(
                    discord.SelectOption(
                        label=member.display_name,
                        description=f"ID: {member.id}",
                        value=str(member.id)
                    )
                )

        # Ajouter des options factices jusqu'à atteindre 25
        dummy_count = 25 - len(options)
        for i in range(dummy_count):
            options.append(
                discord.SelectOption(
                    label=f"━━━",  # Utiliser un séparateur visuel
                    description="Non disponible",
                    value=f"dummy_{i}"
                )
            )

        select = discord.ui.Select(
            placeholder="Sélectionnez les joueurs",
            min_values=1,
            max_values=min(25, len([opt for opt in options if not str(opt.value).startswith('dummy_')])),
            options=options
        )

        async def select_callback(interaction: discord.Interaction):
            try:
                user_ids = [int(value) for value in select.values if not str(value).startswith('dummy_')]
                players = [await interaction.guild.fetch_member(user_id) for user_id in user_ids]

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

                message = await interaction.channel.send(embed=create_gs_embed())
                await message.pin(reason="Tableau GS")
                bot.gs_data['message_id'] = message.id

                await interaction.response.send_message(
                    f"✅ Guerre Sainte initialisée avec {len(players)} participant(s) !",
                    ephemeral=True, delete_after=10
                )

            except Exception as e:
                print(f"Erreur dans le callback de sélection: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Une erreur s'est produite.", ephemeral=True, delete_after=10)

        select.callback = select_callback
        self.add_item(select)

class AddStarView(discord.ui.View):
    def __init__(self):  # Supprimé le paramètre players car on accède directement à bot.gs_data
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

        while len(player_options) < 25:
            player_options.append(
                discord.SelectOption(
                    label="━━━",
                    description="Non disponible",
                    value=f"dummy_{len(player_options)}"
                )
            )

        # Menu de sélection du nombre d'étoiles
        star_options = [
            discord.SelectOption(label="1 étoile", value="1", emoji="⭐"),
            discord.SelectOption(label="2 étoiles", value="2", emoji="⭐"),
            discord.SelectOption(label="3 étoiles", value="3", emoji="⭐"),
            discord.SelectOption(label="4 étoiles", value="4", emoji="⭐"),
            discord.SelectOption(label="5 étoiles", value="5", emoji="⭐"),
            discord.SelectOption(label="6 étoiles", value="6", emoji="⭐")
        ]

        player_select = discord.ui.Select(
            placeholder="Sélectionnez un joueur",
            min_values=1,
            max_values=1,
            options=player_options
        )

        star_select = discord.ui.Select(
            placeholder="Nombre d'étoiles total",
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

                bot.gs_data['stars'][player.id] = stars

                await interaction.response.send_message(
                    f"✅ {stars} étoile{'s' if stars > 1 else ''} attribuée{'s' if stars > 1 else ''} à {player.mention}.",
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