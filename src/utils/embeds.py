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

def create_gs_embed():
    """Crée un embed Discord avec le tableau GS"""
    embed = discord.Embed(
        title="📊 Tableau Guerre Sainte",
        description="État actuel des défenses, tests et attaques\n",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )

    # Séparer les joueurs par statut
    titulaires = []
    remplacants = []

    for user_id, player_info in bot.gs_data['players'].items():
        player_data = {
            'user_id': user_id,
            'info': player_info,
            'def_value': bot.gs_data['defenses'].get(user_id, '-'),
            'test_value': bot.gs_data['tests'].get(user_id, '-'),
            'atq_value': bot.gs_data['attacks'].get(user_id, '-'),
            'stars': "⭐" * bot.gs_data['stars'].get(user_id, 0)
        }

        if player_info.get('status', 'titulaire') == 'titulaire':
            titulaires.append(player_data)
        else:
            remplacants.append(player_data)

    # Diviser les titulaires en groupes de 6
    for i in range(0, len(titulaires), 6):
        group = titulaires[i:i+6]
        player_blocks = []

        for j, player in enumerate(group, start=i+1):
            player_block = [
                f"**{j}. 👤 {player['info']['mention']}**",
                f"{DEFENSE_EMOJI}`{player['def_value']}` {TEST_EMOJI}`{player['test_value']}` {ATTACK_EMOJI}`{player['atq_value']}` {player['stars']}",
                "───────"
            ]
            player_blocks.append("\n".join(filter(None, player_block)))

        embed.add_field(
            name=f"Titulaires - Groupe {(i//6)+1} ({len(titulaires)}/20)",
            value="\n".join(player_blocks) or "Aucun titulaire",
            inline=False
        )

    # Ajouter les remplaçants dans un champ séparé
    if remplacants:
        player_blocks = []
        for j, player in enumerate(remplacants, start=len(titulaires)+1):
            player_block = [
                f"**{j}. 🔄 {player['info']['mention']}**",
                f"{DEFENSE_EMOJI}`{player['def_value']}` {TEST_EMOJI}`{player['test_value']}` {ATTACK_EMOJI}`{player['atq_value']}` {player['stars']}",
                "───────"
            ]
            player_blocks.append("\n".join(filter(None, player_block)))

        embed.add_field(
            name=f"Remplaçants ({len(remplacants)}/{MAX_PLAYERS - 20})",
            value="\n".join(player_blocks),
            inline=False
        )

    if not bot.gs_data['players']:
        embed.add_field(
            name=f"Participants (0/{MAX_PLAYERS})",
            value="Aucun joueur",
            inline=False
        )

    # Statistiques globales
    total_stars = sum(bot.gs_data['stars'].values())

    stats_text = [
        f"Titulaires: {len(titulaires)}/20",
        f"Remplaçants: {len(remplacants)}/4",
        f"Étoiles: {total_stars}⭐"
    ]

    embed.add_field(
        name="📊 Statistiques",
        value="\n".join(stats_text),
        inline=False
    )

    embed.set_footer(text="Dernière mise à jour")
    return embed

def create_check_actions_embed():
    """Crée l'embed pour la vérification des actions"""
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
        # Ne vérifier que les titulaires
        if player_info.get('status', 'titulaire') == 'titulaire':
            missing = []
            if user_id not in bot.gs_data['defenses']: missing.append("Défense")
            if user_id not in bot.gs_data['tests']: missing.append("Test")
            if user_id not in bot.gs_data['attacks']: missing.append("Attaque")

            if missing:
                if "Défense" in missing: missing_def.append(player_info['mention'])
                if "Test" in missing: missing_test.append(player_info['mention'])
                if "Attaque" in missing: missing_atq.append(player_info['mention'])
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
                # Le message n'existe plus, on ne fait rien
                # Optionnellement, on peut effacer l'ID du message pour éviter de futures tentatives
                bot.gs_data.pop('check_message_id', None)

        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour des messages : {e}")
        return False