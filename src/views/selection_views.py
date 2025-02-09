import discord
from src.config.settings import GS_CHANNEL_ID
from src.config.constants import MAX_PLAYERS
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
    def __init__(self, gs_players):
        super().__init__()
        self.selected_player = None

        player_select = discord.ui.Select(
            placeholder="Sélectionnez un joueur",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=player_info["name"],
                    value=str(player_id),
                    description=f"ID: {player_id}"
                )
                for player_id, player_info in gs_players.items()
            ]
        )

        star_select = discord.ui.Select(
            placeholder="Nombre d'étoiles",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="1 étoile", value="1"),
                discord.SelectOption(label="2 étoiles", value="2"),
                discord.SelectOption(label="3 étoiles", value="3")
            ]
        )

        async def player_callback(interaction: discord.Interaction):
            self.selected_player = int(player_select.values[0])
            await interaction.response.defer()

        async def star_callback(interaction: discord.Interaction):
            try:
                if not self.selected_player:
                    await interaction.response.send_message("❌ Veuillez d'abord sélectionner un joueur.", ephemeral=True, delete_after=10)
                    return

                player = await interaction.guild.fetch_member(self.selected_player)
                stars = int(star_select.values[0])

                bot.gs_data['stars'][player.id] = stars

                await interaction.response.send_message(
                    f"✅ {stars} étoile(s) {'a' if stars == 1 else 'ont'} été ajoutée(s) à {player.mention}.",
                    ephemeral=True, delete_after=10
                )
                await update_gs_message(interaction.channel)

            except Exception as e:
                print(f"Erreur dans le callback des étoiles: {e}")
                await interaction.response.send_message("❌ Une erreur s'est produite.", ephemeral=True, delete_after=10)

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