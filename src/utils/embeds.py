import discord
import datetime
from src.config.constants import MAX_PLAYERS, DEFENSE_EMOJI, TEST_EMOJI, ATTACK_EMOJI
from src.bot.gs_bot import bot

def create_admin_menu_embed():
    """Crée l'embed pour le menu administrateur"""
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
    return embed

def create_check_actions_embed():
    """Crée l'embed pour la vérification des attaques"""
    embed = discord.Embed(
        title="📋 Attaques manquantes",
        description="Ce message s'actualise automatiquement à chaque attaque effectuée",
        color=discord.Color.orange(),
        timestamp=datetime.datetime.now()
    )

    missing_atq = []
    all_done = []

    for user_id, player_info in bot.gs_data['players'].items():
        if user_id not in bot.gs_data['attacks']:
            missing_atq.append(player_info['mention'])
        else:
            stars = bot.gs_data['stars'].get(user_id, 0)
            star_display = f" ({stars}{'⭐' if stars > 0 else ''})" if stars > 0 else ""
            all_done.append(f"{player_info['mention']} - Cible: {bot.gs_data['attacks'][user_id]}{star_display}")

    if missing_atq:
        embed.add_field(
            name="❌ Attaque manquante",
            value="\n".join(missing_atq),
            inline=False
        )

    if all_done:
        embed.add_field(
            name="✅ Attaques effectuées",
            value="\n".join(all_done),
            inline=False
        )

    return embed

def create_gs_embed():
    """Crée un embed Discord avec le tableau GS"""
    embed = discord.Embed(
        title="📊 Tableau Guerre Sainte",
        description="État actuel des défenses, tests et attaques\n",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )

    # Convertir en liste et ajouter la position
    players_with_position = []
    for i, (user_id, player_info) in enumerate(bot.gs_data['players'].items(), 1):
        players_with_position.append({
            'position': i,
            'user_id': user_id,
            'info': player_info
        })

    players_per_field = 12

    for i in range(0, len(players_with_position), players_per_field):
        group = players_with_position[i:i + players_per_field]
        player_blocks = []

        for player in group:
            user_id = player['user_id']
            player_info = player['info']
            position = player['position']
            def_value = bot.gs_data['defenses'].get(user_id, '-')
            test_value = bot.gs_data['tests'].get(user_id, '-')
            atq_value = bot.gs_data['attacks'].get(user_id, '-')
            stars = "⭐" * bot.gs_data['stars'].get(user_id, 0)

            player_block = [
                f"**{position}. {player_info['mention']}**",
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
    """Met à jour les messages épinglés"""
    try:
        # Mise à jour du tableau GS
        if bot.gs_data['message_id']:
            try:
                message = await channel.fetch_message(bot.gs_data['message_id'])
                await message.edit(embed=create_gs_embed())
            except discord.NotFound:
                new_message = await channel.send(embed=create_gs_embed())
                await new_message.pin(reason="Tableau GS")
                bot.gs_data['message_id'] = new_message.id

        # Mise à jour du message de vérification des actions
        if bot.gs_data.get('check_message_id'):
            try:
                check_message = await channel.fetch_message(bot.gs_data['check_message_id'])
                await check_message.edit(embed=create_check_actions_embed())
            except discord.NotFound:
                pass  # Si le message n'existe plus, on ne le recrée pas automatiquement

        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour des messages : {e}")
        return False